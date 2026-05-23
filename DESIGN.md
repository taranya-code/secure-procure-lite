# SecureProcure Lite — Design Document

> **Version**: 1.0
> **Date**: 2026-05-20
> **Stack**: Python · Flask · SQLite · HTML · Tailwind CSS (CDN) · Vanilla JS
> **Goal**: Identical feature set to SecureProcure (full-stack TS version) in a college-friendly, zero-build-step stack.

---

## 1. Project Overview

SecureProcure Lite is a web-based collaborative procurement portal that digitises the full procurement lifecycle — from purchase request creation through multi-level approval, RFQ issuance, vendor quoting, AI-assisted analysis, and PO issuance — with a built-in immutable audit trail and fraud detection.

### What's the Same as the Full Version
- All 5 user roles (ADMIN, PROCUREMENT_OFFICER, APPROVER, VENDOR, AUDITOR)
- Complete procurement workflow (Draft → PO Issued)
- Multi-level approval based on budget tiers
- RFQ & vendor quotation system
- AI quote analysis (Claude API — optional)
- Immutable audit logs
- Fraud detection (self-approval block)
- Vendor onboarding approval gate
- Reports & analytics
- Notifications
- In-UI Reset + Seed demo data

### What's Simpler
- **No build step** — Tailwind via CDN, vanilla JS (no React/Next.js/TypeScript)
- **SQLite** instead of PostgreSQL (file-based, zero config)
- **Session-based auth** instead of JWT (Flask-Login + server sessions)
- **Server-rendered HTML** (Jinja2) instead of React SPA
- **Single Python process** instead of separate backend + frontend servers
- **No npm/node** required at all

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Web Framework | Flask 3.x |
| ORM | SQLAlchemy 2.x (Flask-SQLAlchemy) |
| Database | SQLite (file: `data/procure.db`) |
| Auth | Flask-Login + Werkzeug password hashing |
| Migrations | Flask-Migrate (Alembic) |
| Templates | Jinja2 (server-rendered) |
| CSS | Tailwind CSS (CDN) |
| JS | Vanilla JS (fetch API for dynamic calls) |
| Charts | Chart.js (CDN) |
| AI | Anthropic Python SDK (optional) |
| Icons | Lucide Icons (CDN) |

---

## 3. Directory Structure

```
secure-procure-lite/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Config class (dev/prod)
│   ├── models.py            # All SQLAlchemy models
│   ├── extensions.py        # db, login_manager, migrate
│   ├── utils.py             # Helpers: audit_log(), rbac decorator
│   ├── seed.py              # Demo data seed function
│   └── routes/
│       ├── __init__.py
│       ├── auth.py          # /login /logout /register
│       ├── dashboard.py     # / (main dashboard)
│       ├── requests.py      # /requests/*
│       ├── approvals.py     # /approvals/*
│       ├── rfq.py           # /rfq/*
│       ├── vendors.py       # /vendors/*
│       ├── audit.py         # /audit/*
│       ├── reports.py       # /reports
│       ├── notifications.py # /notifications/*
│       ├── admin.py         # /admin/* (users, reset, seed)
│       └── api.py           # /api/* (JSON endpoints for JS calls)
├── templates/
│   ├── base.html            # Layout with sidebar + nav
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   └── dashboard/
│       ├── index.html       # Dashboard home
│       ├── requests.html    # Purchase requests list + create
│       ├── request_detail.html
│       ├── approvals.html   # Approval queue
│       ├── rfq.html         # RFQ list + issue
│       ├── rfq_detail.html  # Quotations + AI analysis
│       ├── vendors.html     # Vendor management
│       ├── audit.html       # Audit logs + fraud alerts
│       ├── reports.html     # Charts + analytics
│       ├── my_quotes.html   # Vendor quote submission
│       ├── notifications.html
│       ├── users.html       # Admin user management
│       └── admin_panel.html # Reset/seed data controls
├── static/
│   ├── css/
│   │   └── app.css          # Custom styles (minimal)
│   └── js/
│       └── app.js           # Shared JS utilities
├── data/                    # SQLite DB lives here (gitignored)
├── requirements.txt
├── run.py                   # App entry point
├── procure-lite.sh          # Start/stop/status/restart script
└── DESIGN.md
```

---

## 4. Database Schema (SQLite via SQLAlchemy)

