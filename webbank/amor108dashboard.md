Below is a **deep, implementation-level breakdown** of the **AMOR108 dashboard**, designed to fit **your current codebase**, the **laws you defined**, and the **refactored architecture** we agreed on.

This is how a **production SACCO dashboard** should be built — not just pages, but **enforced financial logic**.

---

# 🔷 AMOR108 DASHBOARD — PURPOSE

The AMOR108 dashboard is **NOT just UI**.
It is a **member financial cockpit** for:

* Pool participation
* Contributions & shares
* Loan visibility (NOT approval)
* Guarantees
* Profits & reinvestment
* Voting & governance
* Transparency & audit access

⚠️ **Critical rule**

> AMOR108 members **cannot bypass** AMOR108 rules even if they later qualify for WebBank.

---

# 🧠 DASHBOARD ARCHITECTURE

```
Dashboard (UI)
   ↓
Dashboard View Layer (Read-only orchestration)
   ↓
Domain Services (membership / shares / loans / profits)
   ↓
Database (Models)
```

👉 **Dashboard NEVER mutates business rules directly**

---

# 📁 APP RESPONSIBILITY

| Component       | Responsibility                  |
| --------------- | ------------------------------- |
| `dashboard`     | Layout, routing, widgets        |
| `membership`    | Member status, pool eligibility |
| `shares`        | Ownership & credit              |
| `contributions` | Monthly deposits                |
| `loans`         | Loan read-only view             |
| `guarantees`    | Guarantor exposure              |
| `profits`       | Profit & dividend view          |
| `governance`    | Voting & resolutions            |
| `audit`         | Transparency                    |

---

# 🧩 DASHBOARD SECTIONS (MODULE BY MODULE)

## 1️⃣ Dashboard Home (`/amor108/dashboard/`)

### Data Displayed

* Member status (Active / Pending / Suspended)
* Pool type (Bronze / Silver / Gold)
* Total shares
* Total contributions
* Active loans (summary)
* Guarantees exposure
* Profit balance

### Service Calls

```python
MembershipService.get_member_status(user)
ShareService.get_share_summary(member)
LoanService.get_loan_summary(member)
ProfitService.get_profit_summary(member)
```

### Rules Enforced

* Pending members see **limited widgets**
* Suspended members see **read-only dashboard**

---

## 2️⃣ Pools Dashboard (`dashboard_pools.html`)

### Features

* List of all pools
* Current pool participation
* Pool contribution rules
* Pool upgrade eligibility

### Business Logic

```python
PoolService.can_upgrade(member)
PoolService.get_next_pool_requirements(member)
```

### UI States

* Locked pools (grayed out)
* Upgrade CTA (if eligible)
* Admin notices (rule changes)

---

## 3️⃣ Contributions Dashboard

### Features

* Contribution history
* Monthly minimum enforcement
* Missed contribution alerts
* STK Push initiation

### Rules

* Missed contribution → penalty or downgrade
* Cannot withdraw contributions freely

```python
ContributionService.get_contribution_timeline(member)
ContributionService.can_contribute(member)
```

---

## 4️⃣ Shares Dashboard

### Features

* Shares owned
* Share value
* Credit power indicator
* Share purchase CTA

### Laws

* Shares secure loans
* Shares cannot be withdrawn if:

  * Active loan
  * Active guarantee

```python
ShareService.get_credit_power(member)
ShareService.is_locked(member)
```

---

## 5️⃣ Loans Dashboard (Read-Only)

### Features

* Active loans
* Repayment schedule
* Remaining balance
* Loan status

⚠️ **No approvals here**

```python
LoanService.get_member_loans(member)
LoanService.get_repayment_schedule(loan)
```

---

## 6️⃣ Guarantees Dashboard

### Features

* Loans guaranteed
* Amount at risk
* Pending requests
* Accept / reject guarantees

### Enforcement

* Guarantee locks shares
* Over-guaranteeing blocked

```python
GuaranteeService.get_guarantee_exposure(member)
GuaranteeService.can_accept(member, loan)
```

---

## 7️⃣ Profits & Reinvestment Dashboard

### Features

* Accrued profits
* Distribution history
* Reinvestment options
* Withdrawal (if allowed)

### Laws

* Reinvestment preferred
* Withdrawals may require approval

```python
ProfitService.get_profit_balance(member)
ProfitService.can_withdraw(member)
```

---

## 8️⃣ Governance & Voting

### Features

* Active votes
* Voting history
* Resolutions
* Governance documents

### Rules

* Voting power tied to shares
* Some votes limited to Gold pool

```python
GovernanceService.get_active_votes(member)
GovernanceService.get_voting_weight(member)
```

---

## 9️⃣ Transparency & Audit

### Features

* Financial statements
* Pool performance
* Admin decisions
* Audit logs

### Rule

> If members can’t see it, trust dies.

```python
AuditService.get_member_visible_logs(member)
```

---

## 10️⃣ Notifications Panel

### Features

* Loan alerts
* Contribution reminders
* Governance notices
* System warnings

```python
NotificationService.get_unread(member)
```

---

# 🔐 ACCESS CONTROL MATRIX

| Section             | Bronze     | Silver | Gold |
| ------------------- | ---------- | ------ | ---- |
| Contributions       | ✅          | ✅      | ✅    |
| Shares              | ⚠️ Limited | ✅      | ✅    |
| Loans               | ❌          | ⚠️     | ✅    |
| Guarantees          | ❌          | ⚠️     | ✅    |
| Voting              | ❌          | ⚠️     | ✅    |
| WebBank Eligibility | ❌          | ❌      | ✅    |

---

# 🧪 TEMPLATE STRUCTURE (GOOD PRACTICE)

```
amor108/
├── dashboard_base.html
├── dashboard.html
├── dashboard_contributions.html
├── dashboard_shares.html
├── dashboard_loans.html
├── dashboard_guarantees.html
├── dashboard_profits.html
├── dashboard_pools.html
├── dashboard_voting.html
├── dashboard_transparency.html
└── partials/
    ├── _summary_cards.html
    ├── _alerts.html
    └── _quick_actions.html
```

---

# ⚠️ COMMON MISTAKES TO AVOID

❌ Business logic in templates
❌ Loan approval buttons in AMOR108
❌ Direct DB writes from dashboard views
❌ Mixing WebBank logic into AMOR108 UI

---

#