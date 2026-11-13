"""Loan Policies, Applications, Deterministic FIFO Queue, and Servicing Models."""
import uuid
from datetime import date, datetime,timezone
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
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
from app.models.identity import SocietyMembership

"""
  1. LoanPolicy (The Loan Scheme): The rules set by the society (e.g., "Emergency Loan: 8% annual interest, max ₹1,00,000 for up to 24 months, queued strictly First-Come-First-Served").
  2. LoanApplication (The Application Form): A member requests to borrow money (e.g., "Flat 302 requests ₹50,000 for 12 months for home painting").
                                        
  3. LoanApproval (The Committee Vote): Managing committee members review and vote to approve or reject the request.                                                                     


  4. LoanReservation (The Fund Lock): Because society money is limited, when a loan is approved, money from the society treasury is "locked/reserved" for that member so no one else takes it before                                                             disbursement.                                                                                                                                                              
  5. Loan (The Active Disbursed Loan): Once the money is sent to the borrower, this record tracks the overall debt and remaining balance.                                                
  6. LoanInstallment (The EMI Schedule / Calendar): The month-by-month repayment breakdown (e.g., Month 1: Principal ₹4,000 + Interest ₹333).                                            
  7. LoanRepayment (The Actual EMI Payment): The record of the borrower paying an installment, splitting the money between principal reduction and interest income

"""
class LoanPolicy(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_policies"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    interest_rate: Mapped[Float] = mapped_column(Float, nullable=False) # e.g. 0.0800 for 8%
    interest_period: Mapped[str] = mapped_column(String(50), default="ANNUAL", nullable=False)
    interest_method: Mapped[str] = mapped_column(String(50), default="REDUCING_BALANCE", nullable=False) # FLAT, REDUCING_BALANCE
    calculation_convention: Mapped[str] = mapped_column(String(50), default="MONTHLY_AMORTIZATION", nullable=False)
    # ! The borrowing boundaries (e.g., minimum ₹5,000, maximum ₹5,00,000)
    min_amount: Mapped[float] = mapped_column(Float, default=5000.0, nullable=False)
    max_amount: Mapped[float] = mapped_column(Float, default=500000.0, nullable=False)
    # ! Allowed duration of the loan (e.g., 1 to 36 months)
    min_tenure_months: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_tenure_months: Mapped[int] = mapped_column(Integer, default=36, nullable=False)
    eligibility_rules: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    allocation_rule: Mapped[str] = mapped_column(String(50), default="STRICT_FIFO", nullable=False)
    partial_allocation_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) #! Whether a borrower can receive a portion of the loan if full funds aren't available
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))


class LoanApplication(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_applications"
    __table_args__ = (
        Index(
            "idx_loan_apps_fifo_queue",
            "society_id",
            "status",
            "eligibility_at",
            "fifo_sequence",
            postgresql_where=text("status = 'APPROVED_WAITING_FUNDS'"),
        ),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    membership_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("society_memberships.id", ondelete="CASCADE"), nullable=False)
    policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_policies.id", ondelete="SET NULL"))
    requested_amount: Mapped[float] = mapped_column(Float, nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(Text)
    requested_tenure_months: Mapped[int] = mapped_column(Integer, nullable=False) #!Number of months requested to repay.
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    eligibility_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True)) #!Timestamp when the system verified applicant eligibility.
    fifo_sequence: Mapped[Optional[int]] = mapped_column(Integer) #! Queue ticket number for waiting funds (ensures fair First-In,First-Out disbursement).
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False)
    policy_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb")) #! Save a snapshot of policy so that user can see it always[safer side]
    decision_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    membership: Mapped["SocietyMembership"] = relationship("SocietyMembership")
    approvals: Mapped[List["LoanApproval"]] = relationship("LoanApproval", back_populates="application", cascade="all, delete-orphan")
    reservations: Mapped[List["LoanReservation"]] = relationship("LoanReservation", back_populates="application", cascade="all, delete-orphan")
    loan: Mapped[Optional["Loan"]] = relationship("Loan", back_populates="application", uselist=False)


class LoanApproval(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_approvals"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    loan_application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    approver_membership_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("society_memberships.id", ondelete="CASCADE"), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    application: Mapped["LoanApplication"] = relationship("LoanApplication", back_populates="approvals")


class LoanReservation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_reservations"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    loan_application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)

    application: Mapped["LoanApplication"] = relationship("LoanApplication", back_populates="reservations")


class Loan(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loans"
    __table_args__ = (
        Index("idx_loans_society_status", "society_id", "status"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    membership_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("society_memberships.id", ondelete="CASCADE"), nullable=False)
    loan_application_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="SET NULL"), unique=True)
    principal: Mapped[float] = mapped_column(Float, nullable=False) #! Original principal disbursed (e.g., 100000.0).
    outstanding_principal: Mapped[float] = mapped_column(Float, nullable=False) #! Remaining unpaid principal balance (decreases with every EMI if the intrest method is ->REDUCING_BALANCE)
    interest_rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    interest_period_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    interest_method_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    calculation_convention_snapshot: Mapped[str] = mapped_column(String(50), nullable=False)
    disbursed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)#! Final date when the full loan must be cleared.
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    
    membership: Mapped["SocietyMembership"] = relationship("SocietyMembership")
    application: Mapped[Optional["LoanApplication"]] = relationship("LoanApplication", back_populates="loan")
    installments: Mapped[List["LoanInstallment"]] = relationship("LoanInstallment", back_populates="loan", cascade="all, delete-orphan")
    repayments: Mapped[List["LoanRepayment"]] = relationship("LoanRepayment", back_populates="loan", cascade="all, delete-orphan")



class LoanInstallment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_installments"
    __table_args__ = (
        UniqueConstraint("loan_id", "installment_number", name="uq_loan_installment"),
        Index("idx_installments_loan_status_due", "loan_id", "status", "due_date"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    loan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_due: Mapped[float] = mapped_column(Float, nullable=False)
    interest_due: Mapped[float] = mapped_column(Float, nullable=False)
    fees_due: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    principal_paid: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    interest_paid: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fees_paid: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DUE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    loan: Mapped["Loan"] = relationship("Loan", back_populates="installments")


class LoanRepayment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "loan_repayments"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    loan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    principal_component: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    interest_component: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fee_component: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    status: Mapped[str] = mapped_column(String(50), default="POSTED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    loan: Mapped["Loan"] = relationship("Loan", back_populates="repayments")
