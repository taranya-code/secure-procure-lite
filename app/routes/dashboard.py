from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from ..models import PurchaseRequest, Approval, AuditLog, Notification, Vendor, Quotation, RFQ
from ..extensions import db
from ..utils import compute_vendor_risk

bp = Blueprint('dashboard', __name__)


@bp.route('/dashboard')
@login_required
def index():
    # ── Vendor-specific dashboard ─────────────────────────────────────────
    if current_user.role == 'VENDOR':
        vendor = current_user.vendor
        active_rfqs, my_quotes, selected_quotes = 0, 0, 0
        if vendor:
            compute_vendor_risk(vendor, vendor.category)
            from ..models import RFQVendor
            active_rfqs = (RFQ.query.join(RFQVendor, RFQ.id == RFQVendor.rfq_id)
                           .filter(RFQVendor.vendor_id == vendor.id, RFQ.status == 'OPEN').count())
            my_quotes = Quotation.query.filter_by(vendor_id=vendor.id).count()
            selected_quotes = Quotation.query.filter_by(vendor_id=vendor.id, status='SELECTED').count()
        recent_notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
            Notification.created_at.desc()).limit(5).all()
        return render_template('dashboard/index_vendor.html',
            vendor=vendor, active_rfqs=active_rfqs,
            my_quotes=my_quotes, selected_quotes=selected_quotes,
            recent_notifs=recent_notifs)

    # ── Standard dashboard ────────────────────────────────────────────────
    total_requests = PurchaseRequest.query.count()
    total_spend = db.session.query(func.sum(PurchaseRequest.estimated_budget)).scalar() or 0

    pending_approvals = 0
    if current_user.role in ('APPROVER', 'ADMIN'):
        pending_approvals = Approval.query.filter_by(status='PENDING').count()

    # Compliance: % of non-draft/cancelled requests that were properly approved
    # (had at least one APPROVED approval record, not just skipped to PO)
    submitted = PurchaseRequest.query.filter(
        PurchaseRequest.status.notin_(['DRAFT', 'CANCELLED'])
    ).count()
    rejected = PurchaseRequest.query.filter_by(status='REJECTED').count()
    # Compliant = submitted that were NOT rejected without approval
    compliant = submitted - rejected if submitted > 0 else 0
    compliance = round((compliant / submitted * 100) if submitted else 100)

    cutoff = datetime.utcnow() - timedelta(days=3)
    overdue = Approval.query.filter(
        Approval.status == 'PENDING', Approval.created_at < cutoff).count()

    spend_by_cat_raw = db.session.query(
        PurchaseRequest.category,
        func.count(PurchaseRequest.id).label('count'),
        func.sum(PurchaseRequest.estimated_budget).label('total')
    ).group_by(PurchaseRequest.category).all()
    spend_by_cat = [[r.category, r.count, r.total] for r in spend_by_cat_raw]

    # Status breakdown for officer/admin
    status_counts = {}
    if current_user.role in ('PROCUREMENT_OFFICER', 'ADMIN'):
        rows = db.session.query(PurchaseRequest.status, func.count(PurchaseRequest.id)).group_by(PurchaseRequest.status).all()
        status_counts = {r[0]: r[1] for r in rows}

    fraud_alerts = AuditLog.query.filter_by(action='SELF_APPROVAL_BLOCKED').count()
    recent_activity = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(6).all()

    return render_template('dashboard/index.html',
        total_requests=total_requests,
        total_spend=total_spend,
        pending_approvals=pending_approvals,
        compliance=compliance,
        overdue=overdue,
        spend_by_cat=spend_by_cat,
        status_counts=status_counts,
        fraud_alerts=fraud_alerts,
        recent_activity=recent_activity,
    )
