-- =============================================================================
-- Society Savings & Loan Management Platform
-- Consolidated Master Database Schema (DDL) & Read-Heavy Performance Indexes
-- =============================================================================

-- Ensure cryptographic functions are enabled for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. IDENTITY & MULTI-TENANCY
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    email_verified_at TIMESTAMPTZ,
    phone_verified_at TIMESTAMPTZ,
    account_status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS societies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    registration_number VARCHAR(100),
    address TEXT,
    jurisdiction VARCHAR(100),
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    timezone VARCHAR(50) NOT NULL DEFAULT 'Asia/Kolkata',
    financial_year_start VARCHAR(10) NOT NULL DEFAULT '04-01',
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS society_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    member_number VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    left_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_society_user UNIQUE (society_id, user_id)
);

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID REFERENCES societies(id) ON DELETE CASCADE, -- NULL for platform global roles
    name VARCHAR(50) NOT NULL,
    description TEXT,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_role_society_name UNIQUE (society_id, name)
);

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    module VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS membership_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    membership_id UUID NOT NULL REFERENCES society_memberships(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    invited_email VARCHAR(255),
    invited_phone VARCHAR(50),
    intended_role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 2. DOUBLE-ENTRY FINANCIAL LEDGER & ACCOUNTS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ledger_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(50) NOT NULL, -- ASSET, LIABILITY, EQUITY, INCOME, EXPENSE
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_account_society_code UNIQUE (society_id, account_code)
);

CREATE TABLE IF NOT EXISTS ledger_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- CONTRIBUTION, DISBURSEMENT, REPAYMENT, ADJUSTMENT
    reference_type VARCHAR(50),
    reference_id UUID,
    description TEXT,
    effective_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'POSTED',
    idempotency_key VARCHAR(100) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES ledger_transactions(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES ledger_accounts(id) ON DELETE RESTRICT,
    debit_minor BIGINT NOT NULL DEFAULT 0,
    credit_minor BIGINT NOT NULL DEFAULT 0,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_positive_amounts CHECK (debit_minor >= 0 AND credit_minor >= 0),
    CONSTRAINT chk_debit_or_credit CHECK ((debit_minor > 0 AND credit_minor = 0) OR (credit_minor > 0 AND debit_minor = 0))
);

-- -----------------------------------------------------------------------------
-- 3. CONTRIBUTIONS, BILLING & PAYMENTS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS contribution_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    amount_minor BIGINT NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    frequency VARCHAR(50) NOT NULL DEFAULT 'MONTHLY',
    due_day INT NOT NULL DEFAULT 5,
    grace_period_days INT NOT NULL DEFAULT 5,
    late_fee_minor BIGINT NOT NULL DEFAULT 0,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contribution_obligations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    membership_id UUID NOT NULL REFERENCES society_memberships(id) ON DELETE CASCADE,
    policy_id UUID REFERENCES contribution_policies(id) ON DELETE SET NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    due_date DATE NOT NULL,
    amount_due_minor BIGINT NOT NULL,
    amount_paid_minor BIGINT NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'DUE', -- DUE, PAID, PARTIAL, OVERDUE, WAIVED
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_membership_period UNIQUE (membership_id, period_start, period_end)
);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID REFERENCES societies(id) ON DELETE CASCADE,
    payer_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    payment_scope VARCHAR(50) NOT NULL, -- society_contribution, loan_repayment, platform_subscription
    provider VARCHAR(50) NOT NULL DEFAULT 'MANUAL',
    provider_transaction_id VARCHAR(100),
    amount_minor BIGINT NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    status VARCHAR(50) NOT NULL DEFAULT 'CONFIRMED',
    idempotency_key VARCHAR(100) UNIQUE,
    confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS platform_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID REFERENCES societies(id) ON DELETE CASCADE,
    payer_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    plan_id VARCHAR(50) NOT NULL,
    billing_period VARCHAR(50) NOT NULL DEFAULT 'MONTHLY',
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    current_period_start DATE,
    current_period_end DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 4. LOAN POLICIES, APPLICATIONS & DETERMINISTIC FIFO QUEUE
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS loan_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    interest_rate NUMERIC(6, 4) NOT NULL, -- e.g. 0.0800 for 8%
    interest_period VARCHAR(50) NOT NULL DEFAULT 'ANNUAL',
    interest_method VARCHAR(50) NOT NULL DEFAULT 'REDUCING_BALANCE', -- FLAT, REDUCING_BALANCE
    calculation_convention VARCHAR(50) NOT NULL DEFAULT 'MONTHLY_AMORTIZATION',
    min_amount_minor BIGINT NOT NULL DEFAULT 500000,
    max_amount_minor BIGINT NOT NULL DEFAULT 50000000,
    min_tenure_months INT NOT NULL DEFAULT 1,
    max_tenure_months INT NOT NULL DEFAULT 36,
    eligibility_rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    allocation_rule VARCHAR(50) NOT NULL DEFAULT 'STRICT_FIFO',
    partial_allocation_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loan_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    membership_id UUID NOT NULL REFERENCES society_memberships(id) ON DELETE CASCADE,
    policy_id UUID REFERENCES loan_policies(id) ON DELETE SET NULL,
    requested_amount_minor BIGINT NOT NULL,
    purpose TEXT,
    requested_tenure_months INT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    eligibility_at TIMESTAMPTZ,
    fifo_sequence BIGINT,
    status VARCHAR(50) NOT NULL DEFAULT 'SUBMITTED', -- SUBMITTED, UNDER_REVIEW, APPROVED_WAITING_FUNDS, RESERVED, DISBURSED, REJECTED, CANCELLED
    policy_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    decision_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loan_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    loan_application_id UUID NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
    approver_membership_id UUID NOT NULL REFERENCES society_memberships(id) ON DELETE CASCADE,
    decision VARCHAR(50) NOT NULL, -- APPROVED, REJECTED, INFO_REQUESTED
    reason TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loan_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    loan_application_id UUID NOT NULL REFERENCES loan_applications(id) ON DELETE CASCADE,
    amount_minor BIGINT NOT NULL,
    reserved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE' -- ACTIVE, EXPIRED, DISBURSED, CANCELLED
);

