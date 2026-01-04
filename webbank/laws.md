Below is a **clear, executive-level but developer-accurate summary** of **(A) the core system laws (rules)** and **(B) how each Django app enforces those laws**.

This document is suitable for:

* onboarding developers
* explaining the system to directors/founders
* guiding audits and refactors
* acting as a “constitution” for the platform

---

# 🏛️ AMOR108 + WEBBANK SACCO

## SYSTEM LAWS & APP RESPONSIBILITY SUMMARY

---

## PART A: CORE SYSTEM LAWS (NON-NEGOTIABLE RULES)

These are **constitutional rules**.
No UI, API, or admin action may bypass them.

---

### LAW 1: SINGLE IDENTITY LAW

> One human = one system user

* A person has **one user account**
* That user may have **multiple SACCO memberships**
* Identity ≠ Membership

**Enforced by:** `accounts`, `membership`

---

### LAW 2: SACCO LAYER LAW

> AMOR108 is the base SACCO, WebBank is an elite SACCO

* AMOR108 = feeder SACCO
* WebBank = restricted, elite SACCO
* All WebBank members must first be AMOR108 members

**Enforced by:** `membership`, `pools`

---

### LAW 3: GOLD POOL ELIGIBILITY LAW

> Only AMOR108 GOLD pool members qualify for WebBank

* Pool level reflects financial muscle
* GOLD pool is the eligibility gate
* Pool downgrade revokes WebBank eligibility

**Enforced by:** `pools`, `membership`

---

### LAW 4: WEBBANK MEMBER CAP LAW

> WebBank has a maximum of 12 active members

* System blocks 13th membership
* Cap applies only to ACTIVE members
* Pending or exited members do not count

**Enforced by:** `membership`

---

### LAW 5: LOAN ACCESS LAW

> Loan access depends on SACCO type

| SACCO   | Who Can Borrow            |
| ------- | ------------------------- |
| AMOR108 | Registered members only   |
| WebBank | Members + Guest borrowers |

**Enforced by:** `loans`, `membership`

---

### LAW 6: GUEST LOAN SPONSORSHIP LAW

> Guest loans must be sponsored by a WebBank member

* Sponsor must be ACTIVE
* Sponsor earns referral interest
* Guest cannot access system directly

**Enforced by:** `loans`, `membership`

---

### LAW 7: SHARE-BASED CREDIT LAW

> Loan limits are determined by shares

* Max loan = shares × multiplier
* Shares may be locked as security
* Locked shares cannot be withdrawn

**Enforced by:** `shares`, `loans`, `guarantors`

---

### LAW 8: GUARANTOR RISK LAW

> Guarantors must fully cover loan risk

* Guarantors must be active members
* Guarantor shares are frozen
* Release only after loan clearance

**Enforced by:** `guarantors`, `loans`, `shares`

---

### LAW 9: MULTI-LEVEL APPROVAL LAW

> Loans require layered approvals

* Directors approve
* Founder gives final approval
* Overrides are logged and auditable

**Enforced by:** `governance`, `loans`, `audit`

---

Continuing from **LAW 10** and then completing **Part B (App Responsibilities)** in a clean, authoritative way.

---

## LAW 10: INTEREST & PROFIT DISTRIBUTION LAW

> Interest belongs to members, not the platform

* Loan interest feeds profit pools
* Profits are distributed proportionally to shares
* Members may:

  * Reinvest
  * Withdraw
  * Allocate to pools

**Enforced by:** `profits`, `shares`, `pools`

---

## LAW 11: AUTOMATED ENFORCEMENT LAW

> Financial rules must execute without human bias

* Interest calculation is automated
* Loan default checks are automated
* Profit distribution is scheduled
* Manual overrides require justification

**Enforced by:** `management/commands`, `audit`

---

## LAW 12: EXIT & CAPITAL PRESERVATION LAW

> Member exits must not destabilize the SACCO

* Exit requests are reviewed
* Shares may be locked during outstanding loans
* Final settlement happens only after clearance

