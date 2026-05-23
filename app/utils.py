import json
import os
from functools import wraps
from flask import request, jsonify, abort
from flask_login import current_user
from .extensions import db
from .models import AuditLog, Notification, Vendor

ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}


def require_roles(*roles):
    """Decorator: restrict route to specific roles. Returns 403 JSON if denied."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def audit_log(action, entity_type, entity_id, details=None):
    """Write an immutable audit log entry."""
    entry = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        details=json.dumps(details) if details else None,
        ip_address=request.remote_addr,
    )
    db.session.add(entry)
    # Flush so the log is committed even if caller rolls back later
    db.session.flush()


def notify(user_id, ntype, title, message, link=None):
    """Create a notification for a user."""
    n = Notification(user_id=user_id, type=ntype, title=title, message=message, link=link)
    db.session.add(n)


def is_allowed_document(filename):
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_DOCUMENT_EXTENSIONS


def compute_vendor_risk(vendor, tender_category=None):
    """Calculate vendor trust, fraud, compliance, eligibility, and risk block status."""
    if not vendor:
        return None

    reputation = float(vendor.reputation_score or 50.0)
    delivery = float(vendor.on_time_delivery or 70.0)
    status_bonus = 100.0 if vendor.status == 'APPROVED' else 60.0
    category_bonus = 10.0 if tender_category and vendor.category and tender_category.lower() in vendor.category.lower() else 0.0

    trust = min(100.0, max(0.0, reputation * 0.42 + delivery * 0.33 + status_bonus * 0.25))
    fraud = min(1.0, max(0.0, 1.0 - trust / 110.0 + (0.08 if vendor.total_orders < 5 else 0.0)))
    compliance = min(100.0, max(0.0, reputation * 0.45 + delivery * 0.35 + status_bonus * 0.20))
    eligibility = min(100.0, max(0.0, trust * 0.55 + compliance * 0.25 - fraud * 40.0 + category_bonus))
    blocked = fraud > 0.75 or eligibility < 40.0 or vendor.status in ('REJECTED', 'SUSPENDED', 'PENDING')

    vendor.trust_score = round(trust, 2)
    vendor.fraud_probability = round(fraud, 3)
    vendor.compliance_score = round(compliance, 2)
    vendor.eligibility_score = round(eligibility, 2)
    vendor.ai_risk_blocked = blocked
    return vendor


def vendor_is_eligible(vendor, tender_category=None, min_score=40.0):
    compute_vendor_risk(vendor, tender_category)
    return (vendor.status == 'APPROVED'
            and not vendor.ai_risk_blocked
            and vendor.eligibility_score >= min_score)


def find_eligible_vendors(vendor_list, tender_category=None, min_score=40.0):
    eligible = []
    for vendor in vendor_list:
        if vendor_is_eligible(vendor, tender_category, min_score):
            eligible.append(vendor)
    return eligible


def adaptive_security_guard(action, entity_type, entity_id, extra=None):
    ip = request.remote_addr or 'unknown'
    ua = request.headers.get('User-Agent', '')
    score = 0
    payload_size = 0
    if extra and isinstance(extra, dict):
        payload_size = int(extra.get('payload_size', 0) or 0)
    if any(marker in ua.lower() for marker in ('curl', 'wget', 'python-requests', 'httpie', 'libwww-perl')):
        score += 40
    if request.headers.get('X-Forwarded-For'):
        score += 10
    if payload_size > 1024 * 1024:
        score += 15
    details = {'ip_address': ip, 'user_agent': ua, 'payload_size': payload_size}
    if extra:
        details.update(extra)
    is_suspicious = score >= 30
    audit_log(action, entity_type, entity_id, details)
    if is_suspicious:
        audit_log('SUSPICIOUS_ACTIVITY', entity_type, entity_id, {'score': score, **details})
    return is_suspicious


CURRENCY_SYMBOLS = {
    'INR': '₹',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
}

def format_currency(amount, currency='INR'):
    symbol = CURRENCY_SYMBOLS.get(currency, currency + ' ')
    # Indian numbering for INR (lakhs/crores), standard otherwise
    if currency == 'INR':
        return f"{symbol}{amount:,.0f}"
    return f"{symbol}{amount:,.0f}"


def currency_symbol(currency='INR'):
    return CURRENCY_SYMBOLS.get(currency, currency + ' ')


def status_badge_class(status):
    mapping = {
        'DRAFT': 'badge-secondary',
        'SUBMITTED': 'badge-info',
        'UNDER_REVIEW': 'badge-warning',
        'APPROVED': 'badge-success',
        'REJECTED': 'badge-danger',
        'RFQ_ISSUED': 'badge-info',
        'QUOTED': 'badge-info',
        'PO_ISSUED': 'badge-success',
        'COMPLETED': 'badge-success',
        'CANCELLED': 'badge-secondary',
        'PENDING': 'badge-warning',
        'SELECTED': 'badge-success',
        'OPEN': 'badge-info',
        'CLOSED': 'badge-secondary',
    }
    return mapping.get(status, 'badge-secondary')
