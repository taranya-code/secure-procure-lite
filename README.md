# SecureProcure Lite

A lightweight, fully functional **enterprise procurement management** demo application.

**Stack:** Python 3 · Flask · SQLite · SQLAlchemy · Jinja2 · Tailwind CSS (CDN) · Chart.js

---

## What is SecureProcure?

SecureProcure Lite digitises the end-to-end procurement process for an organisation — from an employee raising a purchase request to a vendor being selected and a purchase order issued. It enforces a strict approval chain, maintains a tamper-evident audit log, and uses AI-assisted vendor quote analysis.

For a full step-by-step usage guide see **[RUNBOOK.md](RUNBOOK.md)**.

---

## Quick Start — One Command

### Mac / Linux

```bash
# 1. Get the code
cd /path/to/secure-procure-lite

# 2. Make the script executable (first time only)
chmod +x procure-lite.sh

# 3. Start — installs everything automatically on first run
./procure-lite.sh start
```

The script checks for Python, installs it if missing, creates a virtualenv, installs all packages, initialises the database, seeds demo data, and opens your browser at **http://localhost:5001**.

### Windows

```bat
cd C:\path\to\secure-procure-lite
procure-lite.bat start
```

---

## All Script Commands

### Mac / Linux

| Command | Description |
|---------|-------------|
| `./procure-lite.sh start` | Start the app (auto-installs everything on first run) |
| `./procure-lite.sh stop` | Stop the server |
| `./procure-lite.sh restart` | Stop then start |
| `./procure-lite.sh status` | Show running status and log path |
| `./procure-lite.sh logs` | Show last 50 log lines |
| `./procure-lite.sh install-python` | Install Python 3 via Homebrew (Mac) or apt (Linux) |
| `./procure-lite.sh install-deps` | Create venv and install pip packages |
| `./procure-lite.sh validate` | Run all pre-flight checks and report status |

### Windows

| Command | Description |
|---------|-------------|
| `procure-lite.bat start` | Start the app |
| `procure-lite.bat stop` | Stop the server |
| `procure-lite.bat restart` | Stop then start |
| `procure-lite.bat status` | Show running status |
| `procure-lite.bat logs` | Show last 50 log lines |

---

## What Happens on First Run

```
./procure-lite.sh start
   ↓
1. Checks for Python 3.10+
     └─ not found? → auto-installs via Homebrew (Mac) or apt (Linux)
2. Creates Python virtual environment  (venv/)
3. Installs all pip packages           (Flask, SQLAlchemy, etc.)
4. Creates SQLite database             (data/procure.db)
5. Seeds demo data                     (7 users, 3 vendors, 3 requests, RFQs, audit logs)
6. Starts Flask on port 5001
7. Opens http://localhost:5001 in your browser
```

Subsequent runs skip steps 1–3 if already done.

---

## Manual Installation (if auto-install fails)

### Step 1 — Install Python 3.10+

**Mac:**
```bash
# Option A — Homebrew (recommended)
brew install python

# Option B — installer
# Download from https://www.python.org/downloads/ and run the .pkg
```

**Linux (Ubuntu / Debian):**
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

**Windows:**
1. Download from **https://www.python.org/downloads/**
2. Run the installer
3. **Check "Add Python to PATH"** before clicking Install
4. Open a new Command Prompt and verify: `python --version`

### Step 2 — Install dependencies

```bash
# Mac/Linux
./procure-lite.sh install-deps

# Or manually
```

## Flask CLI and Database Migrations

SecureProcure now includes `manage.py` for Flask CLI and migration support.

```bash
# Use the project virtual environment
./venv/bin/python3 manage.py --help

# Initialize migrations (first time only)
FLASK_APP=manage.py ./venv/bin/python3 -m flask db init

# Create a schema migration
FLASK_APP=manage.py ./venv/bin/python3 -m flask db migrate -m "Add vendor risk fields"

# Apply migrations to the database
FLASK_APP=manage.py ./venv/bin/python3 -m flask db upgrade
```

If you are already using the demo SQLite database and want to keep your current data, run only the migration and upgrade steps.

### Step 3 — Start the app

```bash
./procure-lite.sh start
```

# Or run manually

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3 — Start the app

```bash
./procure-lite.sh start           # Mac/Linux
procure-lite.bat start            # Windows
```

---

## Demo Accounts

All passwords: `password123`

| Email | Name | Role |
|-------|------|------|
| admin@demo.com | Arjun Sharma | Admin |
| officer@demo.com | Priya Nair | Procurement Officer |
| approver@demo.com | Rajesh Iyer | Approver |
| auditor@demo.com | Meera Krishnamurthy | Auditor |
| vendor1@demo.com | Tata Tech Supplies | Vendor |
| vendor2@demo.com | Infosys Procurement | Vendor |
| vendor3@demo.com | Wipro IT Solutions | Vendor |

