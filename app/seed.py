"""
Demo data seed for SecureProcure Lite.
Idempotent — safe to run multiple times (skips if admin already exists).
"""
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from .extensions import db
from .models import (User, Vendor, PurchaseRequest, RequestItem,
                     Approval, RFQ, RFQVendor, Quotation, QuotationItem,
                     AuditLog, Notification)


HASH = generate_password_hash('password123')


def seed_demo_data():
    # Skip if already seeded
    if User.query.filter_by(email='admin@demo.com').first():
        return

    # ── Users ──────────────────────────────────────────────────────────────
    admin   = User(name='Arjun Sharma',       email='admin@demo.com',    password_hash=HASH, role='ADMIN',                department='IT')
    officer = User(name='Priya Nair',         email='officer@demo.com',  password_hash=HASH, role='PROCUREMENT_OFFICER', department='Procurement')
    approver= User(name='Rajesh Iyer',        email='approver@demo.com', password_hash=HASH, role='APPROVER',            department='Finance')
    auditor = User(name='Meera Krishnamurthy',email='auditor@demo.com',  password_hash=HASH, role='AUDITOR',             department='Compliance')
    v1user  = User(name='Tata Tech Supplies', email='vendor1@demo.com',  password_hash=HASH, role='VENDOR')
    v2user  = User(name='Infosys Procurement',email='vendor2@demo.com',  password_hash=HASH, role='VENDOR')
    v3user  = User(name='Wipro IT Solutions', email='vendor3@demo.com',  password_hash=HASH, role='VENDOR')

    for u in [admin, officer, approver, auditor, v1user, v2user, v3user]:
        db.session.add(u)
    db.session.flush()

    # ── Vendors ─────────────────────────────────────────────────────────────
    v1 = Vendor(user_id=v1user.id, company_name='Tata Tech Supplies Pvt. Ltd.',
                registration_no='TTS-MH-2024-001', contact_phone='+91-22-4567-8901',
                category='IT Hardware', status='APPROVED',
                reputation_score=87.5, total_orders=24, on_time_delivery=91.7,
                trust_score=88.5, fraud_probability=0.12, compliance_score=90.0, eligibility_score=92.2, ai_risk_blocked=False)
    v2 = Vendor(user_id=v2user.id, company_name='Infosys Procurement Services',
                registration_no='IPS-KA-2024-042', contact_phone='+91-80-2345-6789',
                category='IT Hardware', status='APPROVED',
                reputation_score=79.0, total_orders=15, on_time_delivery=80.0,
                trust_score=79.6, fraud_probability=0.19, compliance_score=80.5, eligibility_score=82.4, ai_risk_blocked=False)
    v3 = Vendor(user_id=v3user.id, company_name='Wipro IT Solutions Ltd.',
                registration_no='WIS-KA-2024-007', contact_phone='+91-80-3456-7890',
                category='IT Hardware', status='APPROVED',
                reputation_score=93.2, total_orders=38, on_time_delivery=97.4,
                trust_score=95.2, fraud_probability=0.08, compliance_score=96.0, eligibility_score=96.8, ai_risk_blocked=False)
    v4user  = User(name='Fraud Watch Logistics', email='fraud-suspect@demo.com', password_hash=HASH, role='VENDOR')
    db.session.add(v4user)
    db.session.flush()
    v4 = Vendor(user_id=v4user.id, company_name='Fraud Watch Logistics Pvt. Ltd.',
                registration_no='FWL-GJ-2024-121', contact_phone='+91-79-5566-7788',
                category='Logistics', status='SUSPENDED',
                reputation_score=32.0, total_orders=4, on_time_delivery=55.0,
                trust_score=42.1, fraud_probability=0.82, compliance_score=54.0, eligibility_score=35.0, ai_risk_blocked=True)
    for v in [v1, v2, v3, v4]:
        db.session.add(v)
    db.session.flush()

    # ── Request 1: Full workflow (PO_ISSUED) ────────────────────────────────
    req1 = PurchaseRequest(
        title='Data Centre Server Upgrade — Q2 FY2026',
        description='Upgrade data centre servers at Pune facility to support AI workloads and increased user load across regional offices',
        category='IT Hardware', estimated_budget=3800000, currency='INR',
        urgency='HIGH', status='PO_ISSUED', created_by=officer.id,
        created_at=datetime.utcnow() - timedelta(days=10),
    )
    db.session.add(req1)
    db.session.flush()

    db.session.add(RequestItem(request_id=req1.id, item_name='Dell PowerEdge R750 Server',
                               quantity=3, unit='units', specifications='32-core, 256GB RAM, 4TB NVMe SSD'))
    db.session.add(RequestItem(request_id=req1.id, item_name='10GbE Managed Network Switch',
                               quantity=2, unit='units', specifications='24-port, rack-mount, Layer 3'))

    # Approvals for req1
    appr1 = Approval(request_id=req1.id, level=1, approver_role='APPROVER',
                     status='APPROVED', decided_by=approver.id,
                     comments='Approved. Budget within Q2 FY26 IT capex allocation.',
                     decided_at=datetime.utcnow() - timedelta(days=8),
                     created_at=datetime.utcnow() - timedelta(days=9))
    appr2 = Approval(request_id=req1.id, level=2, approver_role='APPROVER',
                     status='APPROVED', decided_by=admin.id,
                     comments='Second level approved. Proceed with RFQ.',
                     decided_at=datetime.utcnow() - timedelta(days=7),
                     created_at=datetime.utcnow() - timedelta(days=9))
    db.session.add_all([appr1, appr2])
    db.session.flush()

    # RFQ for req1
    rfq1 = RFQ(request_id=req1.id, issued_by=officer.id,
               deadline=datetime.utcnow() + timedelta(days=3),
               notes='Please include GST breakup, warranty terms (min 3 years), and AMC options.',
               status='CLOSED',
               created_at=datetime.utcnow() - timedelta(days=6))
    db.session.add(rfq1)
    db.session.flush()

    db.session.add_all([
        RFQVendor(rfq_id=rfq1.id, vendor_id=v1.id),
        RFQVendor(rfq_id=rfq1.id, vendor_id=v2.id),
        RFQVendor(rfq_id=rfq1.id, vendor_id=v3.id),
    ])

    # Quotations for req1 (INR amounts)
    q1 = Quotation(rfq_id=rfq1.id, vendor_id=v1.id, total_amount=3650000,
                   delivery_days=14, validity_days=30, status='REJECTED',
                   ai_score=78.5,
                   ai_summary='Competitive price but longer delivery. Solid track record.',
                   submitted_at=datetime.utcnow() - timedelta(days=5))
    q2 = Quotation(rfq_id=rfq1.id, vendor_id=v2.id, total_amount=4020000,
                   delivery_days=10, validity_days=45, status='REJECTED',
                   ai_score=65.2,
                   ai_summary='Higher price than competitors. Faster delivery is a plus.',
                   submitted_at=datetime.utcnow() - timedelta(days=5))
    q3 = Quotation(rfq_id=rfq1.id, vendor_id=v3.id, total_amount=3520000,
                   delivery_days=10, validity_days=60, status='SELECTED',
                   ai_score=91.8,
                   ai_summary='Best value: lowest price, fast delivery, highest reputation. Recommended.',
                   submitted_at=datetime.utcnow() - timedelta(days=4))
    db.session.add_all([q1, q2, q3])
    db.session.flush()

    for q, items in [
        (q1, [('Dell PowerEdge R750 Server', 1080000, 3), ('10GbE Managed Network Switch', 205000, 2)]),
        (q2, [('Dell PowerEdge R750 Server', 1200000, 3), ('10GbE Managed Network Switch', 210000, 2)]),
        (q3, [('Dell PowerEdge R750 Server', 1040000, 3), ('10GbE Managed Network Switch', 200000, 2)]),
    ]:
        for name, price, qty in items:
            db.session.add(QuotationItem(quotation_id=q.id, item_name=name,
                                         unit_price=price, quantity=qty, total=price*qty))

    # ── Request 2: In approval (UNDER_REVIEW) ───────────────────────────────
    req2 = PurchaseRequest(
        title='Office Furniture Replacement — Bengaluru HQ',
        description='Replace ageing office chairs and desks for 50 workstations at Bengaluru headquarters',
        category='Office Equipment', estimated_budget=2200000, currency='INR',
        urgency='NORMAL', status='UNDER_REVIEW', created_by=officer.id,
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    db.session.add(req2)
    db.session.flush()

    db.session.add(RequestItem(request_id=req2.id, item_name='Ergonomic Office Chair',
                               quantity=50, unit='units', specifications='Lumbar support, adjustable height, mesh back'))
    db.session.add(RequestItem(request_id=req2.id, item_name='Height-Adjustable Standing Desk',
                               quantity=25, unit='units', specifications='140cm wide, electric, cable management tray'))

    appr3 = Approval(request_id=req2.id, level=1, approver_role='APPROVER',
                     status='APPROVED', decided_by=approver.id,
                     comments='Level 1 approved. Reasonable for 50 workstations.',
                     decided_at=datetime.utcnow() - timedelta(days=1),
                     created_at=datetime.utcnow() - timedelta(days=2))
    appr4 = Approval(request_id=req2.id, level=2, approver_role='APPROVER',
                     status='PENDING', created_at=datetime.utcnow() - timedelta(days=2))
    db.session.add_all([appr3, appr4])

    # ── Request 3: Fresh DRAFT ───────────────────────────────────────────────
    req3 = PurchaseRequest(
        title='Cloud Storage Expansion — 500TB DR Tier',
        description='Expand cloud storage for backup and disaster recovery workloads across Mumbai and Chennai DCs',
        category='Cloud Services', estimated_budget=720000, currency='INR',
        urgency='LOW', status='DRAFT', created_by=officer.id,
        created_at=datetime.utcnow() - timedelta(hours=3),
    )
    db.session.add(req3)
    db.session.flush()
    db.session.add(RequestItem(request_id=req3.id, item_name='Cloud Object Storage 500TB/year',
                               quantity=1, unit='subscription', specifications='99.99% durability, multi-AZ'))

    # ── Audit Logs ───────────────────────────────────────────────────────────
    logs = [
        AuditLog(user_id=officer.id, action='CREATE', entity_type='PURCHASE_REQUEST', entity_id=str(req1.id),
                 details='{"title": "Data Centre Server Upgrade"}',
                 created_at=datetime.utcnow() - timedelta(days=10)),
        AuditLog(user_id=officer.id, action='SUBMIT', entity_type='PURCHASE_REQUEST', entity_id=str(req1.id),
                 created_at=datetime.utcnow() - timedelta(days=9)),
        AuditLog(user_id=approver.id, action='APPROVAL_DECISION', entity_type='APPROVAL', entity_id=str(appr1.id),
                 details='{"decision": "APPROVED"}', created_at=datetime.utcnow() - timedelta(days=8)),
        AuditLog(user_id=officer.id, action='ISSUE_RFQ', entity_type='RFQ', entity_id=str(rfq1.id),
                 created_at=datetime.utcnow() - timedelta(days=6)),
        AuditLog(user_id=v3user.id, action='SUBMIT_QUOTE', entity_type='QUOTATION', entity_id=str(q3.id),
                 details='{"amount": 3520000}', created_at=datetime.utcnow() - timedelta(days=4)),
        AuditLog(user_id=officer.id, action='SELECT_QUOTE', entity_type='QUOTATION', entity_id=str(q3.id),
                 details='{"vendor": "Wipro IT Solutions Ltd."}', created_at=datetime.utcnow() - timedelta(days=3)),
    ]
    for log in logs:
        db.session.add(log)

    # ── Notifications ────────────────────────────────────────────────────────
    notifs = [
        Notification(user_id=officer.id, type='REQUEST_APPROVED', title='Request Approved',
                     message='Data Centre Server Upgrade has been fully approved!',
                     read=True, created_at=datetime.utcnow() - timedelta(days=7)),
        Notification(user_id=approver.id, type='APPROVAL_REQUIRED', title='Approval Required',
                     message='Office Furniture Replacement — Bengaluru HQ needs your approval.',
                     read=False, link='/requests/2'),
        Notification(user_id=v3user.id, type='GENERAL', title='Quote Selected — PO Issued',
                     message='Your quote for Data Centre Server Upgrade was selected. PO has been issued.',
                     read=False),
        Notification(user_id=officer.id, type='QUOTATION_RECEIVED', title='3 Quotes Received',
                     message='All vendors have submitted quotes for Data Centre Server Upgrade.',
                     read=True, created_at=datetime.utcnow() - timedelta(days=4)),
    ]
    for n in notifs:
        db.session.add(n)

    db.session.commit()
    print('✓ Demo data seeded: 7 users, 3 vendors, 3 requests, 1 RFQ, 3 quotations')