**Enforced by:** `membership`, `shares`, `loans`

---

## LAW 13: TRANSPARENCY LAW

> Every financial action must be traceable

* All actions logged
* No silent changes
* Reports must reconcile with raw data

**Enforced by:** `audit`, `reports`

---

## LAW 14: NOTIFICATION & CONSENT LAW

> Members must be informed of material events

* Loan approvals
* Defaults
* Profit distributions
* Policy changes

**Enforced by:** `notifications`, `messaging`

---

## LAW 15: ROLE SEPARATION LAW

> Power must be separated

| Role     | Power                |
| -------- | -------------------- |
| Member   | Borrow, invest       |
| Director | Approve loans        |
| Founder  | Final veto           |
| Admin    | System configuration |

**Enforced by:** `accounts`, `governance`

---

# PART B: DJANGO APP RESPONSIBILITY MAP

Each app has **one clear purpose**.
Overlap is intentional only where laws require it.

---

## 🔐 `accounts`

**Purpose:** Identity & authentication

**Responsibilities**

* User registration/login
* Role assignment
* Permissions & decorators
* Password management

**Enforces Laws:** 1, 15

---

## 🧾 `membership` *(members + members_amor108)*

**Purpose:** SACCO membership lifecycle

**Responsibilities**

* AMOR108 membership
* WebBank membership
* Status tracking (pending / active / exited)
* Membership caps
* Eligibility checks

**Enforces Laws:** 2, 3, 4, 12

---

## 🏦 `pools`

**Purpose:** Financial muscle classification

**Responsibilities**

* Pool creation
* Pool assignment
* Upgrade/downgrade rules
* Eligibility signals

**Enforces Laws:** 3

---

## 💰 `shares`

**Purpose:** Ownership & credit backing

**Responsibilities**

* Share purchase/sale
* Share locking
* Share valuation
* Credit limits

**Enforces Laws:** 7, 8

---

## 📄 `loans`

**Purpose:** Lending engine

**Responsibilities**

* Member loans
* Guest loans
* Sponsor linkage
* Repayment schedules
* Default detection

**Enforces Laws:** 5, 6, 7, 8, 9

---

## 🛡️ `guarantees`

**Purpose:** Risk backing

**Responsibilities**

* Guarantor assignment
* Risk validation
* Share freezing
* Release on clearance

**Enforces Laws:** 8

---

## 📈 `profits`

**Purpose:** Profit accounting

**Responsibilities**

* Interest aggregation
* Profit calculation
* Distribution
* Reinvestment logic

**Enforces Laws:** 10, 11

---

## 💳 `payments`

**Purpose:** Money movement

**Responsibilities**

* Contribution payments
* Loan repayments
* Profit withdrawals
* Transaction records

**Enforces Laws:** 10, 12

---

## 🧑‍⚖️ `governance`

**Purpose:** Authority & approvals

**Responsibilities**

* Director approvals
* Founder overrides
* Policy enforcement

**Enforces Laws:** 9, 15

---

## 🧪 `audit`

**Purpose:** Immutable history

**Responsibilities**

* Action logging
* Override tracking
* Compliance review

**Enforces Laws:** 9, 11, 13

---

## 📨 `notifications`

**Purpose:** Mandatory disclosures

**Responsibilities**

* System alerts
* Financial notices
* Policy updates

**Enforces Laws:** 14

---

## 💬 `messaging`

**Purpose:** Human communication

**Responsibilities**

* Member-to-member messaging
* Broadcasts
* Loan-related communications

**Supports Laws:** 14

---

## 📊 `reports`

**Purpose:** Oversight & insight

**Responsibilities**

* Financial statements
* Growth metrics
* Risk exposure reports

**Enforces Laws:** 13

---

## 🧭 `admin_panel`

**Purpose:** Controlled power interface

**Responsibilities**

* Configuration panels
* Approval dashboards
* System monitoring

**Enforces Laws:** All (indirectly)

---

