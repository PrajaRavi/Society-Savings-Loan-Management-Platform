# Society Savings & Loan Management Platform
# Complete Project Context & Architecture Master Guide (CONTEXT.md)

> **To Any AI Agent or Software Engineer Reading This File:**  
> This file is the single, authoritative source of truth for the entire **Society Savings & Loan Management Platform**. Read this document first before writing code, proposing changes, or running commands. It contains the business domain, core non-negotiable rules, real-world analogies, database schema, background queue system, auth design, and the exact 12-feature roadmap.

---

## 1. Executive Summary & Problem Domain

### What is this product?
A multi-tenant Software-as-a-Service (SaaS) web platform designed for community-based savings and lending groups (known globally as *Chamas*, *Bishis*, *Chit Funds*, *SACCOs*, or *Mutual Aid Societies*).

### What does it do?
1. Allows groups to create independent digital societies.
2. Lets societies invite members into defined committee roles (President, Vice President, Secretary, Treasurer, Member).
3. Collects recurring monthly member contributions into a transparent, auditable society pool.
4. Lends money from that pooled fund to eligible members governed by a strict, fair, first-in-first-out (FIFO) queue.
5. Tracks loan disbursements, repayments, interest accruals, and overdue arrears.
6. Maintains a tamper-proof double-entry accounting ledger where every single rupee/cent can be explained and verified.

---

## 2. Real-World Analogies for Core Concepts

To understand why the architecture is designed this way, keep these real-world analogies in mind:

| Concept | Real-World Analogy | Explanation |
|---|---|---|
| **Multi-Tenancy** | **National Passport vs. Club Badges** | You carry one national passport (your platform account), but you can hold a badge as President of the Chess Club (Society A) and an ordinary badge as a gym member (Society B). Actions in Society A have zero authority in Society B. |
| **Financial Separation** | **Hall Rent vs. Community Lockbox** | The SaaS platform fee is like rent paid to the landlord of the hall. The monthly society contribution is cash put directly into the community lockbox. **They must never mix.** SaaS fees never enter the society's loanable fund. |
| **Double-Entry Ledger** | **Permanent Ink Cashbook** | Balances are never typed in pencil or edited directly. Every change is an immutable entry with equal debits and credits: money came from somewhere, and went somewhere. |
| **Fair Loan Queue (FIFO)** | **Bank Counter Numbered Tokens** | Person #1 with Token #1 asks for ₹50,000. Person #2 with Token #2 asks for ₹20,000. If the drawer only has ₹30,000, **the teller waits for more funds to pay Person #1 first.** The system NEVER skips Person #1 just because Person #2 asked for less money. |
| **Background Tasks** | **Restaurant Waiter & Kitchen Order Rail** | FastAPI is the waiter (acknowledges payments and returns HTTP responses in 50ms). Redis is the rotating ticket rail. Celery workers are the kitchen cooks in the back running heavy calculations, generating bills, and checking queues without freezing the front counter. |
| **Read-Heavy Indexing** | **Library Catalog Search Tabs** | Instead of scanning 100,000 database rows one by one when users check balances, composite B-tree indexes act as instant index tabs, returning results in under 2 milliseconds. No migration chains needed—all live in one clean `schema.sql`. |
| **Dummy Auth System** | **Movie Set Actor Badges** | During local development, click a floating badge to wear the "President", "Treasurer", or "Member" badge. Test full RBAC workflows in 1 second without needing Google OAuth credentials or SMS OTPs. |

---

## 3. Non-Negotiable Business Rules & Architectural Laws

1. **Integer Minor Currency Units Only:**
   - Float/decimal arithmetic is strictly prohibited for monetary amounts.
   - All amounts are stored as integers (`BIGINT`) in the smallest currency unit (e.g., paise for INR, cents for USD). `₹100.50` is stored as `10050`.
2. **Ledger-Derived Balances:**
   - Society available cash is **never an editable column**. It is computed dynamically from posted ledger entries:
     $$\text{Available Loanable Cash} = \text{Total Cash} - \text{Reserved Funds} - \text{Restricted Payables}$$
