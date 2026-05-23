from flask import Blueprint, render_template, request
from flask_login import login_required
from ..models import AuditLog
from ..utils import require_roles

bp = Blueprint('audit', __name__)


@bp.route('/audit')
@login_required
@require_roles('AUDITOR', 'ADMIN')
def index():
    entity_type = request.args.get('entity_type', '')
    action      = request.args.get('action', '')
    tab         = request.args.get('tab', 'logs')

    q = AuditLog.query
    if entity_type:
        q = q.filter_by(entity_type=entity_type)
    if action:
        q = q.filter_by(action=action)

    logs = q.order_by(AuditLog.created_at.desc()).limit(200).all()

    fraud_alerts = AuditLog.query.filter_by(action='SELF_APPROVAL_BLOCKED').order_by(
        AuditLog.created_at.desc()).all()

    entity_types = ['PURCHASE_REQUEST', 'APPROVAL', 'VENDOR', 'RFQ', 'QUOTATION', 'USER']
    actions      = ['CREATE', 'SUBMIT', 'APPROVAL_DECISION', 'ISSUE_RFQ',
                    'SUBMIT_QUOTE', 'SELECT_QUOTE', 'VENDOR_STATUS_CHANGE',
                    'LOGIN', 'LOGOUT', 'SELF_APPROVAL_BLOCKED']

    return render_template('dashboard/audit.html',
        logs=logs, fraud_alerts=fraud_alerts, tab=tab,
        entity_types=entity_types, actions=actions,
        filter_entity=entity_type, filter_action=action,
    )
