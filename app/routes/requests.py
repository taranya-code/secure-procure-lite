from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime
from ..extensions import db
from ..models import PurchaseRequest, RequestItem, Approval, Notification
from ..utils import require_roles, audit_log, notify

bp = Blueprint('requests', __name__)


@bp.route('/requests')
@login_required
def list_requests():
    q = PurchaseRequest.query
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    if search:
        q = q.filter(PurchaseRequest.title.ilike(f'%{search}%'))
    if status:
        q = q.filter_by(status=status)
    # Vendors only see nothing here
    if current_user.role == 'VENDOR':
        return redirect(url_for('rfq.my_quotes'))
    reqs = q.order_by(PurchaseRequest.created_at.desc()).all()
    return render_template('dashboard/requests.html', requests=reqs, search=search, status_filter=status)


@bp.route('/requests/new', methods=['GET', 'POST'])
@login_required
@require_roles('PROCUREMENT_OFFICER', 'ADMIN')
def new_request():
    if request.method == 'POST':
        title    = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        budget   = float(request.form.get('estimated_budget', 0))
        currency = request.form.get('currency', 'USD')
        urgency  = request.form.get('urgency', 'NORMAL')
        desc     = request.form.get('description', '').strip()

        pr = PurchaseRequest(
            title=title, description=desc, category=category,
            estimated_budget=budget, currency=currency, urgency=urgency,
            status='DRAFT', created_by=current_user.id,
        )
        db.session.add(pr)
        db.session.flush()

        # Line items
        item_names = request.form.getlist('item_name[]')
        quantities = request.form.getlist('quantity[]')
        units      = request.form.getlist('unit[]')
        specs      = request.form.getlist('specifications[]')
        for i, name in enumerate(item_names):
            if name.strip():
                db.session.add(RequestItem(
                    request_id=pr.id,
                    item_name=name.strip(),
                    quantity=float(quantities[i]) if i < len(quantities) else 1,
                    unit=units[i] if i < len(units) else 'pcs',
                    specifications=specs[i].strip() if i < len(specs) else None,
                ))

        audit_log('CREATE', 'PURCHASE_REQUEST', pr.id, {'title': title, 'budget': budget})
        db.session.commit()
        flash(f'Request "{title}" created as DRAFT.', 'success')
        return redirect(url_for('requests.list_requests'))

    return render_template('dashboard/request_form.html')


@bp.route('/requests/<int:req_id>')
@login_required
def view_request(req_id):
    pr = PurchaseRequest.query.get_or_404(req_id)
    return render_template('dashboard/request_detail.html', pr=pr)


@bp.route('/requests/<int:req_id>/submit', methods=['POST'])
@login_required
@require_roles('PROCUREMENT_OFFICER', 'ADMIN')
def submit_request(req_id):
    pr = PurchaseRequest.query.get_or_404(req_id)
    if pr.status != 'DRAFT':
        flash('Only DRAFT requests can be submitted.', 'warning')
        return redirect(url_for('requests.view_request', req_id=req_id))

    levels = pr.approval_levels_needed()
    for lvl in range(1, levels + 1):
        db.session.add(Approval(request_id=pr.id, level=lvl, approver_role='APPROVER', status='PENDING'))

    pr.status = 'SUBMITTED'
    audit_log('SUBMIT', 'PURCHASE_REQUEST', pr.id, {'levels': levels})

    # Notify all approvers
    from ..models import User
    approvers = User.query.filter(User.role.in_(['APPROVER', 'ADMIN']), User.is_active == True).all()
    for appr in approvers:
        notify(appr.id, 'APPROVAL_REQUIRED', 'Approval Required',
               f'Purchase request "{pr.title}" needs your approval.',
               link=url_for('requests.view_request', req_id=pr.id))

    db.session.commit()
    flash('Request submitted for approval.', 'success')
    return redirect(url_for('requests.view_request', req_id=req_id))


@bp.route('/requests/<int:req_id>/delete', methods=['POST'])
@login_required
@require_roles('PROCUREMENT_OFFICER', 'ADMIN')
def delete_request(req_id):
    pr = PurchaseRequest.query.get_or_404(req_id)
    if pr.status != 'DRAFT':
        flash('Only DRAFT requests can be deleted.', 'warning')
        return redirect(url_for('requests.list_requests'))
    audit_log('DELETE', 'PURCHASE_REQUEST', pr.id, {'title': pr.title})
    db.session.delete(pr)
    db.session.commit()
    flash('Request deleted.', 'info')
    return redirect(url_for('requests.list_requests'))
