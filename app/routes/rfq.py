from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from ..extensions import db
from ..models import (RFQ, RFQVendor, Quotation, QuotationItem,
                      PurchaseRequest, Vendor, User)
from ..utils import require_roles, audit_log, notify, compute_vendor_risk, vendor_is_eligible, find_eligible_vendors, adaptive_security_guard

bp = Blueprint('rfq', __name__)


@bp.route('/rfq')
@login_required
@require_roles('PROCUREMENT_OFFICER', 'ADMIN', 'APPROVER', 'AUDITOR', 'VENDOR')
def list_rfqs():
    if current_user.role == 'VENDOR':
        vendor = current_user.vendor
        if not vendor:
            flash('No vendor profile found.', 'warning')
            return redirect(url_for('dashboard.index'))
        rfqs = (RFQ.query
                .join(RFQVendor, RFQ.id == RFQVendor.rfq_id)
                .filter(RFQVendor.vendor_id == vendor.id)
                .order_by(RFQ.created_at.desc())
                .all())
        for rfq in rfqs:
            compute_vendor_risk(vendor, rfq.request.category)
        return render_template('dashboard/rfq.html', rfqs=rfqs,
                               eligible=[], approved_vendors=[])

    rfqs = RFQ.query.order_by(RFQ.created_at.desc()).all()
    # Requests eligible for RFQ (APPROVED, no RFQ yet)
    eligible = PurchaseRequest.query.filter_by(status='APPROVED').all()
    approved_vendors = Vendor.query.filter_by(status='APPROVED').all()
    for vendor in approved_vendors:
        compute_vendor_risk(vendor, None)
    return render_template('dashboard/rfq.html', rfqs=rfqs,
                           eligible=eligible, approved_vendors=approved_vendors)


@bp.route('/rfq/new', methods=['POST'])
@login_required
@require_roles('PROCUREMENT_OFFICER', 'ADMIN')
def new_rfq():
    req_id   = int(request.form.get('request_id'))
    deadline = request.form.get('deadline')
    notes    = request.form.get('notes', '').strip()
    vendor_ids = request.form.getlist('vendor_ids[]')

    pr = PurchaseRequest.query.get_or_404(req_id)
    if pr.rfq:
        flash('This request already has an RFQ.', 'warning')
        return redirect(url_for('rfq.list_rfqs'))

    rfq = RFQ(
        request_id=req_id,
        issued_by=current_user.id,
        deadline=datetime.strptime(deadline, '%Y-%m-%d') if deadline else datetime.utcnow() + timedelta(days=7),
        notes=notes,
        status='OPEN',
    )
    # Apply AI vendor intelligence filtering before invitations
    requested_vendors = []
    if vendor_ids:
        requested_vendors = [Vendor.query.get(int(vid)) for vid in vendor_ids if vid.isdigit()]
    else:
        requested_vendors = Vendor.query.filter_by(status='APPROVED').all()

    eligible_vendors = find_eligible_vendors([v for v in requested_vendors if v], pr.category)
    blocked_vendors = [v for v in requested_vendors if v and not vendor_is_eligible(v, pr.category)]

    if not eligible_vendors:
        flash('No eligible vendors found for this tender based on category specialization and AI risk profile.', 'danger')
        return redirect(url_for('rfq.list_rfqs'))

    db.session.add(rfq)
    db.session.flush()

    for vendor in eligible_vendors:
        db.session.add(RFQVendor(rfq_id=rfq.id, vendor_id=vendor.id))
        notify(vendor.user_id, 'RFQ_ISSUED', 'New RFQ Received',
               f'You have been invited to quote for: {pr.title}',
               link=url_for('rfq.my_quotes'))

    for vendor in blocked_vendors:
        if vendor:
            audit_log('RFQ_BLOCKED_VENDOR', 'VENDOR', vendor.id,
                      {'rfq_category': pr.category, 'vendor_category': vendor.category,
                       'eligibility_score': vendor.eligibility_score,
                       'fraud_probability': vendor.fraud_probability})

    pr.status = 'RFQ_ISSUED'
    audit_log('ISSUE_RFQ', 'RFQ', rfq.id, {'request_id': req_id, 'vendor_count': len(eligible_vendors)})
    db.session.commit()
    flash('RFQ issued to vendors.', 'success')
    return redirect(url_for('rfq.view_rfq', rfq_id=rfq.id))


@bp.route('/rfq/<int:rfq_id>')
@login_required
@require_roles('PROCUREMENT_OFFICER', 'ADMIN', 'APPROVER', 'AUDITOR', 'VENDOR')
def view_rfq(rfq_id):
    rfq = RFQ.query.get_or_404(rfq_id)
    if current_user.role == 'VENDOR':
        vendor = current_user.vendor
        invited = RFQVendor.query.filter_by(rfq_id=rfq.id, vendor_id=vendor.id).first() if vendor else None
        compute_vendor_risk(vendor, rfq.request.category)
        if not invited or not vendor_is_eligible(vendor, rfq.request.category):
            audit_log('BLOCKED_TENDER_ACCESS', 'RFQ', rfq_id,
                      {'vendor_id': vendor.id if vendor else None, 'eligibility': getattr(vendor, 'eligibility_score', None)})
            flash('Tender access denied: your vendor profile does not meet the AI security requirements for this RFQ.', 'danger')
            return redirect(url_for('dashboard.index'))
    adaptive_security_guard('TENDER_VIEW', 'RFQ', rfq_id, {'rfq_id': rfq_id})
    return render_template('dashboard/rfq_detail.html', rfq=rfq)


