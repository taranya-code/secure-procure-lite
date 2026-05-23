from datetime import datetime
from flask_login import UserMixin
from .extensions import db


# ── Users ─────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(30), nullable=False, default='PROCUREMENT_OFFICER')
    department    = db.Column(db.String(100))
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    vendor         = db.relationship('Vendor', back_populates='user', uselist=False)
    requests       = db.relationship('PurchaseRequest', back_populates='creator', foreign_keys='PurchaseRequest.created_by')
    approvals      = db.relationship('Approval', back_populates='decider', foreign_keys='Approval.decided_by')
    audit_logs     = db.relationship('AuditLog', back_populates='user')
    notifications  = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')

    def has_role(self, *roles):
        return self.role in roles

    def __repr__(self):
        return f'<User {self.email}>'


# ── Vendors ───────────────────────────────────────────────────────────────────

class Vendor(db.Model):
    __tablename__ = 'vendors'
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    company_name     = db.Column(db.String(150), nullable=False)
    registration_no  = db.Column(db.String(60), unique=True)
    contact_phone    = db.Column(db.String(30))
    address          = db.Column(db.Text)
    category            = db.Column(db.String(80))
    status              = db.Column(db.String(20), default='PENDING')
    reputation_score    = db.Column(db.Float, default=0.0)
    total_orders        = db.Column(db.Integer, default=0)
    on_time_delivery    = db.Column(db.Float, default=0.0)
    trust_score         = db.Column(db.Float, default=0.0)
    fraud_probability   = db.Column(db.Float, default=0.0)
    compliance_score    = db.Column(db.Float, default=0.0)
    eligibility_score   = db.Column(db.Float, default=0.0)
    ai_risk_blocked     = db.Column(db.Boolean, default=False)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    user       = db.relationship('User', back_populates='vendor')
    rfq_invites = db.relationship('RFQVendor', back_populates='vendor', cascade='all, delete-orphan')
    quotations = db.relationship('Quotation', back_populates='vendor')


# ── Purchase Requests ─────────────────────────────────────────────────────────

class PurchaseRequest(db.Model):
    __tablename__ = 'purchase_requests'
    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(200), nullable=False)
    description      = db.Column(db.Text)
    category         = db.Column(db.String(80), nullable=False)
    estimated_budget = db.Column(db.Float, nullable=False)
    currency         = db.Column(db.String(10), default='USD')
    urgency          = db.Column(db.String(20), default='NORMAL')
    status           = db.Column(db.String(30), default='DRAFT')
    created_by       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator   = db.relationship('User', back_populates='requests', foreign_keys=[created_by])
    items     = db.relationship('RequestItem', back_populates='request', cascade='all, delete-orphan')
    rfq       = db.relationship('RFQ', back_populates='request', uselist=False)
    approvals = db.relationship('Approval', back_populates='request', cascade='all, delete-orphan')

    def approval_levels_needed(self):
        if self.estimated_budget < 10000:
            return 1
        elif self.estimated_budget <= 100000:
            return 2
        return 3


class RequestItem(db.Model):
    __tablename__ = 'request_items'
    id             = db.Column(db.Integer, primary_key=True)
    request_id     = db.Column(db.Integer, db.ForeignKey('purchase_requests.id'), nullable=False)
    item_name      = db.Column(db.String(150), nullable=False)
    quantity       = db.Column(db.Float, nullable=False)
    unit           = db.Column(db.String(30), nullable=False)
    specifications = db.Column(db.Text)

    request = db.relationship('PurchaseRequest', back_populates='items')


# ── Approvals ─────────────────────────────────────────────────────────────────

class Approval(db.Model):
    __tablename__ = 'approvals'
    id           = db.Column(db.Integer, primary_key=True)
    request_id   = db.Column(db.Integer, db.ForeignKey('purchase_requests.id'), nullable=False)
    level        = db.Column(db.Integer, nullable=False)
    approver_role = db.Column(db.String(30), default='APPROVER')
    status       = db.Column(db.String(20), default='PENDING')
    decided_by   = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments     = db.Column(db.Text)
    decided_at   = db.Column(db.DateTime)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    request = db.relationship('PurchaseRequest', back_populates='approvals')
    decider = db.relationship('User', back_populates='approvals', foreign_keys=[decided_by])


# ── RFQ & Quotations ──────────────────────────────────────────────────────────

class RFQ(db.Model):
    __tablename__ = 'rfqs'
    id         = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('purchase_requests.id'), unique=True, nullable=False)
    issued_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deadline   = db.Column(db.DateTime, nullable=False)
    notes      = db.Column(db.Text)
    status     = db.Column(db.String(20), default='OPEN')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    request    = db.relationship('PurchaseRequest', back_populates='rfq')
    issuer     = db.relationship('User', foreign_keys=[issued_by])
    vendors    = db.relationship('RFQVendor', back_populates='rfq', cascade='all, delete-orphan')
    quotations = db.relationship('Quotation', back_populates='rfq')


class RFQVendor(db.Model):
    __tablename__ = 'rfq_vendors'
    id         = db.Column(db.Integer, primary_key=True)
    rfq_id     = db.Column(db.Integer, db.ForeignKey('rfqs.id'), nullable=False)
    vendor_id  = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    invited_at = db.Column(db.DateTime, default=datetime.utcnow)

    rfq    = db.relationship('RFQ', back_populates='vendors')
    vendor = db.relationship('Vendor', back_populates='rfq_invites')


class Quotation(db.Model):
    __tablename__ = 'quotations'
    id            = db.Column(db.Integer, primary_key=True)
    rfq_id        = db.Column(db.Integer, db.ForeignKey('rfqs.id'), nullable=False)
    vendor_id     = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False)
    total_amount  = db.Column(db.Float, nullable=False)
    delivery_days = db.Column(db.Integer, nullable=False)
    validity_days = db.Column(db.Integer, default=30)
    notes         = db.Column(db.Text)
    status        = db.Column(db.String(20), default='SUBMITTED')
    ai_score      = db.Column(db.Float)
    ai_summary    = db.Column(db.Text)
    submitted_at  = db.Column(db.DateTime, default=datetime.utcnow)

    rfq    = db.relationship('RFQ', back_populates='quotations')
    vendor = db.relationship('Vendor', back_populates='quotations')
    items  = db.relationship('QuotationItem', back_populates='quotation', cascade='all, delete-orphan')


class QuotationItem(db.Model):
    __tablename__ = 'quotation_items'
    id           = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=False)
    item_name    = db.Column(db.String(150), nullable=False)
    unit_price   = db.Column(db.Float, nullable=False)
    quantity     = db.Column(db.Float, nullable=False)
    total        = db.Column(db.Float, nullable=False)

    quotation = db.relationship('Quotation', back_populates='items')


# ── Audit Logs ────────────────────────────────────────────────────────────────

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
    action      = db.Column(db.String(80), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id   = db.Column(db.String(50), nullable=False)
    details     = db.Column(db.Text)    # JSON string
    ip_address  = db.Column(db.String(50))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='audit_logs')


# ── Notifications ─────────────────────────────────────────────────────────────

class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type       = db.Column(db.String(50), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    read       = db.Column(db.Boolean, default=False)
    link       = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='notifications')
