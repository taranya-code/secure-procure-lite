from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import datetime
from ..extensions import db
from ..models import Approval, PurchaseRequest, User
from ..utils import require_roles, audit_log, notify

bp = Blueprint('approvals', __name__)


@bp.route('/approvals')
@login_required
@require_roles('APPROVER', 'ADMIN')
def list_approvals():
    pending = Approval.query.filter_by(status='PENDING').order_by(Approval.created_at).all()
    decided = Approval.query.filter(Approval.status != 'PENDING').order_by(Approval.decided_at.desc()).limit(20).all()
    return render_template('dashboard/approvals.html', pending=pending, decided=decided)


@bp.route('/approvals/<int:appr_id>/decide', methods=['POST'])
@login_required
@require_roles('APPROVER', 'ADMIN')
def decide(appr_id):
    appr = Approval.query.get_or_404(appr_id)
    pr   = PurchaseRequest.query.get_or_404(appr.request_id)

    # Self-approval prevention
    if pr.created_by == current_user.id:
        audit_log('SELF_APPROVAL_BLOCKED', 'APPROVAL', appr_id,
                  {'request_id': pr.id, 'user_id': current_user.id})
        db.session.commit()
        flash('You cannot approve your own purchase request.', 'danger')
        return redirect(url_for('approvals.list_approvals'))

    decision = request.form.get('decision')
    comments = request.form.get('comments', '').strip()

    if decision not in ('APPROVED', 'REJECTED'):
        flash('Invalid decision.', 'danger')
        return redirect(url_for('approvals.list_approvals'))

    appr.status     = decision
    appr.decided_by = current_user.id
    appr.comments   = comments
    appr.decided_at = datetime.utcnow()

    if decision == 'REJECTED':
        pr.status = 'REJECTED'
        notify(pr.created_by, 'REQUEST_REJECTED', 'Request Rejected',
               f'Your request "{pr.title}" was rejected. Reason: {comments or "No comment"}',
               link=url_for('requests.view_request', req_id=pr.id))
    else:
        # Check if all levels are now approved
        all_approvals = Approval.query.filter_by(request_id=pr.id).all()
        pending_others = [a for a in all_approvals if a.id != appr_id and a.status == 'PENDING']
        if not pending_others:
            pr.status = 'APPROVED'
            notify(pr.created_by, 'REQUEST_APPROVED', 'Request Approved',
                   f'Your request "{pr.title}" has been fully approved!',
                   link=url_for('requests.view_request', req_id=pr.id))
        else:
            pr.status = 'UNDER_REVIEW'

    audit_log('APPROVAL_DECISION', 'APPROVAL', appr_id,
              {'decision': decision, 'request_id': pr.id, 'comments': comments})
    db.session.commit()
    flash(f'Request {decision.lower()}.', 'success' if decision == 'APPROVED' else 'warning')
    return redirect(url_for('approvals.list_approvals'))
