"""initial_schema: 24 entity tables and 11 high-performance composite indexes.

Revision ID: c61fb8f69534
Revises: 
Create Date: 2026-11-12 09:27:17.950389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = 'c61fb8f69534'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. IDENTITY, USERS, SOCIETIES & RBAC
    # -------------------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=True),
        sa.Column('phone', sa.String(50), unique=True, index=True, nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('phone_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('account_status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'societies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('legal_name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('registration_number', sa.String(100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('jurisdiction', sa.String(100), nullable=True),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='Asia/Kolkata'),
        sa.Column('financial_year_start', sa.String(10), nullable=False, server_default='04-01'),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'society_memberships',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('member_number', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('society_id', 'user_id', name='uq_society_user'),
    )

    op.create_table(
        'roles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='FALSE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('society_id', 'name', name='uq_role_society_name'),
    )

    op.create_table(
        'permissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('key', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'role_permissions',
        sa.Column('role_id', UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    )

    op.create_table(
        'membership_roles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('membership_id', UUID(as_uuid=True), sa.ForeignKey('society_memberships.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'invitations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invited_email', sa.String(255), nullable=True),
        sa.Column('invited_phone', sa.String(50), nullable=True),
        sa.Column('intended_role_id', UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('token_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('invited_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    # -------------------------------------------------------------------------
    # 2. DOUBLE-ENTRY LEDGER & FINANCIAL ACCOUNTS
    # -------------------------------------------------------------------------
    op.create_table(
        'ledger_accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_code', sa.String(50), nullable=False),
        sa.Column('account_name', sa.String(100), nullable=False),
        sa.Column('account_type', sa.String(50), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='TRUE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('society_id', 'account_code', name='uq_account_society_code'),
    )

    op.create_table(
        'ledger_transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('effective_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='POSTED'),
        sa.Column('idempotency_key', sa.String(100), unique=True, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'ledger_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('transaction_id', UUID(as_uuid=True), sa.ForeignKey('ledger_transactions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey('ledger_accounts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('debit', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('credit', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    # -------------------------------------------------------------------------
    # 3. CONTRIBUTION POLICIES, OBLIGATIONS & PAYMENTS
    # -------------------------------------------------------------------------
    op.create_table(
        'contribution_policies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),
        sa.Column('frequency', sa.String(50), nullable=False, server_default='MONTHLY'),
        sa.Column('due_day', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('grace_period_days', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('late_fee', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'contribution_obligations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('membership_id', UUID(as_uuid=True), sa.ForeignKey('society_memberships.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_id', UUID(as_uuid=True), sa.ForeignKey('contribution_policies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('amount_due', sa.Float(), nullable=False),
        sa.Column('amount_paid', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='DUE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('membership_id', 'period_start', 'period_end', name='uq_membership_period'),
    )

    op.create_table(
        'payments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('payer_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('payment_scope', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False, server_default='MANUAL'),
        sa.Column('provider_transaction_id', sa.String(100), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(50), nullable=False, server_default='CONFIRMED'),
        sa.Column('idempotency_key', sa.String(100), unique=True, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'platform_subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_name', sa.String(50), nullable=False, server_default='FREE_TIER'),
        sa.Column('monthly_fee', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('billing_cycle_day', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    # -------------------------------------------------------------------------
    # 4. LOAN POLICIES, APPLICATIONS, APPROVALS & RESERVATIONS
    # -------------------------------------------------------------------------
    op.create_table(
        'loan_policies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('interest_rate', sa.Numeric(6, 4), nullable=False),
        sa.Column('interest_period', sa.String(50), nullable=False, server_default='ANNUAL'),
        sa.Column('interest_method', sa.String(50), nullable=False, server_default='REDUCING_BALANCE'),
        sa.Column('calculation_convention', sa.String(50), nullable=False, server_default='MONTHLY_AMORTIZATION'),
        sa.Column('min_amount', sa.Float(), nullable=False, server_default='5000.0'),
        sa.Column('max_amount', sa.Float(), nullable=False, server_default='500000.0'),
        sa.Column('min_tenure_months', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_tenure_months', sa.Integer(), nullable=False, server_default='36'),
        sa.Column('eligibility_rules', JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('allocation_rule', sa.String(50), nullable=False, server_default='STRICT_FIFO'),
        sa.Column('partial_allocation_allowed', sa.Boolean(), nullable=False, server_default='FALSE'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'loan_applications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('membership_id', UUID(as_uuid=True), sa.ForeignKey('society_memberships.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_id', UUID(as_uuid=True), sa.ForeignKey('loan_policies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requested_amount', sa.Float(), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('requested_tenure_months', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('eligibility_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fifo_sequence', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='SUBMITTED'),
        sa.Column('policy_snapshot', JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'loan_approvals',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('loan_application_id', UUID(as_uuid=True), sa.ForeignKey('loan_applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('approver_membership_id', UUID(as_uuid=True), sa.ForeignKey('society_memberships.id', ondelete='CASCADE'), nullable=False),
        sa.Column('decision', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'loan_reservations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('loan_application_id', UUID(as_uuid=True), sa.ForeignKey('loan_applications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('reserved_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
    )

    # -------------------------------------------------------------------------
    # 5. LOANS, INSTALLMENTS & REPAYMENTS
    # -------------------------------------------------------------------------
    op.create_table(
        'loans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('membership_id', UUID(as_uuid=True), sa.ForeignKey('society_memberships.id', ondelete='CASCADE'), nullable=False),
        sa.Column('loan_application_id', UUID(as_uuid=True), sa.ForeignKey('loan_applications.id', ondelete='SET NULL'), unique=True, nullable=True),
        sa.Column('principal', sa.Float(), nullable=False),
        sa.Column('outstanding_principal', sa.Float(), nullable=False),
        sa.Column('interest_rate_snapshot', sa.Numeric(6, 4), nullable=False),
        sa.Column('interest_period_snapshot', sa.String(50), nullable=False),
        sa.Column('interest_method_snapshot', sa.String(50), nullable=False),
        sa.Column('calculation_convention_snapshot', sa.String(50), nullable=False),
        sa.Column('disbursed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('maturity_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'loan_installments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('loan_id', UUID(as_uuid=True), sa.ForeignKey('loans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('installment_number', sa.Integer(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('principal_due', sa.Float(), nullable=False),
        sa.Column('interest_due', sa.Float(), nullable=False),
        sa.Column('fees_due', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('principal_paid', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('interest_paid', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('fees_paid', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='DUE'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('loan_id', 'installment_number', name='uq_loan_installment'),
    )

    op.create_table(
        'loan_repayments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('loan_id', UUID(as_uuid=True), sa.ForeignKey('loans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('payment_id', UUID(as_uuid=True), sa.ForeignKey('payments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('principal_component', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('interest_component', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('fee_component', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('status', sa.String(50), nullable=False, server_default='POSTED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    # -------------------------------------------------------------------------
    # 6. AUDIT TRAIL & NOTIFICATIONS
    # -------------------------------------------------------------------------
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('actor_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('before_snapshot', JSONB(), nullable=True),
        sa.Column('after_snapshot', JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('society_id', UUID(as_uuid=True), sa.ForeignKey('societies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False, server_default='IN_APP'),
        sa.Column('payload', JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('status', sa.String(50), nullable=False, server_default='UNREAD'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )

    # -------------------------------------------------------------------------
    # 7. HIGH-PERFORMANCE READ-HEAVY COMPOSITE INDEXES
    # -------------------------------------------------------------------------
    op.create_index('idx_memberships_society_user', 'society_memberships', ['society_id', 'user_id'])
    op.create_index('idx_memberships_society_status', 'society_memberships', ['society_id', 'status'])
    op.create_index(
        'idx_loan_apps_fifo_queue',
        'loan_applications',
        ['society_id', 'status', 'eligibility_at', 'fifo_sequence'],
        postgresql_where=sa.text("status = 'APPROVED_WAITING_FUNDS'"),
    )
    op.create_index('idx_obligations_society_status_due', 'contribution_obligations', ['society_id', 'status', 'due_date'])
    op.create_index('idx_obligations_member_period', 'contribution_obligations', ['membership_id', 'period_start', 'period_end'])
    op.create_index('idx_ledger_tx_society_type_date', 'ledger_transactions', ['society_id', 'transaction_type', sa.text('effective_at DESC')])
    op.create_index('idx_ledger_entries_tx_acc', 'ledger_entries', ['transaction_id', 'account_id'])
    op.create_index('idx_loans_society_status', 'loans', ['society_id', 'status'])
    op.create_index('idx_installments_loan_status_due', 'loan_installments', ['loan_id', 'status', 'due_date'])
    op.create_index('idx_audit_society_created', 'audit_logs', ['society_id', sa.text('created_at DESC')])
    op.create_index('idx_notifications_user_status', 'notifications', ['user_id', 'status', sa.text('created_at DESC')])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_notifications_user_status', table_name='notifications')
    op.drop_index('idx_audit_society_created', table_name='audit_logs')
    op.drop_index('idx_installments_loan_status_due', table_name='loan_installments')
    op.drop_index('idx_loans_society_status', table_name='loans')
    op.drop_index('idx_ledger_entries_tx_acc', table_name='ledger_entries')
    op.drop_index('idx_ledger_tx_society_type_date', table_name='ledger_transactions')
    op.drop_index('idx_obligations_member_period', table_name='contribution_obligations')
    op.drop_index('idx_obligations_society_status_due', table_name='contribution_obligations')
    op.drop_index('idx_loan_apps_fifo_queue', table_name='loan_applications')
    op.drop_index('idx_memberships_society_status', table_name='society_memberships')
    op.drop_index('idx_memberships_society_user', table_name='society_memberships')

    # Drop tables in reverse dependency order
    op.drop_table('notifications')
    op.drop_table('audit_logs')
    op.drop_table('loan_repayments')
    op.drop_table('loan_installments')
    op.drop_table('loans')
    op.drop_table('loan_reservations')
    op.drop_table('loan_approvals')
    op.drop_table('loan_applications')
    op.drop_table('loan_policies')
    op.drop_table('platform_subscriptions')
    op.drop_table('payments')
    op.drop_table('contribution_obligations')
    op.drop_table('contribution_policies')
    op.drop_table('ledger_entries')
    op.drop_table('ledger_transactions')
    op.drop_table('ledger_accounts')
    op.drop_table('invitations')
    op.drop_table('membership_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('society_memberships')
    op.drop_table('societies')
    op.drop_table('users')