3. **Deterministic FIFO Loan Queue:**
   - Loan ordering is strictly: `ORDER BY eligibility_at ASC, fifo_sequence ASC`.
   - When new funds clear or reservations expire, allocation logic runs under an explicit PostgreSQL advisory transaction lock: `SELECT pg_advisory_xact_lock(society_id)`.
   - **Strict All-or-Nothing Rule:** If the earliest approved loan cannot be fully funded, allocation halts. Smaller subsequent requests are not allowed to skip ahead unless the first applicant explicitly consented to partial funding.
4. **Invitation-Only Membership:**
   - Users cannot self-register directly into a society. They must be invited by an authorized committee member.
   - Invitations use a single-use, time-expiring cryptographic token hash (`SHA-256`).
5. **Waterfall Repayment Allocation:**
   - Borrower repayments settle liabilities in strict order:
     $$\text{Repayment} \longrightarrow \text{Late Fees / Penalties} \longrightarrow \text{Accrued Interest} \longrightarrow \text{Principal Reduction}$$
6. **Separation of Duties (Maker-Checker):**
   - High-risk actions (disbursing loans, recording manual cash entries, waiving late fees) require recorded approval and audit logs. The person recording a disbursement cannot be the sole approver.

---

## 4. Full Technology Stack & Locked Versions

### Frontend (SPA)
- **Framework:** React `18.3.1` (Vite `^5.4.11`)
- **Language:** TypeScript `^5.6.3`
- **Styling:** Tailwind CSS `^3.4.15` + `@tailwindcss/forms`
- **Routing:** `react-router-dom` `^6.28.0`
- **Data Fetching & Cache:** `@tanstack/react-query` `^5.60.5`
- **Forms & Validation:** `react-hook-form` `^7.53.2` + `zod` `^3.23.8` + `@hookform/resolvers` `^3.9.1`
- **HTTP Client:** `axios` `^1.7.7`
- **Icons & UI Helpers:** `lucide-react` `^0.460.0`, `clsx`, `tailwind-merge`

### Backend (REST API)
- **Framework:** FastAPI `0.115.5`
- **Python Runtime:** Python `3.12`
- **ASGI Server:** Uvicorn `0.32.1`
- **Validation & Settings:** Pydantic `2.10.2`, Pydantic Settings `2.6.1`
- **ORM:** SQLAlchemy `2.0.36` (modern async 2.0 syntax)
- **Postgres Async Driver:** `asyncpg` `0.30.0`
- **Security:** `python-jose[cryptography]` `3.3.0`, `passlib[bcrypt]` `1.7.4`
- **Testing:** `pytest` `8.3.3`, `pytest-asyncio` `0.24.0`, `httpx` `0.28.0`

### Database & Storage Layer
- **Platform:** Supabase (PostgreSQL 15+)
- **Schema Management:** Single consolidated `schema.sql` (no incremental migration chains) + `init_db.py` runner script.
- **Object Storage:** Supabase Private Storage Bucket for loan attachments and identity documents.

### Asynchronous Background Task Queue
- **Distributed Worker:** Celery `5.4.0`
- **Message Broker & Result Store:** Redis `5.2.0` (runs locally on port `6379`)
- **Scheduler:** Celery Beat (periodic cron tasks for monthly obligations, overdue checks, and reservation expiry sweeps)

---

## 5. Master Database Entity-Relationship Model

```
┌─────────────────────────────────┐
│              users              │
│  id, email, full_name, status   │
└────────────────┬────────────────┘
                 │ 1
                 │
                 │ *
┌────────────────┴────────────────┐
│       society_memberships       │
│ id, society_id, user_id, status │
└────────┬───────────────┬────────┘
         │ *             │ *
         │               │
         │ 1             │ 1
┌────────┴───────┐   ┌───┴────────────────────────┐
│   societies    │   │     loan_applications      │
│  id, name, ... │   │ id, amount, fifo_seq, ...  │
└────────┬───────┘   └───┬────────────────────────┘
         │ 1             │ 1
         │               │
         │ *             │ 1
┌────────┴───────────────┴────────┐
│      loan_reservations          │
│ id, amount, expires_at, status  │
└────────────────┬────────────────┘
                 │ 1
                 │
                 │ 1
┌────────────────┴────────────────┐
│             loans               │
│ id, principal, interest_rate, ..│
└────────┬────────────────────────┘
         │ 1
         │
         │ *
┌────────┴────────────────────────┐
│       loan_installments         │
│ id, installment_no, due_date, ..│
└─────────────────────────────────┘
```

