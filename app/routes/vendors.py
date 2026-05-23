import os
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import Vendor
from ..utils import require_roles, audit_log, notify, compute_vendor_risk, vendor_is_eligible, is_allowed_document, adaptive_security_guard

bp = Blueprint('vendors', __name__)


@bp.route('/vendors')
@login_required
def list_vendors():
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    q = Vendor.query
    if search:
        q = q.filter(Vendor.company_name.ilike(f'%{search}%'))
    if status:
        q = q.filter_by(status=status)
    vendors = q.order_by(Vendor.created_at.desc()).all()
    for vendor in vendors:
        compute_vendor_risk(vendor, vendor.category)
    db.session.commit()
    return render_template('dashboard/vendors.html', vendors=vendors, search=search, status_filter=status)


@bp.route('/vendors/<int:vendor_id>/status', methods=['POST'])
@login_required
@require_roles('ADMIN', 'PROCUREMENT_OFFICER')
def update_status(vendor_id):
    vendor     = Vendor.query.get_or_404(vendor_id)
    new_status = request.form.get('status')
    if new_status not in ('APPROVED', 'REJECTED', 'SUSPENDED', 'PENDING'):
        flash('Invalid status.', 'danger')
        return redirect(url_for('vendors.list_vendors'))

    old_status    = vendor.status
    vendor.status = new_status
    audit_log('VENDOR_STATUS_CHANGE', 'VENDOR', vendor_id,
              {'old': old_status, 'new': new_status})
    compute_vendor_risk(vendor, vendor.category)
    notify(vendor.user_id, 'GENERAL', f'Vendor Status: {new_status}',
           f'Your vendor account has been {new_status.lower()}.',
           link=url_for('vendors.list_vendors'))
    db.session.commit()
    flash(f'Vendor {vendor.company_name} status updated to {new_status}.', 'success')
    return redirect(url_for('vendors.list_vendors'))


@bp.route('/vendor/upload-document', methods=['POST'])
@login_required
@require_roles('VENDOR')
def upload_document():
    vendor = current_user.vendor
    if not vendor:
        flash('Vendor profile not found.', 'danger')
        return redirect(url_for('dashboard.index'))

    if vendor.ai_risk_blocked:
        audit_log('BLOCKED_UPLOAD', 'VENDOR', vendor.id,
                  {'reason': 'risk_blocked', 'eligibility_score': vendor.eligibility_score})
        flash('Document upload blocked due to vendor risk policy. Contact support.', 'danger')
        return redirect(url_for('dashboard.index'))

    file = request.files.get('document')
    if not file or file.filename == '':
        flash('No document selected.', 'warning')
        return redirect(url_for('dashboard.index'))

    if not is_allowed_document(file.filename):
        flash('Only PDF, DOC, XLS, JPG or PNG files are allowed.', 'danger')
        return redirect(url_for('dashboard.index'))

    filename = secure_filename(file.filename)
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'vendor-documents', str(vendor.id))
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    adaptive_security_guard('UPLOAD_DOCUMENT', 'VENDOR', vendor.id,
                            {'document_name': filename, 'upload_path': filepath})
    audit_log('UPLOAD_DOCUMENT', 'VENDOR', vendor.id, {'file': filename})
    notify(current_user.id, 'GENERAL', 'Document Uploaded Securely',
           'Your vendor document was uploaded through the secure procurement portal.')
    db.session.commit()

    flash('Document uploaded securely.', 'success')
    return redirect(url_for('dashboard.index'))