@bp.route('/rfq/<int:rfq_id>/select/<int:quot_id>', methods=['POST'])
@login_required
@require_roles('PROCUREMENT_OFFICER', 'ADMIN')
def select_quote(rfq_id, quot_id):
    rfq  = RFQ.query.get_or_404(rfq_id)
    quot = Quotation.query.get_or_404(quot_id)

    for q in rfq.quotations:
        q.status = 'REJECTED'
    quot.status = 'SELECTED'
    rfq.status  = 'CLOSED'
    rfq.request.status = 'PO_ISSUED'

    # Notify winning vendor
    notify(quot.vendor.user_id, 'GENERAL', 'Quote Selected — PO Issued',
           f'Congratulations! Your quote for "{rfq.request.title}" was selected. PO is being issued.',
           link=url_for('rfq.my_quotes'))

    audit_log('SELECT_QUOTE', 'QUOTATION', quot_id,
              {'rfq_id': rfq_id, 'vendor_id': quot.vendor_id, 'amount': quot.total_amount})
    db.session.commit()
    flash('Vendor selected. PO issued!', 'success')
    return redirect(url_for('rfq.view_rfq', rfq_id=rfq_id))


# ── Vendor: My Quotes ─────────────────────────────────────────────────────────

@bp.route('/my-quotes')
@login_required
@require_roles('VENDOR')
def my_quotes():
    vendor = current_user.vendor
    if not vendor:
        flash('No vendor profile found.', 'warning')
        return redirect(url_for('dashboard.index'))

    # Open RFQs this vendor is invited to
    open_rfqs = (RFQ.query
                 .join(RFQVendor, RFQ.id == RFQVendor.rfq_id)
                 .filter(RFQVendor.vendor_id == vendor.id, RFQ.status == 'OPEN')
                 .all())

    # Already submitted quotations
    my_quotations = Quotation.query.filter_by(vendor_id=vendor.id).order_by(Quotation.submitted_at.desc()).all()

    return render_template('dashboard/my_quotes.html',
                           open_rfqs=open_rfqs, my_quotations=my_quotations, vendor=vendor)


@bp.route('/my-quotes/<int:rfq_id>/submit', methods=['POST'])
@login_required
@require_roles('VENDOR')
def submit_quote(rfq_id):
    rfq    = RFQ.query.get_or_404(rfq_id)
    vendor = current_user.vendor

    if not vendor:
        flash('No vendor profile.', 'danger')
        return redirect(url_for('rfq.my_quotes'))

    invited = RFQVendor.query.filter_by(rfq_id=rfq_id, vendor_id=vendor.id).first()
    if not invited:
        flash('You are not authorized to submit a quote for this tender.', 'danger')
        return redirect(url_for('rfq.my_quotes'))

    compute_vendor_risk(vendor, rfq.request.category)
    if not vendor_is_eligible(vendor, rfq.request.category):
        audit_log('BLOCKED_BID_SUBMISSION', 'VENDOR', vendor.id,
                  {'rfq_id': rfq_id, 'eligibility_score': vendor.eligibility_score,
                   'fraud_probability': vendor.fraud_probability})
        flash('Your bid submission is blocked by the vendor intelligence engine due to risk factors.', 'danger')
        return redirect(url_for('rfq.my_quotes'))

    # Check already submitted
    existing = Quotation.query.filter_by(rfq_id=rfq_id, vendor_id=vendor.id).first()
    if existing:
        flash('You have already submitted a quote for this RFQ.', 'warning')
        return redirect(url_for('rfq.my_quotes'))

    total_amount  = float(request.form.get('total_amount', 0))
    delivery_days = int(request.form.get('delivery_days', 14))
    validity_days = int(request.form.get('validity_days', 30))
    notes         = request.form.get('notes', '').strip()

    quot = Quotation(
        rfq_id=rfq_id, vendor_id=vendor.id,
        total_amount=total_amount, delivery_days=delivery_days,
        validity_days=validity_days, notes=notes, status='SUBMITTED',
    )
    db.session.add(quot)
    db.session.flush()

    # Line items
    item_names = request.form.getlist('item_name[]')
    unit_prices = request.form.getlist('unit_price[]')
    quantities  = request.form.getlist('quantity[]')
    for i, name in enumerate(item_names):
        if name.strip():
            qty   = float(quantities[i]) if i < len(quantities) else 1
            price = float(unit_prices[i]) if i < len(unit_prices) else 0
            db.session.add(QuotationItem(
                quotation_id=quot.id, item_name=name.strip(),
                unit_price=price, quantity=qty, total=price * qty,
            ))

    if adaptive_security_guard('SUBMIT_QUOTE', 'QUOTATION', rfq_id,
                                {'payload_size': sum(len(str(v)) for v in request.form.values())}):
        flash('Suspicious quote submission detected and logged. If this was legitimate, contact support.', 'warning')

    # Update request status
    rfq.request.status = 'QUOTED'

    # Notify officer
    officers = User.query.filter(User.role.in_(['PROCUREMENT_OFFICER', 'ADMIN']), User.is_active == True).all()
    for o in officers:
        notify(o.id, 'QUOTATION_RECEIVED', 'New Quotation Received',
               f'{vendor.company_name} submitted a quote for "{rfq.request.title}".',
               link=url_for('rfq.view_rfq', rfq_id=rfq_id))

    audit_log('SUBMIT_QUOTE', 'QUOTATION', quot.id,
              {'rfq_id': rfq_id, 'vendor_id': vendor.id, 'amount': total_amount})
    db.session.commit()
    flash('Quotation submitted!', 'success')
    return redirect(url_for('rfq.my_quotes'))
