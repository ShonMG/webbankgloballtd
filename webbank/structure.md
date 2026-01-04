Below is a **complete, exhaustive list of EVERY app** in the **merged AMOR108 + WEBBANK SACCO platform**, with **detailed features, responsibilities, business rules, and cross-app interactions**.

This is written as a **master implementation checklist** for developers and system architects.
Nothing is abstract — everything maps directly to code.

---

# 🏦 AMOR108 + WEBBANK

## FULL DJANGO APP LIST & DETAILED FEATURES

---

## 1. CORE APP (`core`)

**System-wide rules & shared utilities**

### Features

* Global constants (statuses, enums, rates)
* Financial validators (loan limits, share rules)
* Custom permissions & decorators
* Soft-delete & timestamp mixins
* System signals (audit triggers)
* Feature flags (enable/disable modules)

### Business Rules

* No financial record can be deleted
* All state transitions logged
* Shared rules override local ones

---

## 2. ACCOUNTS APP (`accounts`)

**Identity, authentication & RBAC**

### Features

* Custom User model (email + phone login)
* Role management (Admin, Founder, Director, Manager, Member)
* Two-factor authentication (2FA)
* Account lockout on failed attempts
* Password reset & recovery
* Role assignment workflows

### Business Rules

* Only Root Admin creates Directors & Managers
* Role escalation requires audit log
* Non-members cannot log in

---

## 3. MEMBERS APP (`members`)

**Unified member profile & KYC**

### Features

* Member personal details
* KYC verification workflow
* Next-of-kin management
* Referral & referee tracking
* Member status lifecycle
* Eligibility checks (AMOR108 vs WebBank)

### Business Rules

* KYC required for loans
* One profile per user
* Status controls system access

---

## 4. PAYMENTS APP (`payments`)

**All money movement (single source of truth)**

### Features

* M-Pesa STK Push
* Paybill reconciliation
* Transaction ledger
* Refund handling
* Payment routing engine
* Failed payment queue

### Business Rules

* Immutable transactions
* Auto-matching rules enforced
* No manual balance edits

---

## 5. RISK APP (`risk`)

**Credit scoring & exposure control**

### Features

* Automated credit scoring
* Default risk flags
* Loan exposure calculations
* Blacklisting logic
* Director override tracking

### Business Rules

* Risk score caps loan amount
* Overrides logged & audited
* Repeat defaulters restricted

---

## 6. NOTIFICATIONS APP (`notifications`)

**All communication channels**

### Features

* SMS notifications
* Email alerts
* In-app notifications
* WhatsApp integration (optional)
* Notification templates
* Delivery tracking

### Business Rules

* Financial alerts are mandatory
* Failed delivery retried
* Admin alerts are high-priority

---

## 7. REPORTS APP (`reports`)

**Transparency & analytics**

### Features

* Member statements (PDF/Excel)
* Loan performance reports
* Pool performance reports
* Dividend summaries
* Director activity logs
* Export engine

### Business Rules

* Reports are read-only
* Financial reports immutable once generated

---

## 8. AUDIT APP (`audit`)

**Compliance & accountability**

### Features

* Immutable audit logs
* Approval trails
* Before/after snapshots
* Actor attribution
* Time-stamped records

### Business Rules

* No delete/update
* All financial actions logged
* Admin-only access

---

# 🔵 AMOR108 LAYER (FEEDER SACCO)

---

## 9. AMOR108 POOLS APP (`amor108.pools`)

**Investment pool definitions**

### Features

* Fixed pool tiers
* Contribution schedules
* Auto-locking pools
* Pool manager assignment
* Pool lifecycle management

### Business Rules

* One member per pool
* Pool locks when full
* Manager assigned by admin

---

## 10. AMOR108 MEMBERSHIPS APP (`amor108.memberships`)

**AMOR108 membership lifecycle**

### Features

* Pool enrollment
* Pool exit workflow
* Suspension handling
* Share accumulation tracking
* Gold pool eligibility marker

### Business Rules

