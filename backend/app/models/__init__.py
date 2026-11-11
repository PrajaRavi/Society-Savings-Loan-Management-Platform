"""Declarative models registry."""
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.identity import (
    User,
    Society,
    SocietyMembership,
    Role,
    Permission,
    RolePermission,
    MembershipRole,
    Invitation,
)
from app.models.ledger import (
    LedgerAccount,
    LedgerTransaction,
    LedgerEntry,
)
from app.models.contribution import (
    ContributionPolicy,
    ContributionObligation,
    Payment,
    PlatformSubscription,
)
from app.models.loan import (
    LoanPolicy,
    LoanApplication,
    LoanApproval,
    LoanReservation,
    Loan,
    LoanInstallment,
    LoanRepayment,
)
from app.models.audit import (
    AuditLog,
    Notification,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "User",
    "Society",
    "SocietyMembership",
    "Role",
    "Permission",
    "RolePermission",
    "MembershipRole",
    "Invitation",
    "LedgerAccount",
    "LedgerTransaction",
    "LedgerEntry",
    "ContributionPolicy",
    "ContributionObligation",
    "Payment",
    "PlatformSubscription",
    "LoanPolicy",
    "LoanApplication",
    "LoanApproval",
    "LoanReservation",
    "Loan",
    "LoanInstallment",
    "LoanRepayment",
    "AuditLog",
    "Notification",
]