-- -----------------------------------------------------------------------------
-- 5. LOAN SERVICING, INSTALLMENTS & REPAYMENTS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    membership_id UUID NOT NULL REFERENCES society_memberships(id) ON DELETE CASCADE,
    loan_application_id UUID UNIQUE REFERENCES loan_applications(id) ON DELETE SET NULL,
    principal_minor BIGINT NOT NULL,
    outstanding_principal_minor BIGINT NOT NULL,
    interest_rate_snapshot NUMERIC(6, 4) NOT NULL,
    interest_period_snapshot VARCHAR(50) NOT NULL,
    interest_method_snapshot VARCHAR(50) NOT NULL,
    calculation_convention_snapshot VARCHAR(50) NOT NULL,
    disbursed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    maturity_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, CLOSED, DEFAULTED
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loan_installments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    installment_number INT NOT NULL,
    due_date DATE NOT NULL,
    principal_due_minor BIGINT NOT NULL,
    interest_due_minor BIGINT NOT NULL,
    fees_due_minor BIGINT NOT NULL DEFAULT 0,
    principal_paid_minor BIGINT NOT NULL DEFAULT 0,
    interest_paid_minor BIGINT NOT NULL DEFAULT 0,
    fees_paid_minor BIGINT NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'DUE', -- DUE, PAID, PARTIAL, OVERDUE
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_loan_installment UNIQUE (loan_id, installment_number)
);

CREATE TABLE IF NOT EXISTS loan_repayments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID NOT NULL REFERENCES societies(id) ON DELETE CASCADE,
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    payment_id UUID REFERENCES payments(id) ON DELETE SET NULL,
    amount_minor BIGINT NOT NULL,
    principal_component_minor BIGINT NOT NULL DEFAULT 0,
    interest_component_minor BIGINT NOT NULL DEFAULT 0,
    fee_component_minor BIGINT NOT NULL DEFAULT 0,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'POSTED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 6. AUDIT TRAIL & NOTIFICATIONS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    society_id UUID REFERENCES societies(id) ON DELETE CASCADE,
    actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    before_snapshot JSONB,
    after_snapshot JSONB,
    reason TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    society_id UUID REFERENCES societies(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    channel VARCHAR(50) NOT NULL DEFAULT 'IN_APP',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'UNREAD', -- UNREAD, READ, ARCHIVED
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- HIGH-PERFORMANCE READ-HEAVY COMPOSITE INDEXES
-- =============================================================================

-- 1. Multi-Tenant Membership Lookups
CREATE INDEX IF NOT EXISTS idx_memberships_society_user 
    ON society_memberships (society_id, user_id);

CREATE INDEX IF NOT EXISTS idx_memberships_society_status 
    ON society_memberships (society_id, status);

-- 2. Ultra-Fast Deterministic FIFO Loan Queue Reads
-- Covers queries filtering approved applications waiting for funds ordered by eligibility & sequence
CREATE INDEX IF NOT EXISTS idx_loan_apps_fifo_queue 
    ON loan_applications (society_id, status, eligibility_at, fifo_sequence)
    WHERE status = 'APPROVED_WAITING_FUNDS';

-- 3. Monthly Contribution Obligations & Arrears Filtering
CREATE INDEX IF NOT EXISTS idx_obligations_society_status_due 
    ON contribution_obligations (society_id, status, due_date);

CREATE INDEX IF NOT EXISTS idx_obligations_member_period 
    ON contribution_obligations (membership_id, period_start, period_end);

-- 4. Double-Entry Ledger Timeline & Cashbook
CREATE INDEX IF NOT EXISTS idx_ledger_tx_society_type_date 
    ON ledger_transactions (society_id, transaction_type, effective_at DESC);

CREATE INDEX IF NOT EXISTS idx_ledger_entries_tx_acc 
    ON ledger_entries (transaction_id, account_id);

-- 5. Active Loans & Installments
CREATE INDEX IF NOT EXISTS idx_loans_society_status 
    ON loans (society_id, status);

CREATE INDEX IF NOT EXISTS idx_installments_loan_status_due 
    ON loan_installments (loan_id, status, due_date);

-- 6. Audit Trail Retrieval
CREATE INDEX IF NOT EXISTS idx_audit_society_created 
    ON audit_logs (society_id, created_at DESC);

-- 7. User Notification Stream
CREATE INDEX IF NOT EXISTS idx_notifications_user_status 
    ON notifications (user_id, status, created_at DESC);
