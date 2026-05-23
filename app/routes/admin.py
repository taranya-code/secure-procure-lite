from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from ..extensions import db
from ..models import User, Vendor
from ..utils import require_roles, audit_log, compute_vendor_risk

bp = Blueprint('admin', __name__, url_prefix='/admin')

ROLES = ['ADMIN', 'PROCUREMENT_OFFICER', 'APPROVER', 'AUDITOR', 'VENDOR']


@bp.route('/users')
@login_required
@require_roles('ADMIN')
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('dashboard/users.html', users=all_users, roles=ROLES)


@bp.route('/users/add', methods=['POST'])
@login_required
@require_roles('ADMIN')
def add_user():
    name       = request.form.get('name', '').strip()
    email      = request.form.get('email', '').strip().lower()
    password   = request.form.get('password', '').strip()
    role       = request.form.get('role', 'PROCUREMENT_OFFICER')
    department = request.form.get('department', '').strip()

    if not name or not email or not password:
        flash('Name, email and password are required.', 'danger')
        return redirect(url_for('admin.users'))
    if role not in ROLES:
        flash('Invalid role.', 'danger')
        return redirect(url_for('admin.users'))
    if User.query.filter_by(email=email).first():
        flash(f'Email {email} is already registered.', 'danger')
        return redirect(url_for('admin.users'))

    user = User(
        name=name, email=email,
        password_hash=generate_password_hash(password),
        role=role, department=department or None,
    )
    db.session.add(user)
    db.session.flush()
    audit_log('USER_CREATE', 'USER', user.id, {'name': name, 'role': role})
    db.session.commit()
    flash(f'User {name} created successfully.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@require_roles('ADMIN')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    name       = request.form.get('name', '').strip()
    role       = request.form.get('role', user.role)
    department = request.form.get('department', '').strip()

    if not name:
        flash('Name is required.', 'danger')
        return redirect(url_for('admin.users'))
    if role not in ROLES:
        flash('Invalid role.', 'danger')
        return redirect(url_for('admin.users'))
    # Prevent admin from changing their own role
    if user_id == current_user.id and role != 'ADMIN':
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.users'))

    user.name       = name
    user.role       = role
    user.department = department or None
    audit_log('USER_EDIT', 'USER', user_id, {'name': name, 'role': role})
    db.session.commit()
    flash(f'User {name} updated.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@require_roles('ADMIN')
def reset_password(user_id):
    user     = User.query.get_or_404(user_id)
    password = request.form.get('password', '').strip()
    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'danger')
        return redirect(url_for('admin.users'))
    user.password_hash = generate_password_hash(password)
    audit_log('USER_PASSWORD_RESET', 'USER', user_id, {})
    db.session.commit()
    flash(f'Password reset for {user.name}.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@require_roles('ADMIN')
def toggle_user(user_id):
    if user_id == current_user.id:
        flash('Cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.users'))
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    audit_log('USER_TOGGLE', 'USER', user_id, {'is_active': user.is_active})
    db.session.commit()
    flash(f'User {"activated" if user.is_active else "deactivated"}.', 'info')
    return redirect(url_for('admin.users'))


@bp.route('/panel')
@login_required
@require_roles('ADMIN')
def panel():
    blocked_count = Vendor.query.filter_by(ai_risk_blocked=True).count()
    total_vendors = Vendor.query.count()
    blocked_display = Vendor.query.filter_by(ai_risk_blocked=True).limit(5).all()
    return render_template('dashboard/admin_panel.html', blocked_count=blocked_count,
                           total_vendors=total_vendors, blocked_display=blocked_display)


@bp.route('/docs')
@login_required
@require_roles('ADMIN')
def docs():
    return render_template('dashboard/docs.html')


@bp.route('/security-intelligence')
@login_required
@require_roles('ADMIN')
def security_intelligence():
    selected = request.args.get('view', 'ai_risk')
    valid_views = ['ai_risk', 'trust', 'fraud', 'compliance', 'eligibility']
    selected = selected if selected in valid_views else 'ai_risk'

    vendors = Vendor.query.order_by(Vendor.ai_risk_blocked.desc(), Vendor.created_at.desc()).all()
    for v in vendors:
        compute_vendor_risk(v, v.category)

    total_vendors = len(vendors)
    blocked_count = sum(1 for v in vendors if v.ai_risk_blocked)
    avg_trust = round(sum((v.trust_score or 0) for v in vendors) / total_vendors, 1) if total_vendors else 0
    avg_fraud = round(sum((v.fraud_probability or 0) for v in vendors) / total_vendors, 2) if total_vendors else 0
    avg_compliance = round(sum((v.compliance_score or 0) for v in vendors) / total_vendors, 1) if total_vendors else 0
    avg_eligibility = round(sum((v.eligibility_score or 0) for v in vendors) / total_vendors, 1) if total_vendors else 0
    low_compliance = sum(1 for v in vendors if v.compliance_score is not None and v.compliance_score < 70)
    high_fraud = sum(1 for v in vendors if v.fraud_probability is not None and v.fraud_probability > 0.25)
    top_fraud_vendor = max(vendors, key=lambda v: (v.fraud_probability or 0), default=None)
    suspected_login = top_fraud_vendor.user.email if top_fraud_vendor and top_fraud_vendor.user else None
    fraud_chart_labels = [v.company_name for v in vendors]
    fraud_chart_data = [round((v.fraud_probability or 0) * 100, 1) for v in vendors]

    return render_template(
        'dashboard/security_intel.html',
        vendors=vendors,
        selected=selected,
        total_vendors=total_vendors,
        blocked_count=blocked_count,
        avg_trust=avg_trust,
        avg_fraud=avg_fraud,
        avg_compliance=avg_compliance,
        avg_eligibility=avg_eligibility,
        low_compliance=low_compliance,
        high_fraud=high_fraud,
        top_fraud_vendor=top_fraud_vendor,
        suspected_login=suspected_login,
        fraud_chart_labels=fraud_chart_labels,
        fraud_chart_data=fraud_chart_data,
    )


@bp.route('/vendors-risk')
@login_required
@require_roles('ADMIN')
def vendors_risk():
    # List vendors with AI risk metrics for admin review
    vendors = Vendor.query.order_by(Vendor.created_at.desc()).all()
    for v in vendors:
        compute_vendor_risk(v, v.category)
    return render_template('dashboard/vendor_risk.html', vendors=vendors)


@bp.route('/vendors-risk/<int:vendor_id>/edit')
@login_required
@require_roles('ADMIN')
def edit_vendor_risk(vendor_id):
    v = Vendor.query.get_or_404(vendor_id)
    compute_vendor_risk(v, v.category)
    return render_template('dashboard/vendor_risk_edit.html', vendor=v)


@bp.route('/vendors-risk/<int:vendor_id>/update', methods=['POST'])
@login_required
@require_roles('ADMIN')
def update_vendor_risk(vendor_id):
    v = Vendor.query.get_or_404(vendor_id)
    # Accept manual overrides from admin
    try:
        v.trust_score = float(request.form.get('trust_score', v.trust_score or 0))
        v.fraud_probability = float(request.form.get('fraud_probability', v.fraud_probability or 0))
        v.compliance_score = float(request.form.get('compliance_score', v.compliance_score or 0))
        v.eligibility_score = float(request.form.get('eligibility_score', v.eligibility_score or 0))
        v.ai_risk_blocked = True if request.form.get('ai_risk_blocked') == 'on' else False
    except Exception:
        flash('Invalid input values.', 'danger')
        return redirect(url_for('admin.edit_vendor_risk', vendor_id=vendor_id))
    audit_log('ADMIN_VENDOR_RISK_UPDATE', 'VENDOR', vendor_id,
              {'trust': v.trust_score, 'fraud': v.fraud_probability,
               'compliance': v.compliance_score, 'eligibility': v.eligibility_score,
               'blocked': v.ai_risk_blocked})
    db.session.commit()
    flash('Vendor risk profile updated.', 'success')
    return redirect(url_for('admin.vendors_risk'))
