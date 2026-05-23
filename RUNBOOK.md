# SecureProcure Lite — Runbook

**Complete step-by-step guide for every role in the system.**

---

## Table of Contents

1. [What is SecureProcure?](#1-what-is-secureprocure)
2. [Key Concepts & Glossary](#2-key-concepts--glossary)
3. [User Roles](#3-user-roles)
4. [Getting Started — First Login](#4-getting-started--first-login)
5. [Procurement Officer — Full Workflow](#5-procurement-officer--full-workflow)
6. [Approver — Review & Decide](#6-approver--review--decide)
7. [Vendor — Submit a Quote](#7-vendor--submit-a-quote)
8. [Auditor — Review & Compliance](#8-auditor--review--compliance)
9. [Admin — System Management](#9-admin--system-management)
10. [Full Workflow End-to-End](#10-full-workflow-end-to-end)
11. [Request Status Reference](#11-request-status-reference)
12. [Fraud Prevention](#12-fraud-prevention)
13. [Troubleshooting & Recovery](#13-troubleshooting--recovery)

---

## 1. What is SecureProcure?

SecureProcure is an **enterprise procurement management system** designed to bring structure, transparency, and auditability to an organisation's purchasing process.

**Without SecureProcure:** Purchase requests go via email, approvals are informal, vendor selection is undocumented, and there is no audit trail.

**With SecureProcure:**
- Every purchase request follows a defined approval chain
- No one can approve their own request (self-approval is blocked and logged)
- Vendors compete via a formal Request for Quotation (RFQ) process
- AI scores vendor quotes to support objective decision-making
- Every action is recorded in a tamper-evident audit log
- Admins have full visibility and control over users and data

The system is built for Indian organisations — all amounts in INR (₹).

---

## 2. Key Concepts & Glossary

| Term | Meaning |
|------|---------|
| **Purchase Request (PR)** | A formal internal request to procure goods or services. Contains title, category, estimated budget, department, justification, and line items. Must be approved before purchasing can proceed. |
| **RFQ — Request for Quotation** | A document sent to one or more vendors asking them to submit a price quote for the goods/services in an approved PR. |
| **Quotation / Quote** | A vendor's formal response to an RFQ. Contains total amount, delivery timeline (days), validity period, and notes. |
| **Purchase Order (PO)** | Confirmation to the winning vendor that they have been selected. A PR reaches `PO_ISSUED` status when the officer selects the best quote. |
| **AI Analysis** | Automated scoring (0–100) of all quotes on an RFQ using the Claude AI API. Considers price, delivery speed, vendor reputation, and validity. Works in mock mode if no API key is set. |
| **Audit Log** | An immutable record of every significant action in the system — who did what, when, and on which record. |
| **Fraud Alert** | Logged automatically when a user attempts to approve a request they created. The attempt is blocked and recorded as `APPROVAL_SELF_APPROVAL_BLOCKED`. |
| **Compliance Score** | **Dashboard** metric: (Submitted − Rejected) ÷ Submitted × 100. Measures *approval quality* — how many requests passed through without rejection. High = well-justified requests. Click the ⓘ button on the card to see the formula. |
| **PO Completion Rate** | **Reports** metric: PO_ISSUED requests ÷ Total requests × 100. Measures *procurement completion* — how many requests made it all the way to a Purchase Order. Different from Compliance Score by design. Click the ⓘ button on the card to see the formula. |
| **SLA Breach / Overdue** | An approval flagged as overdue when it has been waiting more than 3 days without a decision. |

---

## 3. User Roles

| Role | What they can do |
|------|-----------------|
| **Admin** | Everything. Manages users, resets data, accesses all pages, can act as Officer and Approver. |
| **Procurement Officer** | Creates and manages Purchase Requests. Issues RFQs. Runs AI analysis. Selects winning vendor. Cannot approve own requests. |
| **Approver** | Reviews submitted PRs and approves or rejects them. Cannot approve requests they created. |
| **Auditor** | Read-only access. Views all PRs, RFQs, audit logs, reports. Cannot create or modify anything. |
| **Vendor** | Receives RFQs. Submits quotations. Can only see their own quotes. |

---

## 4. Getting Started — First Login

1. Open **http://localhost:5001** in your browser
2. The login page shows demo account shortcuts — click any email to auto-fill credentials
3. Default password for all demo accounts: `password123`
4. Click **Sign In**

**Recommended first login:** `admin@demo.com` to explore all features.

### Register a New Account

1. Click **Register** on the login page
2. Fill in: Full Name, Email, Password (min 8 chars), Role, Department (optional)
3. If registering as a Vendor, enter your Company Name
4. Click **Create Account** — you are logged in immediately
5. Press **Escape** or click **← Cancel** to go back to login without registering

> **Note:** Self-registered users cannot have the Admin role. Admins must be created by another Admin via the Users page.

---

## 5. Procurement Officer — Full Workflow

### Step 1 — Create a Purchase Request

1. Log in as a Procurement Officer (or Admin)
2. Click **Purchase Requests** in the sidebar
3. Click **+ New Request**
4. Fill in the form:
   - **Title** — clear description of what you need (e.g. "Data Centre Server Upgrade")
   - **Category** — IT Hardware / Office Equipment / Infrastructure / Cloud Services / Other
   - **Estimated Budget** — amount in ₹
   - **Currency** — defaults to INR
   - **Urgency** — LOW / NORMAL / HIGH / CRITICAL
   - **Department** — your department name
   - **Justification** — business reason for the purchase
   - **Required By** — target delivery date (optional)
5. Add **Line Items** — click "+ Add Item", enter item name, quantity, unit price
6. Click **Save as Draft**

The request is now in **DRAFT** status. You can edit or delete it.

### Step 2 — Submit for Approval

1. Open the draft request (click its title in the list)
2. Review all details and line items
3. Click **Submit for Approval**
4. Status changes to **SUBMITTED**
5. All Approvers receive a notification

> You cannot edit the request after submission. If changes are needed, ask an Admin to reject it so you can revise.

### Step 3 — Wait for Approval

- Check the **Notifications** page (bell icon) for approval decisions
- If **rejected**: the request returns with a rejection reason. Review the feedback, then create a new revised request.
- If **approved**: proceed to Step 4

### Step 4 — Issue an RFQ

1. Open the approved request
2. Click **Issue RFQ**
3. Fill in:
   - **Response Deadline** — date by which vendors must submit quotes
   - **Instructions** — any special requirements or terms
4. Select **which vendors** to invite (tick the checkboxes)
5. Click **Send RFQ**
6. Status changes to **RFQ_ISSUED**
7. Selected vendors receive a notification

### Step 5 — Monitor Incoming Quotes

1. Go to **RFQ & Quotations** in the sidebar
2. Find your RFQ and open it
3. The **Quotations** section shows all submitted vendor quotes
4. Status changes to **QUOTED** once at least one quote is received

### Step 6 — Run AI Analysis

1. On the RFQ detail page, click **Analyse Quotes**
2. The system scores each quote 0–100 based on:
   - Price competitiveness
   - Delivery speed (days)
   - Vendor reputation score
   - Validity period
3. Each quote shows an AI score and a 2-sentence justification
4. If no Anthropic API key is configured, mock scores are applied automatically

### Step 7 — Select the Winning Vendor

1. Review the AI scores and summaries
2. Click **Select** next to the best quote
3. Confirm the selection
4. Status changes to **PO_ISSUED**
5. The winning vendor receives a notification
6. The full audit trail is complete

---

## 6. Approver — Review & Decide

### View Pending Approvals

1. Log in as Approver (or Admin)
2. Click **Approvals** in the sidebar
3. The sidebar badge shows the count of pending approvals
4. Each pending item shows: title, budget, category, creator, urgency, justification, and line items

### Approve a Request

1. Read the request details carefully
2. Add an optional comment in the text box
3. Click **✓ Approve**
4. Status changes to **APPROVED**
5. The Procurement Officer is notified

### Reject a Request

1. Add a comment explaining why (recommended — helps the officer revise)
2. Click **✕ Reject**
3. Status changes to **REJECTED**
4. The Procurement Officer is notified with your comment

### Self-Approval Block

If you created the request yourself:
- The approve/reject buttons are hidden
- A warning banner reads: "You created this request — self-approval is not allowed"
- Any programmatic attempt is blocked and logged as a fraud alert

### Recent Decisions

The lower section of the Approvals page shows all past decisions — useful for reference and disputes.

---

## 7. Vendor — Submit a Quote

### View Assigned RFQs

1. Log in as a Vendor
2. Click **My Quotes** in the sidebar
3. You see all RFQs you have been invited to respond to
4. Each RFQ shows the request title, deadline, and required items

### Submit a Quotation

1. Click on an RFQ to open it
2. Click **Submit Quote**
3. Fill in:
   - **Total Amount (₹)** — your quoted price for the full requirement
   - **Delivery Days** — number of days from PO to delivery
   - **Validity Days** — how many days your quote is valid
   - **Notes** — any terms, conditions, or clarifications
4. Add **line-item breakdown** if needed
5. Click **Submit Quotation**

> You can only see your own quote — not other vendors' quotes.

### After Submission

- Your quote appears in the "My Quotes" list with status **SUBMITTED**
- If selected as the winner, you receive a notification and your quote shows **SELECTED**
- The officer uses your quote details to issue the Purchase Order

---

## 8. Auditor — Review & Compliance

Auditors have **read-only** access to all data. They cannot create, edit, or approve anything.

### Audit Logs

1. Click **Audit Logs** in the sidebar
2. Every system action is recorded: request creation, submission, approval decisions, RFQ issuance, quote submission, AI analysis, PO issuance, fraud alerts, user logins
3. Filter by:
   - **Action type** — e.g. APPROVAL_DECISION, CREATE, FRAUD_ALERT
   - **Entity type** — PURCHASE_REQUEST, RFQ, USER, etc.
   - **Date range**
4. Each log entry shows: timestamp, actor, action, entity type, entity ID, and additional details

### Fraud Alerts

- Filter Audit Logs by action `APPROVAL_SELF_APPROVAL_BLOCKED`
- Each entry shows who attempted self-approval, on which request, and when
- These cannot be deleted — they are permanent records

### Purchase Requests

- Click **Purchase Requests** to view all PRs across all officers
- Click any request to see full details, line items, approval history, and associated RFQs

### Reports

- Click **Reports** for spend analytics:
  - Spend by category (bar chart)
  - Spend by vendor
  - Monthly spend trend
  - Compliance score over time
  - Top vendors by quote win rate

---

## 9. Admin — System Management

### User Management

1. Click **Users** in the sidebar
2. The table shows all users with role, department, and active status

**Add a user:**
1. Click **+ Add User**
2. Fill in name, email, password, role, department
3. Click **Create User**

**Edit a user:**
1. Click the pencil icon (✏) next to a user
2. Change name, role, or department
3. Click **Save Changes**
4. Note: you cannot change your own role

**Reset a user's password:**
1. Click the key icon (🔑) next to a user
2. Enter the new password (min 6 chars)
3. Click **Reset Password**

**Activate / Deactivate:**
1. Click the play/pause icon next to a user
2. Deactivated users cannot log in
3. You cannot deactivate your own account

### Admin Panel

Go to **Admin Panel** in the sidebar.

**Reset & Seed:**
- Drops all tables, recreates schema, seeds full demo data
- Use when you want a completely clean demo state
- Redirects to login (your session is cleared)
- After login: all demo data is ready — 7 users, 3 vendors, 3 requests, RFQs, audit logs

**Clear Data:**
- Deletes all requests, approvals, RFQs, vendors, audit logs, notifications
- **Keeps all user accounts** — you stay logged in
- Use this when you want to demo the workflow from scratch with your own data

**Demo Login Panel toggle:**
- Controls whether the demo account shortcuts appear on the login page
- Toggle ON for demos, OFF for production-like presentations

**Demo Password:**
- Changes the password for all 7 demo accounts at once
- Useful when sharing a demo instance with an audience

### Docs Page

Go to **Docs** in the sidebar for an in-app reference guide (same content as this runbook, formatted for the browser). Use the **Print / Save as PDF** button to generate a printable handout.

---

## 10. Full Workflow End-to-End

Here is the complete flow from start to finish, showing which role acts at each step:

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1 — Officer creates Purchase Request                      │
│  Role: Procurement Officer / Admin                              │
│  Status: DRAFT                                                  │
│  Action: Fill form → Save as Draft                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  STEP 2 — Officer submits for approval                          │
│  Role: Procurement Officer / Admin                              │
│  Status: SUBMITTED                                              │
│  Action: Open draft → Submit for Approval                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  STEP 3 — Approver reviews and decides                          │
│  Role: Approver / Admin (NOT the request creator)               │
│  Status: APPROVED or REJECTED                                   │
│  Action: Approvals page → Add comment → Approve / Reject        │
│  Note: Self-approval is blocked and logged as fraud alert       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ (if APPROVED)
┌──────────────────────────▼──────────────────────────────────────┐
│  STEP 4 — Officer issues RFQ to vendors                         │
│  Role: Procurement Officer / Admin                              │
│  Status: RFQ_ISSUED                                             │
│  Action: Open approved PR → Issue RFQ → Select vendors → Send   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  STEP 5 — Vendors submit quotations                             │
│  Role: Vendor                                                   │
│  Status: QUOTED (when first quote received)                     │
│  Action: My Quotes → Open RFQ → Submit Quote                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  STEP 6 — Officer runs AI analysis                              │
│  Role: Procurement Officer / Admin                              │
│  Action: RFQ detail page → Analyse Quotes                       │
│  Result: Each quote scored 0–100 with justification             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│  STEP 7 — Officer selects winner and issues PO                  │
│  Role: Procurement Officer / Admin                              │
│  Status: PO_ISSUED                                              │
│  Action: RFQ detail → Select best quote → Confirm               │
│  Result: Vendor notified, audit trail complete                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Request Status Reference

| Status | Meaning | Next action |
|--------|---------|-------------|
| **DRAFT** | Created, not yet submitted | Officer submits for approval |
| **SUBMITTED** | Awaiting approval decision | Approver reviews |
| **UNDER_REVIEW** | Approver has opened it | Approver approves or rejects |
| **APPROVED** | Approved — ready for RFQ | Officer issues RFQ |
| **REJECTED** | Rejected — needs revision | Officer creates revised request |
| **RFQ_ISSUED** | RFQ sent to vendors | Vendors submit quotes |
| **QUOTED** | At least one quote received | Officer analyses and selects |
| **PO_ISSUED** | Vendor selected, PO issued | Process complete |

---

## 12. Fraud Prevention

SecureProcure has built-in controls to prevent procurement fraud:

### Self-Approval Block
- A user **cannot approve a request they created**
- Enforced server-side — not just hidden in the UI
- Every bypass attempt is permanently recorded in the audit log as `APPROVAL_SELF_APPROVAL_BLOCKED`
- Visible to all Auditors and Admins

### Audit Trail
- Every action is logged with: timestamp, user, action type, entity, and details
- Logs cannot be edited or deleted through the UI
- Accessible to Auditors and Admins at all times

### Role Separation
- Vendors can only see their own quotes
- Auditors are read-only
- Officers cannot approve
- The combination prevents any single role from completing the full cycle alone

### Dashboard Alerts
- Fraud alert count shown on the dashboard
- Overdue approvals (SLA > 3 days) flagged with a warning banner

---

## 13. Troubleshooting & Recovery

### Can't log in after a Reset & Seed

The Reset operation clears your session. Log back in with `admin@demo.com` / `password123`.

If the database is empty and the login fails entirely, run the emergency seed from a terminal:

```bash
# Mac/Linux
curl -X POST http://localhost:5001/api/admin/emergency-seed \
  -H "X-Recovery-Token: demo-recovery-2026"

# Windows PowerShell
Invoke-WebRequest -Uri http://localhost:5001/api/admin/emergency-seed `
  -Method POST -Headers @{"X-Recovery-Token"="demo-recovery-2026"}
```

Then log in as `admin@demo.com` / `password123`.

### Run pre-flight diagnostics

```bash
./procure-lite.sh validate
```

This checks Python version, virtualenv, pip packages, database connectivity, and port availability — and tells you exactly how to fix each issue.

### Python not found

```bash
./procure-lite.sh install-python
```

Or manually:
- **Mac:** `brew install python`
- **Linux:** `sudo apt install python3 python3-venv python3-pip`
- **Windows:** Download from https://www.python.org/downloads/ — check "Add to PATH"

### Packages missing / pip errors

```bash
./procure-lite.sh install-deps
```

### Port 5001 already in use

```bash
./procure-lite.sh stop
# If that doesn't help:
lsof -ti:5001 | xargs kill    # Mac/Linux
# Then:
./procure-lite.sh start
```

### App crashes on start

```bash
./procure-lite.sh logs
```

Look for Python tracebacks. Common causes: missing package (run `install-deps`), database corruption (run Reset & Seed from Admin Panel or emergency-seed from terminal).

### Common error messages

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'flask'` | venv not activated or packages not installed | `./procure-lite.sh install-deps` |
| `Address already in use` | Another process on port 5001 | `./procure-lite.sh stop` then `start` |
| `OperationalError: no such table` | Database not initialised | `./procure-lite.sh restart` |
| `CSRF token missing` | Form submitted without CSRF token | Reload the page and try again |
| `Invalid email or password` | Wrong credentials or deactivated account | Check email/password; Admin can reset via Users page |
| `Self-approval not allowed` | Trying to approve your own request | Ask another Approver or Admin to approve it |

---

*For a shorter quick-reference see [README.md](README.md). For a scripted live demo guide see [DEMO_PLAYBOOK.md](DEMO_PLAYBOOK.md).*