### Key Tables & Roles:
1. `users`: Global platform identity.
2. `societies`: Individual society tenants.
3. `society_memberships`: Links users to societies with unique constraint `(society_id, user_id)`.
4. `roles` & `permissions`: Granular RBAC (`President`, `Vice President`, `Secretary`, `Treasurer`, `Member`).
5. `invitations`: Expiring single-use invitation tokens with SHA-256 hash.
6. `ledger_accounts`: Standard Chart of Accounts (Cash, Receivables, Member Contributions, Interest Income).
7. `ledger_transactions`: Balanced transactions (`status = 'POSTED'`).
8. `ledger_entries`: Individual debit and credit rows (`debit_minor`, `credit_minor`).
9. `contribution_policies`: Society savings rules (amount, frequency, due date, grace period).
10. `contribution_obligations`: Monthly bills per member per period (`status IN ('DUE', 'PAID', 'OVERDUE')`).
11. `loan_policies`: Society lending rules (interest rate, flat/reducing, tenure limits).
12. `loan_applications`: Member requests with `eligibility_at` and `fifo_sequence`.
13. `loan_reservations`: Temporary 7-day fund holds while disbursement approval is pending.
14. `loans`: Active loan contracts with snapshotted interest terms.
15. `loan_installments`: Repayment schedule rows.
16. `loan_repayments`: Recorded borrower payments.
17. `audit_logs`: Immutable before/after change logs.

---

## 6. Celery + Redis Background Task System

### Queues:
- `fifo_allocation`: Priority queue for fund checking and loan reservation.
- `billing_engine`: Scheduled generation of monthly dues and overdue marking.
- `notifications`: Async email/SMS and in-app alerts.

### Registered Tasks:
1. `tasks.fifo_allocation_sweep(society_id)`:
   - Acquires `SELECT pg_advisory_xact_lock(society_id)`.
   - Computes `available_loanable_cash`.
   - Evaluates earliest approved queue item.
   - Reserves funds if available; halts if insufficient.
2. `tasks.generate_monthly_obligations(society_id)`:
   - Celery Beat cron running on the 1st of every month.
   - Protected by `UNIQUE(membership_id, period_start, period_end)` against duplicates.
3. `tasks.expire_stale_reservations()`:
   - Hourly sweep releasing un-disbursed reservations older than 7 days and triggering re-allocation.
4. `tasks.check_overdue_obligations()`:
   - Daily sweep marking past-grace-period dues as `OVERDUE`.

---

## 7. Pluggable Auth Architecture

- **`AuthProvider` Protocol:** Abstract interface defining `verify_token(token: str) -> AuthUser`.
- **`DummyAuthProvider` (V1 Active):**
  - Resolves identities from `X-Dev-User` header or dev bearer tokens:
    - `president@society.local` (Society President)
    - `treasurer@society.local` (Society Treasurer)
    - `secretary@society.local` (Society Secretary)
    - `member1@society.local`, `member2@society.local` (Regular Members)
    - `admin@platform.local` (Platform Super Admin)
  - Interfaced in the frontend with a floating **Dev Persona Switcher** widget.
- **Production Google OAuth Bridge (V2):**
  - Replaces `DummyAuthProvider` with `SupabaseGoogleAuthProvider` checking standard Google claims (`sub`, `email`, `name`). Zero changes required to API endpoints or router guards.

---

## 8. The 12 Sequential Feature Milestones

