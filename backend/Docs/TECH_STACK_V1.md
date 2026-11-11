# Society Savings & Loan Management Platform
## V1 Tech Stack Architecture & Engineering Blueprint

**Document Version:** 1.0  
**Target:** Local Development, High-Performance Read Workloads, and Production Readiness  
**Core Stack:** React (TypeScript + Tailwind CSS) | FastAPI (Python 3.12) | Supabase (PostgreSQL) | Celery + Redis

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (SPA)                                 │
│  React 18 + TypeScript + Vite + Tailwind CSS v3 + TanStack Query + Lucide   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / JSON (Bearer Token / Dev Header)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             BACKEND API                                     │
│     FastAPI (Python 3.12) + Pydantic v2 + SQLAlchemy 2.0 (asyncpg)          │
│                      + Pluggable Dummy Auth Provider                         │
└───────────────────┬─────────────────────────────────────┬───────────────────┘
                    │                                     │
      PostgreSQL Async Queries              Async Tasks & Cron (Sweeps)
                    ▼                                     ▼
┌──────────────────────────────────────┐  ┌───────────────────────────────────┐
│     DATABASE (Supabase / Postgres)   │  │       TASK QUEUE (Celery + Redis) │
│ • Single consolidated `schema.sql`   │  │ • Redis (Broker + Result Store)   │
│ • Composite B-tree Read Indexes      │  │ • Celery Worker (FIFO Allocation) │
│ • `init_db.py` 1-click bootstrap     │  │ • Celery Beat (Monthly Billing)   │
└──────────────────────────────────────┘  └───────────────────────────────────┘
```

---

## 2. Frontend Stack Specifications (V1)

| Category | Package | Version | Purpose & Rationale |
|---|---|---|---|
| **Build & Tooling** | `vite` | `^5.4.11` | Instant Hot Module Replacement (HMR) and optimized ES module bundling. |
| **Core Framework** | `react`, `react-dom` | `^18.3.1` | Battle-tested, zero breaking changes, 100% ecosystem library compatibility. |
| **Language** | `typescript` | `^5.6.3` | Strict type checking to catch errors at compile time, matching backend DTOs. |
| **Styling** | `tailwindcss`, `postcss`, `autoprefixer` | `^3.4.15` | Fast utility classes for responsive mobile and desktop layouts without CSS bloat. |
| **Routing** | `react-router-dom` | `^6.28.0` | Client-side routing with role-based and society-context route guards. |
| **Data Fetching** | `@tanstack/react-query` | `^5.60.5` | Handles server caching, stale-while-revalidate, and optimistic updates. |
| **Forms & Validation** | `react-hook-form` + `zod` + `@hookform/resolvers` | `^7.53.2` / `^3.23.8` | High-performance, re-render-free forms with schema-driven validation. |
| **HTTP Client** | `axios` | `^1.7.7` | Pre-configured interceptors for Auth headers, dev persona tokens, and error handling. |
| **UI Helpers & Icons** | `lucide-react`, `clsx`, `tailwind-merge` | `^0.460.0` | Clean, modern iconography and conditional class merging. |

---

## 3. Backend Stack Specifications (V1)

| Category | Package | Version | Purpose & Rationale |
|---|---|---|---|
| **Web Framework** | `fastapi` | `0.115.5` | High-speed asynchronous Python framework with auto-generated Swagger UI (`/docs`). |
| **ASGI Server** | `uvicorn[standard]` | `0.32.1` | Lightning-fast async server with hot reloading. |
| **Validation & Config** | `pydantic`, `pydantic-settings` | `2.10.2` / `2.6.1` | Strict request/response DTO schemas and typed `.env` file management. |
| **Database ORM** | `sqlalchemy` | `2.0.36` | Industry standard; uses modern async 2.0 syntax with transactional locking support. |
| **PostgreSQL Driver** | `asyncpg` | `0.30.0` | High-performance asynchronous PostgreSQL driver for Python. |
| **Background Queue** | `celery` | `5.4.0` | Production-grade distributed task worker. |
| **Message Broker** | `redis` | `5.2.0` | In-memory message queue for fast task distribution. |
| **Security & JWT** | `python-jose[cryptography]`, `passlib[bcrypt]` | `3.3.0` / `1.7.4` | Standard JWT token decoding and password hashing. |
| **Testing** | `pytest`, `pytest-asyncio`, `httpx` | `8.3.3` / `0.24.0` / `0.28.0` | Asynchronous test execution for FIFO concurrency and ledger balancing. |

---

## 4. Database & Storage Architecture (V1)

### Consolidated Schema Strategy
To avoid migration clutter, all table definitions, relationships, and indexes reside in a single file:
- `backend/app/db/schema.sql` (and mirrored in `supabase/schema.sql`).
- Handled locally via `backend/app/db/init_db.py` for one-click setup and reseeding.

### Read-Heavy Indexing Strategy
Because members and administrators frequently query balances, active queues, and statement histories, the following composite indexes are included:

```sql
-- 1. Multi-Tenant Membership Lookups
CREATE INDEX idx_memberships_society_user ON society_memberships (society_id, user_id);
CREATE INDEX idx_memberships_society_status ON society_memberships (society_id, status);

