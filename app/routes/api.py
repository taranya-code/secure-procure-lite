import os, json
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from ..extensions import db
from ..models import Notification, RFQ, Quotation, User
from ..utils import require_roles, audit_log

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/notifications')
@login_required
def get_notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id, read=False).order_by(
        Notification.created_at.desc()).limit(10).all()
    return jsonify([{
        'id': n.id, 'title': n.title, 'message': n.message,
        'type': n.type, 'link': n.link,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
    } for n in notifs])


@bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    n = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    n.read = True
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/rfq/<int:rfq_id>/analyze', methods=['POST'])
@login_required
@require_roles('PROCUREMENT_OFFICER', 'ADMIN')
def analyze_quotes(rfq_id):
    """Run AI analysis on all quotations for an RFQ."""
    rfq = RFQ.query.get_or_404(rfq_id)
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')

    if not api_key or api_key.startswith('sk-ant-...'):
        # Mock scoring when no API key
        for i, q in enumerate(rfq.quotations):
            scores = [82.0, 71.5, 91.0, 65.0, 78.0]
            summaries = [
                'Competitive pricing with reliable delivery track record.',
                'Higher price offset by faster delivery commitment.',
                'Best value: lowest cost, strong reputation, fast delivery.',
                'Above-market pricing; limited advantages noted.',
                'Solid mid-range option with acceptable terms.',
            ]
            q.ai_score   = scores[i % len(scores)]
            q.ai_summary = summaries[i % len(summaries)]
        db.session.commit()
        return jsonify({'ok': True, 'mock': True,
                       'message': 'Mock scores applied (no API key configured)'})

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        quotes_text = '\n'.join([
            f"Vendor: {q.vendor.company_name}, Amount: ${q.total_amount:,.2f}, "
            f"Delivery: {q.delivery_days} days, Validity: {q.validity_days} days, "
            f"Reputation: {q.vendor.reputation_score}/100, "
            f"Notes: {q.notes or 'N/A'}"
            for q in rfq.quotations
        ])

        prompt = f"""Analyze these vendor quotations for "{rfq.request.title}" and score each 0-100.
Consider: price competitiveness, delivery speed, vendor reputation, validity period.

Quotations:
{quotes_text}

Return JSON array:
[{{"vendor": "name", "score": 85, "summary": "2-sentence reason"}}]
Return ONLY the JSON array."""

        msg = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=1024,
            messages=[{'role': 'user', 'content': prompt}]
        )
        text = msg.content[0].text.strip()
        # Extract JSON
        start = text.find('[')
        end   = text.rfind(']') + 1
        results = json.loads(text[start:end])

        for item in results:
            for q in rfq.quotations:
                if q.vendor.company_name.lower() in item.get('vendor', '').lower():
                    q.ai_score   = item.get('score', 0)
                    q.ai_summary = item.get('summary', '')

        audit_log('AI_ANALYSIS', 'RFQ', rfq_id, {'quotes_analyzed': len(rfq.quotations)})
        db.session.commit()
        return jsonify({'ok': True, 'mock': False})

    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/admin/reset', methods=['POST'])
@login_required
@require_roles('ADMIN')
def reset_data():
    """Drop all data, recreate tables, and immediately re-seed demo data.
    Seeding is done here (not in a separate request) because the reset
    invalidates the session, so a follow-up /seed request would redirect to login.
    """
    try:
        from flask import session
        from ..seed import seed_demo_data
        db.drop_all()
        db.create_all()
        seed_demo_data()
        session.clear()
        return jsonify({'ok': True, 'message': 'Database reset and demo data seeded. Please log in again.'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/admin/seed', methods=['POST'])
@login_required
@require_roles('ADMIN')
def seed_data():
    """Seed demo data (only if DB already has tables and admin is logged in)."""
    try:
        from ..seed import seed_demo_data
        seed_demo_data()
        return jsonify({'ok': True, 'message': 'Demo data seeded successfully!'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/admin/delete-data', methods=['POST'])
@login_required
@require_roles('ADMIN')
def delete_app_data():
    """Delete all transactional data but keep all user accounts.
    Deletes: PurchaseRequest, Approval, RFQ, Quotation, Vendor, AuditLog, Notification.
    Preserves: User records so everyone can still log in.
    """
    try:
        from ..models import (PurchaseRequest, RequestItem, Approval,
                              RFQ, RFQVendor, Quotation, QuotationItem,
                              AuditLog, Notification, Vendor)
        # Order matters for FK constraints
        QuotationItem.query.delete()
        Quotation.query.delete()
        RFQVendor.query.delete()
        RFQ.query.delete()
        Approval.query.delete()
        RequestItem.query.delete()
        PurchaseRequest.query.delete()
        AuditLog.query.delete()
        Notification.query.delete()
        Vendor.query.delete()
        db.session.commit()
        return jsonify({'ok': True, 'message': 'All app data deleted. Users preserved. Ready for your own demo!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/admin/set-demo-password', methods=['POST'])
@login_required
@require_roles('ADMIN')
def set_demo_password():
    """Change the password for all 7 demo accounts at once."""
    data = request.get_json(silent=True) or {}
    password = data.get('password', '').strip()
    if len(password) < 6:
        return jsonify({'ok': False, 'error': 'Password must be at least 6 characters.'}), 400
    demo_emails = [
        'admin@demo.com', 'officer@demo.com', 'approver@demo.com',
        'auditor@demo.com', 'vendor1@demo.com', 'vendor2@demo.com', 'vendor3@demo.com',
    ]
    updated = 0
    hashed = generate_password_hash(password)
    for email in demo_emails:
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = hashed
            updated += 1
    audit_log('DEMO_PASSWORD_CHANGE', 'USER', current_user.id, {'accounts_updated': updated})
    db.session.commit()
    return jsonify({'ok': True, 'message': f'Password updated for {updated} demo account(s).'})


@bp.route('/admin/emergency-seed', methods=['POST'])
def emergency_seed():
    """Recovery endpoint — seeds demo data without requiring login.
    Protected by a static token to prevent abuse.
    Use when reset left the DB empty and you cannot log in.
    POST /api/admin/emergency-seed  with header  X-Recovery-Token: demo-recovery-2026
    """
    token = request.headers.get('X-Recovery-Token', '')
    if token != 'demo-recovery-2026':
        return jsonify({'ok': False, 'error': 'Invalid recovery token'}), 403
    try:
        from ..seed import seed_demo_data
        db.create_all()
        seed_demo_data()
        return jsonify({'ok': True, 'message': 'Emergency seed complete. Login with admin@demo.com / password123'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
