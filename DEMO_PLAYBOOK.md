# SecureProcure Lite — Demo Playbook

Step-by-step presenter guide for a complete end-to-end procurement lifecycle demo.
**Estimated demo time:** 15–20 minutes

---

## Before You Start

### 1. Start the app
```bash
cd secure-procure-lite
./procure-lite.sh start
```
Open your browser to: **http://localhost:5001**

### 2. Reset + Seed fresh demo data
1. Log in as **admin@demo.com** / `password123`
2. Go to **Admin Panel** (sidebar, bottom of Admin section)
3. Click **"Reset Database"** → confirm → wait for redirect to login
4. Log back in as admin@demo.com / `password123`
5. Go to **Admin Panel** again → click **"Seed Demo Data"**
6. Wait for success message. Page reloads with fresh data.

> The demo dataset includes: 7 users, 3 vendors, 3 purchase requests at different stages, 1 RFQ with 3 quotations (including AI scores), audit logs, and notifications.

---

## Demo Accounts (all password: `password123`)

| Email | Role | Name | What they do |
|-------|------|------|-------------|
| admin@demo.com | Admin | Arjun Sharma | Full access, user management |
| officer@demo.com | Procurement Officer | Priya Nair | Creates purchase requests, issues RFQs, selects vendors |
| approver@demo.com | Approver | Rajesh Iyer | Reviews and approves/rejects requests |
| auditor@demo.com | Auditor | Meera Krishnamurthy | Read-only access to audit logs and reports |
| vendor1@demo.com | Vendor | Tata Tech Supplies (★87.5) | Submits quotes on RFQs |
| vendor2@demo.com | Vendor | Infosys Procurement (★79.0) | Submits quotes on RFQs |
| vendor3@demo.com | Vendor | Wipro IT Solutions (★93.2) | Already submitted winning quote in seed data |

---

## Demo Walkthrough

### ACT 1 — Admin Setup View (2 min)

**Login as: admin@demo.com**

1. **Dashboard** — Show the KPI cards:
   - Total Requests, Total Spend, Pending Approvals, Compliance Score
   - Point out the **Request Pipeline** at the bottom (DRAFT → SUBMITTED → APPROVED → PO ISSUED)
   - Point out the **Spend by Category** breakdown

2. **Admin → Users** — Show all 7 users and their roles.
   > *"Role-based access control. Each user only sees what's relevant to their role."*

3. **Vendors** — Show 3 vendors with reputation scores, on-time delivery percentages.
   > *"Prime IT has the highest score (93.2), already selected for the server upgrade PO."*

4. **Reports** — Show the bar chart (spend by category) and doughnut chart (request status distribution).

---

### ACT 2 — Procurement Officer Creates a New Request (4 min)

**Log out → Login as: officer@demo.com**

1. **Dashboard** — Notice the blue **"+ New Request"** CTA banner. Click it.

2. **Fill out the form:**
   - Title: `Laptop Refresh Programme FY2026`
   - Category: `IT Hardware`
   - Estimated Budget: `2400000` (₹24,00,000)
   - Currency: `INR`
   - Urgency: `HIGH`
   - Description: `Replace 20 ageing laptops across engineering team at Pune office`
   - Line Item: `Dell Latitude 5540` × `20` pcs
   - Click **"+ Add Item"** → add `3-Year On-Site Warranty` × `20` pcs

3. Click **"Create Request"** → lands on the requests list.

4. **Purchase Requests page** — Show the new request in DRAFT status with urgency badge.

5. Click the **"Submit"** button in the actions column.
   > *"One click to submit for the approval workflow."*
   - Status changes from DRAFT → SUBMITTED.

---

### ACT 3 — Approver Reviews and Approves (3 min)

**Log out → Login as: approver@demo.com**

1. **Dashboard** — Show the **Pending Approvals** counter (red badge). The sidebar also shows the badge count next to "Approvals".

2. **Approvals page** — The new request appears in the Pending section with a yellow border.
   - Point out: budget, category, urgency badge, requestor name, "Level 1" indicator.

3. **Self-approval protection** — Explain:
   > *"If the approver had created this request themselves, the approve/reject buttons are hidden and a warning is shown. This prevents self-approval fraud — all blocked attempts are logged."*

4. Add a comment: `Approved — budget confirmed with finance`

5. Click **"✓ Approve"**.

6. Show the **Recent Decisions** table below — the approval is logged there.

7. **Audit Logs** — Click the sidebar link. Show the APPROVAL_DECISION entry in the trail.
   > *"Immutable audit log. Every action is recorded with user, timestamp, and IP."*

