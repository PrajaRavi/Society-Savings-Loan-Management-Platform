"""Loan Policies, Applications, Deterministic FIFO Queue, and Servicing Models."""
import uuid
from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin


class LoanPolicy(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_policies"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False) # e.g. 0.0800 for 8%
    interest_period: Mapped[str] = mapped_column(String(50), default="ANNUAL", nullable=False)
    interest_method: Mapped[str] = mapped_column(String(50), default="REDUCING_BALANCE", nullable=False) # FLAT, REDUCING_BALANCE
    calculation_convention: Mapped[str] = mapped_column(String(50), default="MONTHLY_AMORTIZATION", nullable=False)
    min_amount_minor: Mapped[int] = mapped_column(BigInteger, default=500000, nullable=False)
    max_amount_minor: Mapped[int] = mapped_column(BigInteger, default=50000000, nullable=False)
    min_tenure_months: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_tenure_months: Mapped[int] = mapped_column(Integer, default=36, nullable=False)
    eligibility_rules: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    allocation_rule: Mapped[str] = mapped_column(String(50), default="STRICT_FIFO", nullable=False)
    partial_allocation_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))


class LoanApplication(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_applications"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    membership_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("society_memberships.id", ondelete="CASCADE"), nullable=False)
    policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_policies.id", ondelete="SET NULL"))
    requested_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(Text)
    requested_tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    eligibility_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    fifo_sequence: Mapped[Optional[int]] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False) # SUBMITTED, UNDER_REVIEW, APPROVED_WAITING_FUNDS, RESERVED, DISBURSED, REJECTED, CANCELLED
    policy_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    decision_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    membership: Mapped["SocietyMembership"] = relationship("SocietyMembership")
    approvals: Mapped[List["LoanApproval"]] = relationship("LoanApproval", back_populates="application", cascade="all, delete-orphan")
    reservations: Mapped[List["LoanReservation"]] = relationship("LoanReservation", back_populates="application", cascade="all, delete-orphan")
    loan: Mapped[Optional["Loan"]] = relationship("Loan", back_populates="application", uselist=False)


class LoanApproval(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_approvals"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    loan_application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    approver_membership_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("society_memberships.id", ondelete="CASCADE"), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False) # APPROVED, REJECTED, INFO_REQUESTED
    reason: Mapped[Optional[str]] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    application: Mapped["LoanApplication"] = relationship("LoanApplication", back_populates="approvals")


class LoanReservation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_reservations"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    loan_application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False) # ACTIVE, EXPIRED, DISBURSED, CANCELLED

    application: Mapped["LoanApplication"] = relationship("LoanApplication", back_populates="reservations")


class Loan(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loans"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    membership_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("society_memberships.id", ondelete="CASCADE"), nullable=False)
    loan_application_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="SET NULL"), unique=True)
    principal_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    outstanding_principal_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    interest_rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    interest_period_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    interest_method_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    calculation_convention_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    disbursed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False) # ACTIVE, CLOSED, DEFAULTED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    membership: Mapped["SocietyMembership"] = relationship("SocietyMembership")
    application: Mapped[Optional["LoanApplication"]] = relationship("LoanApplication", back_populates="loan")
    installments: Mapped[List["LoanInstallment"]] = relationship("LoanInstallment", back_populates="loan", cascade="all, delete-orphan")
    repayments: Mapped[List["LoanRepayment"]] = relationship("LoanRepayment", back_populates="loan", cascade="all, delete-orphan")


class LoanInstallment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_installments"
    __table_args__ = (
        UniqueConstraint("loan_id", "installment_number", name="uq_loan_installment"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    loan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_due_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    interest_due_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fees_due_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    principal_paid_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    interest_paid_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    fees_paid_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DUE", nullable=False) # DUE, PAID, PARTIAL, OVERDUE
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    loan: Mapped["Loan"] = relationship("Loan", back_populates="installments")


class LoanRepayment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_repayments"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    loan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"))
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    principal_component_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    interest_component_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    fee_component_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    status: Mapped[str] = mapped_column(String(50), default="POSTED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    loan: Mapped["Loan"] = relationship("Loan", back_populates="repayments")
