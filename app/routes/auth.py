from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from ..models import User, Vendor
from ..utils import audit_log, compute_vendor_risk, adaptive_security_guard

bp = Blueprint('auth', __name__)


@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Account is deactivated. Contact admin.', 'danger')
                return render_template('auth/login.html')

            if adaptive_security_guard('LOGIN', 'USER', user.id, {
                    'user_agent': request.headers.get('User-Agent', ''),
                    'ip_address': request.remote_addr,
                }):
                db.session.commit()
                flash('Login attempt flagged by adaptive security. Contact support.', 'danger')
                return render_template('auth/login.html')

            if user.role == 'VENDOR' and user.vendor:
                compute_vendor_risk(user.vendor)
                if user.vendor.ai_risk_blocked:
                    db.session.commit()
                    flash('Your vendor account is blocked due to risk review. Contact the procurement team.', 'danger')
                    return render_template('auth/login.html')

            login_user(user, remember=True)
            audit_log('LOGIN', 'USER', user.id)
            db.session.commit()
            return redirect(url_for('dashboard.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'PROCUREMENT_OFFICER')
        dept     = request.form.get('department', '').strip()

        allowed_roles = ['PROCUREMENT_OFFICER', 'APPROVER', 'VENDOR', 'AUDITOR']
        if role not in allowed_roles:
            flash('Invalid role selected.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/register.html')

        user = User(
            name=name, email=email,
            password_hash=generate_password_hash(password),
            role=role, department=dept or None,
        )
        db.session.add(user)
        db.session.flush()

        if role == 'VENDOR':
            company = request.form.get('company_name', name).strip()
            vendor = Vendor(user_id=user.id, company_name=company, status='PENDING')
            db.session.add(vendor)

        audit_log('REGISTER', 'USER', user.id, {'role': role})
        db.session.commit()
        login_user(user, remember=True)
        flash('Account created! Welcome to SecureProcure.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    audit_log('LOGOUT', 'USER', current_user.id)
    db.session.commit()
    logout_user()
    flash('Signed out successfully.', 'info')
    return redirect(url_for('auth.login'))