-- 2. Ultra-Fast Deterministic FIFO Loan Queue Reads
-- Covers queries filtering approved applications waiting for funds ordered by FIFO sequence
CREATE INDEX idx_loan_apps_fifo_queue ON loan_applications (society_id, status, eligibility_at, fifo_sequence)
WHERE status = 'APPROVED_WAITING_FUNDS';

-- 3. Monthly Contribution Obligations & Arrears Filtering
CREATE INDEX idx_obligations_society_status_due ON contribution_obligations (society_id, status, due_date);
CREATE INDEX idx_obligations_member_period ON contribution_obligations (membership_id, period_start, period_end);

-- 4. Double-Entry Ledger Timeline & Cashbook
CREATE INDEX idx_ledger_tx_society_type_date ON ledger_transactions (society_id, transaction_type, effective_at DESC);
CREATE INDEX idx_ledger_entries_tx_acc ON ledger_entries (transaction_id, account_id);

-- 5. Active Loans & Installments
CREATE INDEX idx_loans_society_status ON loans (society_id, status);
CREATE INDEX idx_installments_loan_status_due ON loan_installments (loan_id, status, due_date);

-- 6. Audit Trail Retrieval
CREATE INDEX idx_audit_society_created ON audit_logs (society_id, created_at DESC);
```

---

## 5. Background Task Queue (Celery + Redis)

```mermaid
flowchart LR
    API[FastAPI App] -->|Deposit / Repayment Event| Redis[(Redis Broker)]
    Beat[Celery Beat Scheduler] -->|Monthly Cron / Hourly Sweep| Redis
    Redis --> Worker[Celery Worker Fleet]
    Worker -->|Lock & Allocate| DB[(PostgreSQL)]