The login page shows clickable shortcuts for all demo accounts by default.
To hide them: **Admin Panel → Demo Login Panel → toggle off**.

---

## Admin Panel

Go to **Admin Panel** in the sidebar (`/admin/panel`) — Admin role only.

| Control | What it does |
|---------|-------------|
| **Reset & Seed** | Drops all data, recreates schema, seeds fresh demo dataset. Redirects to login. |
| **Clear Data** | Deletes all requests, approvals, RFQs, vendors, logs — **keeps user accounts**. You stay logged in. Use this to demo with your own data. |
| **Demo Login Panel toggle** | Show or hide the demo account shortcuts on the login page. |
| **Demo Password** | Change the password for all 7 demo accounts at once. |

---

## User Management

Go to **Users** in the sidebar (`/admin/users`) — Admin only.

- **Add User** — create any role: Admin, Procurement Officer, Approver, Auditor, or Vendor
- **Edit** — change name, role, department
- **Reset Password** — set a new password for any user
- **Activate / Deactivate** — toggle account access (cannot deactivate yourself)

---

## Light / Dark Theme

Click the **moon / sun button** in the top-right corner.
Your preference is saved in the browser and remembered across sessions.

---

## Procurement Workflow (summary)

```
Officer creates PR (DRAFT)
  → submits for approval (SUBMITTED)
    → Approver approves (APPROVED)
      → Officer issues RFQ to vendors (RFQ_ISSUED)
        → Vendors submit quotes (QUOTED)
          → Officer runs AI analysis
            → Officer selects winning quote (PO_ISSUED)
```

Self-approval is blocked and logged as a fraud alert.
See **[RUNBOOK.md](RUNBOOK.md)** for detailed step-by-step instructions for every role.

---

## Recovery — if you get locked out

If a reset leaves the database empty and you cannot log in:

```bash
# Mac/Linux
curl -X POST http://localhost:5001/api/admin/emergency-seed \
  -H "X-Recovery-Token: demo-recovery-2026"

# Windows (PowerShell)
Invoke-WebRequest -Uri http://localhost:5001/api/admin/emergency-seed `
  -Method POST -Headers @{"X-Recovery-Token"="demo-recovery-2026"}
```

Then log in as `admin@demo.com` / `password123`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python3: command not found` | `./procure-lite.sh install-python` |
| Python not found (Windows) | Reinstall Python — check "Add to PATH" |
| pip install errors | `./procure-lite.sh install-deps` or check internet connection |
| Port 5001 in use | `./procure-lite.sh stop` then `start`, or `lsof -ti:5001 \| xargs kill` |
| Can't log in after reset | Use the emergency-seed curl command above |
| Windows: "Access is denied" | Run Command Prompt as Administrator |
| App starts but shows blank | Check `./procure-lite.sh logs` for Python errors |
| Dark mode text invisible | Restart browser; clear cache |

Run `./procure-lite.sh validate` to diagnose all issues at once.

---

## File Structure

```
secure-procure-lite/
├── procure-lite.sh        Mac/Linux launcher (start/stop/install-python/validate/…)
├── procure-lite.bat       Windows launcher
├── run.py                 Flask entry point
├── requirements.txt       Python dependencies
├── app/
│   ├── __init__.py        App factory + Jinja globals
│   ├── extensions.py      SQLAlchemy + LoginManager + CSRF init
│   ├── models.py          SQLAlchemy models (SQLite)
│   ├── seed.py            Demo data (Indian context, INR)
│   ├── utils.py           audit_log, notify, fmt_currency, status_badge
│   └── routes/
│       ├── auth.py        Login, register, logout
│       ├── dashboard.py   Dashboard KPIs
│       ├── requests.py    Purchase requests CRUD
│       ├── approvals.py   Approval workflow
│       ├── rfq.py         RFQ + quote management
│       ├── vendors.py     Vendor directory
│       ├── audit.py       Audit log viewer
│       ├── reports.py     Spend analytics
│       ├── notifications.py
│       ├── admin.py       User mgmt, admin panel, docs
│       └── api.py         JSON API (notifications, AI analysis, admin ops)
├── templates/
│   ├── base.html          Layout, sidebar, dark/light theme toggle
│   ├── auth/              login.html, register.html
│   └── dashboard/         All page templates
├── data/                  SQLite database (auto-created)
├── README.md              This file
├── RUNBOOK.md             Step-by-step usage guide for all roles
└── DEMO_PLAYBOOK.md       Presenter script for live demos
```