* Exit requires notice & clearance
* Suspension freezes benefits
* Gold pool unlocks WebBank access

---

## 11. AMOR108 CONTRIBUTIONS APP (`amor108.contributions`)

**Savings & share growth engine**

### Features

* Daily/monthly contributions
* Automatic schedules
* Late/missed tracking
* Share conversion logic
* Contribution analytics

### Business Rules

* Strict amount validation
* Late contributions penalized
* Affects loan eligibility

---

## 12. AMOR108 LOANS APP (`amor108.loans`)

**Pool-based lending**

### Features

* Member loans (1%)
* Emergency loans (10%)
* Sponsored non-member loans (20%)
* Loan approval workflow
* Repayment schedules

### Business Rules

* Members only
* Pool liquidity enforced
* Sponsored loans tracked separately

---

## 13. AMOR108 PROFITS APP (`amor108.profits`)

**Interest pooling & distribution**

### Features

* Interest accumulation
* Profit periods
* Share-based distribution
* Reinvestment logic
* Withdrawal scheduling

### Business Rules

* Distribution proportional to shares
* Withdrawals time-restricted

---

## 14. AMOR108 INVESTMENTS APP (`amor108.investments`)

**External investments**

### Features

* Investment proposals
* Approval workflows
* Return tracking
* Profit injection to pool

### Business Rules

* Large investments require voting
* Returns go to profit pool

---

## 15. AMOR108 GOVERNANCE APP (`amor108.governance`)

**Voting & policy changes**

### Features

* Proposal creation
* Weighted voting
* Voting deadlines
* Outcome enforcement

### Business Rules

* Vote weight tied to shares
* Immutable voting records

---

# 🟣 WEBBANK LAYER (ELITE SACCO)

---

## 16. WEBBANK MEMBERSHIPS APP (`webbank.memberships`)

**Elite SACCO membership**

### Features

* Gold-pool gate validation
* Seat limits enforcement
* Director assignment
* Membership suspension
* WebBank exit workflow

### Business Rules

* AMOR108 Gold required
* Membership cap enforced
* Director approval required

---

## 17. WEBBANK SHARES APP (`webbank.shares`)

**Formal share management**

### Features

* Share purchases via STK
* Share freezing
* Share withdrawals
* Share valuation engine
* Share audit trails

### Business Rules

* Cannot withdraw secured shares
* Minimum holding enforced

---

## 18. WEBBANK GUARANTORS APP (`webbank.guarantors`)

**Loan security system**

### Features

* Guarantor requests
* Acceptance workflow
* Share locking
* Release logic
* Risk coverage validation

### Business Rules

* Guarantors must be active members
* Shares frozen until release

---

## 19. WEBBANK LOANS APP (`webbank.loans`)

**Share & guarantor-backed loans**

### Features

* Loan application workflow
* Director approvals
* Founder final approval
* STK disbursement
* Advanced repayment tracking

### Business Rules

* Shares × multiplier limit
* Guarantor coverage enforced
* Multi-level approval mandatory

---

## 20. WEBBANK DIVIDENDS APP (`webbank.dividends`)

**Dividend calculation & payouts**

### Features

* Interest split engine
* Dividend pool management
* Real-time dividend updates
* Payout scheduling
* Reinvestment option

### Business Rules

* Split rules enforced
* Auto-recalculation on share changes

---

## 21. WEBBANK DIRECTORS APP (`webbank.directors`)

**Governance hierarchy**

### Features

* Director-member mapping
* Performance dashboards
* Loan oversight
* Approval tracking
* Member onboarding validation

### Business Rules

* Directors limited to assigned members
* Overrides logged

---

# 🧠 FINAL SUMMARY

**Total Django Apps: 21**

* Core/Shared: **8**
* AMOR108: **7**
* WebBank: **6**

---

## ✅ SYSTEM GUARANTEES

✔ No rule overlap or conflict
✔ Strict financial discipline
✔ Clear audit trails
✔ Scalable into mobile/web apps
✔ Regulator-ready architecture

---