```

### Registered Tasks:
1. **`tasks.fifo_allocation_sweep(society_id)`:**
   - Triggered when funds are added (contribution or repayment) or when reservations expire.
   - Uses `SELECT pg_advisory_xact_lock(society_id)` to prevent race conditions during concurrent allocations.
   - Enforces strict all-or-nothing FIFO allocation.
2. **`tasks.generate_monthly_obligations(society_id)`:**
   - Scheduled on the 1st of every month via Celery Beat.
   - Protected by `UNIQUE(membership_id, period_start, period_end)` to prevent duplicate billing.
3. **`tasks.expire_stale_reservations()`:**
   - Sweeps every hour to release loan reservations older than 7 days.
4. **`tasks.check_overdue_obligations()`:**
   - Flags unpaid contributions past their grace period as `OVERDUE`.

---

## 6. Pluggable Authentication System (V1 Dummy -> V2 Google OAuth)

To allow instant local testing without configuring Google Cloud Console or Supabase OAuth initially:
1. **Frontend Dev Persona Switcher:** A floating widget to test all roles with one click:
   - 👑 **President** (`president@society.local`)
   - 💰 **Treasurer** (`treasurer@society.local`)
   - 📝 **Secretary** (`secretary@society.local`)
   - 👤 **Member 1** (`member1@society.local`)
   - 👤 **Member 2** (`member2@society.local`)
   - 🛠️ **Platform Admin** (`admin@platform.local`)
2. **Pluggable Architecture:**
   - Backend routes rely on an abstract `AuthProvider` interface.
   - In V1 dev mode, `DummyAuthProvider` validates the active mock persona from the `X-Dev-User` header or test token.
   - Swapping to Google OAuth later only requires replacing the provider class—all endpoint dependencies and permission checks remain untouched.

---

## 7. Directory Structure (V1)

```
Society/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py              # Auth & RBAC dependencies
│   │   │   └── v1/
│   │   │       ├── api.py           # Master router
│   │   │       ├── auth.py          # /auth (login, dev-login, mock users)
│   │   │       ├── societies.py     # /societies (CRUD, settings, committee)
│   │   │       ├── invitations.py   # /societies/{id}/invitations & acceptance
│   │   │       ├── members.py       # /societies/{id}/members & role assignment
│   │   │       ├── contributions.py # /societies/{id}/contributions & obligations
│   │   │       ├── ledger.py        # /societies/{id}/ledger & fund summary
│   │   │       ├── loans.py         # /societies/{id}/loan-applications, /loan-queue, /loans
│   │   │       ├── reports.py       # /societies/{id}/reports (cashbook, registers, arrears)
│   │   │       └── audit.py         # /societies/{id}/audit-logs
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings (.env handling)
│   │   │   ├── database.py          # SQLAlchemy async engine & session maker
│   │   │   ├── auth_provider.py     # DummyAuthProvider / SupabaseGoogleAuthProvider
│   │   │   └── security.py          # Token hashing utilities
│   │   ├── models/                  # SQLAlchemy 2.0 Declarative Models
│   │   │   ├── base.py
│   │   │   ├── identity.py          # User, Society, SocietyMembership, Role, Permission, Invitation
│   │   │   ├── contribution.py      # ContributionPolicy, ContributionObligation, Payment
│   │   │   ├── ledger.py            # LedgerAccount, LedgerTransaction, LedgerEntry
│   │   │   ├── loan.py              # LoanPolicy, LoanApplication, LoanReservation, Loan, Installment, Repayment
│   │   │   └── audit.py             # AuditLog, Notification
│   │   ├── schemas/                 # Pydantic v2 Request/Response DTOs
│   │   ├── services/                # Business Logic Services
│   │   │   ├── ledger_service.py    # Double-entry ledger calculation & entry posting
│   │   │   ├── fifo_service.py      # Transaction-locked FIFO queue allocation
│   │   │   ├── loan_service.py      # Amortization, waterfall repayment, loan lifecycle
│   │   │   ├── contribution_service.py
│   │   │   └── invitation_service.py
│   │   ├── tasks/                   # Celery Task Definitions
│   │   │   ├── celery_app.py        # Celery application instance & configuration
│   │   │   ├── allocation_tasks.py  # FIFO queue allocation worker
│   │   │   └── billing_tasks.py     # Monthly obligations & reservation cleanup
│   │   ├── db/
│   │   │   ├── schema.sql           # Single consolidated DDL + Read-heavy indexes
│   │   │   ├── seeds.sql            # Initial test data (societies, demo committee & members)
│   │   │   └── init_db.py           # Script to initialize database from schema.sql
│   │   └── main.py                  # FastAPI application entry point
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/              # Navbar, Sidebar, SocietySwitcher, StatCard, Badge, Modal
│   │   │   ├── dev/                 # DevUserSwitcher widget
│   │   │   └── forms/               # InputField, SelectField, AmountInput
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx      # Current user identity (Dummy / Google OAuth)
│   │   │   └── SocietyContext.tsx   # Active society workspace, role & permissions
│   │   ├── features/
│   │   │   ├── auth/                # Login, DevUserSelect, AcceptInvitation
│   │   │   ├── societies/           # CreateSociety, SocietyProfile, CommitteeManagement
│   │   │   ├── members/             # MemberList, InviteMemberModal, RoleAssignment
│   │   │   ├── contributions/       # PolicyConfig, MonthlyObligationsTable, RecordPaymentModal
│   │   │   ├── ledger/              # FundOverview, Cashbook, LedgerTransactionsTable
│   │   │   ├── loans/               # LoanPolicyConfig, ApplyLoanModal, FIFOQueueViewer, LoanDetail, RepayModal
│   │   │   └── reports/             # CollectionRegister, ArrearsReport, AuditLogViewer
│   │   ├── hooks/                   # useSociety, usePermissions, useFundSummary, useLoanQueue
│   │   ├── services/
│   │   │   └── api.ts               # Axios client with auth interceptors
│   │   ├── types/                   # TypeScript interfaces matching backend DTOs
│   │   ├── utils/                   # Currency formatters (paise to INR), date formatters
│   │   ├── App.tsx                  # Root layout & route configuration
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
└── supabase/
    └── schema.sql                   # Mirror copy of schema.sql for Supabase SQL Editor
```

---

## 8. Local Environment Setup (.env.example)

```env
# Backend Environment Variables
ENVIRONMENT=development
PROJECT_NAME="Society Savings & Loan Management"
API_V1_STR="/api/v1"

# Database (Supabase PostgreSQL / Local Postgres)
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/society_db"
SYNC_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/society_db"

# Celery & Redis
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/1"

# Auth Settings
AUTH_MODE="dummy" # "dummy" for local dev, "supabase_google" for production
SECRET_KEY="dev-secret-key-change-in-production"
```