### Enums (stored as strings)
- **Role**: `ADMIN`, `PROCUREMENT_OFFICER`, `APPROVER`, `VENDOR`, `AUDITOR`
- **VendorStatus**: `PENDING`, `APPROVED`, `REJECTED`, `SUSPENDED`
- **RequestStatus**: `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `RFQ_ISSUED`, `QUOTED`, `PO_ISSUED`, `COMPLETED`, `CANCELLED`
- **RFQStatus**: `OPEN`, `CLOSED`, `CANCELLED`
- **QuotationStatus**: `SUBMITTED`, `REJECTED`, `SELECTED`
- **ApprovalStatus**: `PENDING`, `APPROVED`, `REJECTED`

### Tables

```
users               vendors             purchase_requests
─────────────       ────────────────    ─────────────────────
id (PK)             id (PK)             id (PK)
name                user_id (FK)        title
email (unique)      company_name        description
password_hash       registration_no     category
role                contact_phone       estimated_budget
department          address             currency
is_active           category            urgency
created_at          status              status
                    reputation_score    created_by (FK)
                    total_orders        created_at
                    on_time_delivery    updated_at
                    created_at

request_items       rfqs                rfq_vendors
──────────────      ──────────          ───────────
id (PK)             id (PK)             id (PK)
request_id (FK)     request_id (FK)     rfq_id (FK)
item_name           issued_by (FK)      vendor_id (FK)
quantity            deadline            invited_at
unit                notes
specifications      status
                    created_at

quotations          quotation_items     approvals
──────────────      ───────────────     ─────────────
id (PK)             id (PK)             id (PK)
rfq_id (FK)         quotation_id (FK)   request_id (FK)
vendor_id (FK)      item_name           level
total_amount        unit_price          approver_role
delivery_days       quantity            status
validity_days       total               decided_by (FK)
notes                                   comments
status                                  decided_at
ai_score                                created_at
ai_summary
submitted_at

audit_logs          notifications
──────────────      ─────────────────
id (PK)             id (PK)
user_id (FK)        user_id (FK)
action              type
entity_type         title
entity_id           message
details (JSON str)  read
ip_address          link
created_at          created_at
```

---

## 5. API Routes

### Auth
| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/login` | Login page + form handler |
| GET/POST | `/register` | Register page + form handler |
| POST | `/logout` | Logout |

### Dashboard
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Dashboard (redirect to `/dashboard`) |
| GET | `/dashboard` | KPI cards + spend chart |

### Purchase Requests
| Method | Route | Description | Roles |
|--------|-------|-------------|-------|
| GET | `/requests` | List all requests | All |
| POST | `/requests` | Create new request | OFFICER, ADMIN |
| GET | `/requests/<id>` | Request detail | All |
| POST | `/requests/<id>/submit` | Submit for approval | OFFICER, ADMIN |
| DELETE | `/requests/<id>` | Delete DRAFT | OFFICER, ADMIN |

### Approvals
| Method | Route | Description | Roles |
|--------|-------|-------------|-------|
| GET | `/approvals` | Pending approval queue | APPROVER, ADMIN |
| POST | `/approvals/<id>/decide` | Approve or reject | APPROVER, ADMIN |

### RFQ & Quotations
| Method | Route | Description | Roles |
|--------|-------|-------------|-------|
| GET | `/rfq` | RFQ list | OFFICER, ADMIN |
| POST | `/rfq` | Issue new RFQ | OFFICER, ADMIN |
| GET | `/rfq/<id>` | RFQ detail + quotations | OFFICER, ADMIN |
| POST | `/rfq/<id>/select/<qid>` | Select winning quote | OFFICER, ADMIN |
| GET | `/my-quotes` | Vendor's open RFQs | VENDOR |
| POST | `/my-quotes/<rfq_id>/submit` | Submit quotation | VENDOR |

### Vendors
| Method | Route | Description | Roles |
|--------|-------|-------------|-------|
| GET | `/vendors` | Vendor list | All |
| POST | `/vendors/<id>/status` | Approve/reject vendor | ADMIN, OFFICER |

### Audit
| Method | Route | Description | Roles |
|--------|-------|-------------|-------|
| GET | `/audit` | Audit log table | AUDITOR, ADMIN |

### Reports
| Method | Route | Description | Roles |
|--------|-------|-------------|-------|
| GET | `/reports` | Analytics + charts | All |

### Admin
| Method | Route | Description | Roles |
|--------|-------|-------------|-------|
| GET | `/admin/users` | User list + management | ADMIN |
| POST | `/admin/users/<id>/toggle` | Activate/deactivate | ADMIN |
| GET | `/admin/panel` | Reset/seed panel | ADMIN |