---

### ACT 4 — Issue RFQ and Collect Quotes (3 min)

**Log out → Login as: officer@demo.com**

1. **Purchase Requests** — The laptop request is now SUBMITTED/APPROVED.

2. **RFQ & Quotations** — Show the existing RFQ for "Server Infrastructure Upgrade" — this has already gone through the full flow (PO ISSUED).

3. **Issue a new RFQ** — The form at the top shows the approved laptop request:
   - Select: `Laptop Refresh Program 2025`
   - Deadline: pick a date 2 weeks out
   - Invite all 3 vendors (check all checkboxes)
   - Notes: `Include warranty options and bulk pricing. Delivery within 30 days.`
   - Click **"Issue RFQ →"**

4. **Show the RFQ list** — New RFQ appears with status OPEN.

---

### ACT 5 — Vendor Submits a Quote (3 min)

**Log out → Login as: vendor1@demo.com**

1. **Vendor Dashboard** — Show the vendor-specific view:
   - Active RFQs counter (blue)
   - Reputation score banner
   - Performance metrics (on-time delivery bar, reputation bar)

2. **My Quotes** — The open RFQ appears with items listed for reference.

3. Click **"Submit Quote"** to expand the form:
   - Total Amount: `28500`
   - Delivery Days: `21`
   - Quote Valid: `45`
   - Notes: `Includes 3-year warranty. Free delivery.`
   - Fill in line items with unit prices

4. Click **"Submit Quotation"** → quote appears in the submitted quotes table below.

5. Log out → Login as **vendor2@demo.com** → repeat with a different price (e.g. `2180000`, 25 days delivery).

---

### ACT 6 — AI Analysis and PO Issuance (3 min)

**Log out → Login as: officer@demo.com**

1. **RFQ & Quotations** → click **"View →"** on the laptop RFQ.

2. **RFQ Detail page** — Shows both vendor quotes sorted by price. Point out delivery days, validity, notes.

3. Click **"Analyze with AI"** button:
   > *"SecureProcure uses Claude AI to score each quote on price competitiveness, delivery speed, vendor reputation, and terms. If no API key is set, mock scores are applied for demo purposes."*

   - After analysis, each quote shows an AI Score (e.g. 84.2/100) with a color-coded bar and summary text.

4. Select the best quote → Click **"Select & Issue PO"** → confirm.

5. **Result:** RFQ status → CLOSED. Request status → PO_ISSUED. The selected vendor quote shows "✓ SELECTED — PO Issued".

---

### ACT 7 — Auditor View (1 min)

**Log out → Login as: auditor@demo.com**

1. **Audit Logs** — Full immutable trail showing every action taken during the demo.
   - Filter by action "APPROVAL_DECISION" to show just approvals.
   - Switch to **"Fraud Alerts"** tab — shows any self-approval attempts that were blocked.

2. **Reports** — Show the updated charts reflecting the new data.

---

## Key Talking Points

| Feature | What to say |
|---------|-------------|
| Role-Based Access | Each role sees a tailored interface. Vendors can't see internal requests. Auditors are read-only. |
| Self-Approval Prevention | Built-in fraud control. Attempts are blocked and logged permanently. |
| Approval Workflow | Multi-level approval routing. SLA tracking — overdue approvals show on the dashboard. |
| Audit Trail | Every action is logged with user, timestamp, and IP. Tamper-proof. |
| AI Quote Scoring | Claude AI evaluates quotes on price, delivery, vendor reputation, and terms. Removes bias. |
| Vendor Reputation | Scores track on-time delivery, quality history, and order completion over time. |
| Compliance Score | Auto-calculated: % of non-draft requests that went through proper approval before PO issuance. |

---

## Quick Reset Between Demos

If you need to run the demo again for a new audience:
1. Go to **Admin Panel** → **Reset Database** → **Seed Demo Data**
2. Optionally re-run Act 2–6 live, or use the seeded "in-progress" data to jump to any act

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| App not starting | `./procure-lite.sh stop && ./procure-lite.sh start` |
| Login fails after reset | Use Seed Demo Data first — reset wipes all users |
| 500 error | Check terminal for Flask errors. Likely a template or DB issue. |
| AI scores not appearing | Normal without `ANTHROPIC_API_KEY`. Click "Analyze with AI" to apply mock scores. |
| Port already in use | `./procure-lite.sh stop` or `lsof -ti:5001 | xargs kill` |