```
1. feature/project-scaffolding-and-foundation
   └─ Clean monorepo, FastAPI health check, React Vite Tailwind shell.
2. feature/database-schema-and-indexing
   └─ Consolidated schema.sql, read-heavy composite indexes, init_db.py, SQLAlchemy models.
3. feature/creating-authentication-and-authorization
   └─ Pluggable AuthProvider, DummyAuth, DevPersonaSwitcher widget, RBAC dependencies.
4. feature/creating-background-queue
   └─ Celery worker, Redis broker, task queues, Windows run scripts, health test task.
5. feature/society-and-membership-management
   └─ Society CRUD, multi-tenant memberships, header SocietySwitcher, committee roles.
6. feature/invitation-system
   └─ SHA-256 single-use invite tokens, acceptance page, token reuse prevention.
7. feature/double-entry-ledger-and-fund
   └─ Double-entry ledger service, balanced debits/credits, dynamic fund overview cards.
8. feature/monthly-contribution-engine
   └─ Celery Beat monthly billing, Treasurer payment recording, idempotency keys.
9. feature/loan-policy-and-application
   └─ Loan policy terms, member application with live EMI calculator, committee approval.
10. feature/deterministic-fifo-loan-queue
    └─ Concurrency-locked allocation worker, strict all-or-nothing FIFO queue tracker.
11. feature/loan-servicing-and-repayments
    └─ Loan disbursement, waterfall repayments (fees->interest->principal), auto-closure.
12. feature/reports-audit-and-statements
    └─ Audit log diffs, collection registers, arrears reports, PDF/CSV statements.
```

---

## 9. Project Directory Layout

```
Society/
├── CONTEXT.md                       # THIS MASTER FILE (Read first!)
├── IMPLEMENTATION_PLAN.md           # 12-Feature step-by-step deliverable plan
├── TECH_STACK_V1.md                 # Technical stack specifications and versions
├── PRD.md                           # Original Product Requirements Document
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py              # Auth & RBAC FastAPI dependencies
│   │   │   └── v1/
│   │   │       ├── api.py           # Main router aggregator
│   │   │       ├── auth.py          # Auth endpoints
│   │   │       ├── societies.py     # Society management
│   │   │       ├── invitations.py   # Invitation generation & acceptance
│   │   │       ├── members.py       # Member directory & roles
│   │   │       ├── contributions.py # Dues & payment collection
│   │   │       ├── ledger.py        # Double-entry ledger & fund summaries
│   │   │       ├── loans.py         # Applications, FIFO queue & servicing
│   │   │       ├── reports.py       # Arrears & registers
│   │   │       └── audit.py         # Audit logs
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings
│   │   │   ├── database.py          # SQLAlchemy async sessionmaker
│   │   │   ├── auth_provider.py     # DummyAuthProvider / GoogleOAuth
│   │   │   └── security.py          # Token hashing utilities
│   │   ├── models/                  # Declarative SQLAlchemy 2.0 models
│   │   ├── schemas/                 # Pydantic v2 DTOs
│   │   ├── services/                # Encapsulated domain logic (Ledger, FIFO, Loan)
│   │   ├── tasks/                   # Celery application & worker tasks
│   │   ├── db/
│   │   │   ├── schema.sql           # Master DDL with composite indexes
│   │   │   ├── seeds.sql            # Demo data
│   │   │   └── init_db.py           # 1-click database bootstrap
│   │   └── main.py                  # FastAPI app entry point
│   ├── tests/                       # Concurrency and ledger integrity tests
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/              # Navbar, Sidebar, SocietySwitcher, Cards
│   │   │   ├── dev/                 # DevUserSwitcher widget
│   │   │   └── forms/               # Inputs, sliders, amount converters
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx      # Current user identity
│   │   │   └── SocietyContext.tsx   # Active society workspace
│   │   ├── features/                # Feature-scoped UI modules
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── services/                # Axios API client
│   │   ├── types/                   # TypeScript interfaces matching backend DTOs
│   │   ├── utils/                   # Minor unit currency and date formatters
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
└── supabase/
    └── schema.sql                   # Mirror copy for Supabase SQL Editor
```

---

## 10. Rules of Engagement for Any Working Agent

1. **Do not create incremental migration files.** Keep all DDL and index commands consolidated in `backend/app/db/schema.sql` and update `init_db.py` when adding new tables or columns.
2. **Never calculate money with floats.** Always use integer minor units (`paise` or `cents`).
3. **Never bypass the FIFO lock.** Any code that alters the loan queue or reserves money must acquire the PostgreSQL advisory transaction lock `pg_advisory_xact_lock(society_id)`.
4. **Never mix platform fees with society contributions.** They represent two legally separate financial flows.
5. **Always preserve existing docstrings, tests, and comments.**
6. **Work one feature at a time.** Finish the current feature, verify it with tests, and ensure it works before opening the next feature.