### JSON API (for JS fetch calls)
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/admin/reset` | Drop + recreate all tables |
| POST | `/api/admin/seed` | Seed demo data |
| GET | `/api/notifications` | Get notifications JSON |
| POST | `/api/notifications/<id>/read` | Mark read |
| POST | `/api/rfq/<id>/analyze` | AI quote analysis |

---

## 6. Role-Based Access Matrix

| Feature | ADMIN | OFFICER | APPROVER | VENDOR | AUDITOR |
|---------|-------|---------|----------|--------|---------|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create Request | ✅ | ✅ | ❌ | ❌ | ❌ |
| Submit Request | ✅ | ✅ | ❌ | ❌ | ❌ |
| Approve Request | ✅ | ❌ | ✅ | ❌ | ❌ |
| Issue RFQ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Submit Quote | ❌ | ❌ | ❌ | ✅ | ❌ |
| Select Quote | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage Vendors | ✅ | ✅ | ❌ | ❌ | ❌ |
| Audit Logs | ✅ | ❌ | ❌ | ❌ | ✅ |
| Reports | ✅ | ✅ | ✅ | ❌ | ✅ |
| User Management | ✅ | ❌ | ❌ | ❌ | ❌ |
| Reset/Seed Data | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 7. Procurement Workflow

```
[DRAFT] ──submit──▶ [SUBMITTED] ──auto──▶ [UNDER_REVIEW]
                                                │
                                         ┌──approve──┐
                                         ▼           ▼
                                     [APPROVED]  [REJECTED]
                                         │
                                    issue RFQ
                                         │
                                         ▼
                                    [RFQ_ISSUED]
                                         │
                                  vendors quote
                                         │
                                         ▼
                                      [QUOTED]
                                         │
                                   select vendor
                                         │
                                         ▼
                                    [PO_ISSUED]
```

**Approval Level Logic:**
- Budget < $10,000 → 1 level (APPROVER)
- Budget $10,000–$100,000 → 2 levels (APPROVER × 2)
- Budget > $100,000 → 3 levels (APPROVER × 3)

---

## 8. Security Features

1. **Session-based auth** — Flask-Login manages session cookies (HTTP-only, Secure in prod)
2. **Password hashing** — Werkzeug `generate_password_hash` / `check_password_hash` (PBKDF2-SHA256)
3. **RBAC decorator** — `@require_roles(*roles)` on every route
4. **Self-approval prevention** — Checked at `/approvals/<id>/decide`
5. **Immutable audit log** — `audit_log()` called on every mutation, no DELETE route
6. **CSRF protection** — Flask-WTF CSRF token in all forms
7. **Input validation** — Server-side validation on all POST handlers

---

## 9. Demo Data (Seed)

### Users (all password: `password123`)
| Email | Role | Name |
|-------|------|------|
| admin@demo.com | ADMIN | System Admin |
| officer@demo.com | PROCUREMENT_OFFICER | Sarah Johnson |
| approver@demo.com | APPROVER | Michael Chen |
| auditor@demo.com | AUDITOR | Emily Rodriguez |
| vendor1@demo.com | VENDOR | TechSupply Corp |
| vendor2@demo.com | VENDOR | GlobalTech Solutions |
| vendor3@demo.com | VENDOR | Prime IT Distributors |

### Pre-seeded Data
- 3 vendors (APPROVED status, with reputation scores)
- 2 purchase requests:
  - **Request 1**: Server Infrastructure Upgrade ($45,000) — PO_ISSUED (full workflow complete)
  - **Request 2**: Office Furniture Replacement ($28,000) — UNDER_REVIEW (awaiting approval)
- RFQ + 3 quotations for Request 1 (with AI scores)
- Approval records, audit logs, notifications

---

## 10. Task Status Tracker

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Design document | ✅ Done | This file |
| 2 | Project scaffold + shell script | ✅ Done | procure-lite.sh |
| 3 | Flask core (models, auth, extensions) | 🔄 In Progress | |
| 4 | All route blueprints | ⏳ Pending | |
| 5 | All HTML templates | ⏳ Pending | |
| 6 | Seed/reset system + UI panel | ⏳ Pending | |
| 7 | End-to-end testing + fixes | ⏳ Pending | |

---

## 11. Running the App

```bash
cd secure-procure-lite
./procure-lite.sh start    # Install deps, init DB, start Flask
./procure-lite.sh stop     # Stop the server
./procure-lite.sh status   # Show server status
./procure-lite.sh restart  # Stop + start
```

App runs at: **http://localhost:5001**

### First Run
The shell script automatically:
1. Creates a Python virtualenv (`venv/`)
2. Installs `requirements.txt`
3. Initialises the SQLite database
4. Seeds demo data
5. Starts Flask on port 5001
