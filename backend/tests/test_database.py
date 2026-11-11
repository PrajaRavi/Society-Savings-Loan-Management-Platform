"""Tests for Database Schema, Models, and Exponential Back-Off Resilience."""
import pytest
import asyncio
from decimal import Decimal
from sqlalchemy import BigInteger
from app.models import (
    Base,
    User,
    Society,
    SocietyMembership,
    Role,
    Permission,
    LedgerAccount,
    LedgerTransaction,
    LedgerEntry,
    ContributionPolicy,
    ContributionObligation,
    Payment,
    LoanPolicy,
    LoanApplication,
    LoanReservation,
    Loan,
    LoanInstallment,
    LoanRepayment,
    AuditLog,
    Notification,
)
from app.core.retry import calculate_backoff, retry_async, retry_sync


def test_models_metadata_registered():
    """Verify all 20+ tables are properly registered in SQLAlchemy metadata."""
    expected_tables = {
        "users",
        "societies",
        "society_memberships",
        "roles",
        "permissions",
        "role_permissions",
        "membership_roles",
        "invitations",
        "ledger_accounts",
        "ledger_transactions",
        "ledger_entries",
        "contribution_policies",
        "contribution_obligations",
        "payments",
        "platform_subscriptions",
        "loan_policies",
        "loan_applications",
        "loan_approvals",
        "loan_reservations",
        "loans",
        "loan_installments",
        "loan_repayments",
        "audit_logs",
        "notifications",
    }
    registered_tables = set(Base.metadata.tables.keys())
    for table in expected_tables:
        assert table in registered_tables, f"Table '{table}' missing from Base.metadata"


def test_monetary_columns_use_bigint():
    """Architectural Law: All monetary columns must use BIGINT (integer minor units)."""
    # Check LedgerEntry
    assert isinstance(LedgerEntry.__table__.columns["debit_minor"].type, BigInteger)
    assert isinstance(LedgerEntry.__table__.columns["credit_minor"].type, BigInteger)

    # Check ContributionObligation & Policy
    assert isinstance(ContributionPolicy.__table__.columns["amount_minor"].type, BigInteger)
    assert isinstance(ContributionObligation.__table__.columns["amount_due_minor"].type, BigInteger)
    assert isinstance(ContributionObligation.__table__.columns["amount_paid_minor"].type, BigInteger)

    # Check LoanApplication & Loan
    assert isinstance(LoanApplication.__table__.columns["requested_amount_minor"].type, BigInteger)
    assert isinstance(Loan.__table__.columns["principal_minor"].type, BigInteger)
    assert isinstance(Loan.__table__.columns["outstanding_principal_minor"].type, BigInteger)

    # Check Installments
    assert isinstance(LoanInstallment.__table__.columns["principal_due_minor"].type, BigInteger)
    assert isinstance(LoanInstallment.__table__.columns["interest_due_minor"].type, BigInteger)


def test_exponential_backoff_bounds():
    """Verify exponential back-off calculation with jitter adheres to bounds."""
    base_delay = 1.0
    max_delay = 16.0

    for attempt in range(5):
        delay = calculate_backoff(attempt, base_delay=base_delay, max_delay=max_delay, jitter=True)
        assert delay >= base_delay * 0.1
        # Delay with jitter should never exceed max_delay
        assert delay <= max_delay

    # Without jitter, verify strict exponential progression: 1, 2, 4, 8, 16
    assert calculate_backoff(0, base_delay=1.0, max_delay=16.0, jitter=False) == 1.0
    assert calculate_backoff(1, base_delay=1.0, max_delay=16.0, jitter=False) == 2.0
    assert calculate_backoff(2, base_delay=1.0, max_delay=16.0, jitter=False) == 4.0
    assert calculate_backoff(3, base_delay=1.0, max_delay=16.0, jitter=False) == 8.0
    assert calculate_backoff(4, base_delay=1.0, max_delay=16.0, jitter=False) == 16.0
    assert calculate_backoff(5, base_delay=1.0, max_delay=16.0, jitter=False) == 16.0  # capped


@pytest.mark.asyncio
async def test_retry_async_eventual_success():
    """Verify retry_async decorator succeeds when transient errors resolve."""
    attempts = 0

    @retry_async(max_retries=4, base_delay=0.01, max_delay=0.05, exceptions=(ValueError,))
    async def flaky_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Transient error")
        return "success"

    result = await flaky_operation()
    assert result == "success"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_async_exhaustion():
    """Verify retry_async decorator raises after max retries are exhausted."""
    attempts = 0

    @retry_async(max_retries=3, base_delay=0.01, max_delay=0.05, exceptions=(RuntimeError,))
    async def always_fails():
        nonlocal attempts
        attempts += 1
        raise RuntimeError("Permanent failure")

    with pytest.raises(RuntimeError):
        await always_fails()
    assert attempts == 3


def test_retry_sync_eventual_success():
    """Verify retry_sync decorator succeeds when transient errors resolve."""
    attempts = 0

    @retry_sync(max_retries=3, base_delay=0.01, max_delay=0.05, exceptions=(ConnectionResetError,))
    def flaky_sync():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionResetError("Transient reset")
        return 42

    result = flaky_sync()
    assert result == 42
    assert attempts == 2
