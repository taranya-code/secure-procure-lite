from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func
from ..models import PurchaseRequest, Vendor, Quotation
from ..extensions import db

bp = Blueprint('reports', __name__)


@bp.route('/reports')
@login_required
def index():
    # Spend by category
    spend_by_cat = db.session.query(
        PurchaseRequest.category,
        func.count(PurchaseRequest.id).label('count'),
        func.sum(PurchaseRequest.estimated_budget).label('total')
    ).group_by(PurchaseRequest.category).all()

    # Status distribution
    status_dist = db.session.query(
        PurchaseRequest.status,
        func.count(PurchaseRequest.id).label('count')
    ).group_by(PurchaseRequest.status).all()

    # Vendor performance
    vendors = Vendor.query.filter_by(status='APPROVED').order_by(
        Vendor.reputation_score.desc()).all()

    # Total stats
    total_spend   = db.session.query(func.sum(PurchaseRequest.estimated_budget)).scalar() or 0
    total_requests = PurchaseRequest.query.count()
    total_vendors  = Vendor.query.filter_by(status='APPROVED').count()
    po_count       = PurchaseRequest.query.filter_by(status='PO_ISSUED').count()
    compliance     = round((po_count / total_requests * 100) if total_requests else 100)

    # Convert Row objects to plain lists for JSON serialization in templates
    spend_by_cat_list = [[r.category, r.count, r.total] for r in spend_by_cat]
    status_dist_list  = [[r.status, r.count] for r in status_dist]

    return render_template('dashboard/reports.html',
        spend_by_cat=spend_by_cat_list,
        status_dist=status_dist_list,
        vendors=vendors,
        total_spend=total_spend,
        total_requests=total_requests,
        total_vendors=total_vendors,
        compliance=compliance,
    )
