"""Contribution Policy, Obligations, and Payment Models."""
import uuid
from datetime import date, datetime,timezone
from typing import Optional
from sqlalchemy import BigInteger, Date, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin


class ContributionPolicy(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "contribution_policies"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), default="MONTHLY", nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    grace_period_days: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    late_fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    @property
    def amount_minor(self) -> float:
        return self.amount


class ContributionObligation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "contribution_obligations"
    __table_args__ = (
        UniqueConstraint("membership_id", "period_start", "period_end", name="uq_membership_period"),
        Index("idx_obligations_society_status_due", "society_id", "status", "due_date"),
        Index("idx_obligations_member_period", "membership_id", "period_start", "period_end"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    membership_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("society_memberships.id", ondelete="CASCADE"), nullable=False)
    policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("contribution_policies.id", ondelete="SET NULL"))
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_due: Mapped[float] = mapped_column(Float, nullable=False)
    amount_paid: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DUE", nullable=False) # DUE, PAID, PARTIAL, OVERDUE, WAIVED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    membership: Mapped["SocietyMembership"] = relationship("SocietyMembership")

    @property
    def amount_due_minor(self) -> float:
        return self.amount_due

    @property
    def amount_paid_minor(self) -> float:
        return self.amount_paid


class Payment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "payments"

    society_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=True)
    payer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    payment_scope: Mapped[str] = mapped_column(String(50), nullable=False) # society_contribution, loan_repayment, platform_subscription
    provider: Mapped[str] = mapped_column(String(50), default="MANUAL", nullable=False)
    provider_transaction_id: Mapped[Optional[str]] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="CONFIRMED", nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    @property
    def amount_minor(self) -> float:
        return self.amount


class PlatformSubscription(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "platform_subscriptions"

    society_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"))
    payer_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    plan_id: Mapped[str] = mapped_column(String(50), nullable=False)
    billing_period: Mapped[str] = mapped_column(String(50), default="MONTHLY", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    current_period_start: Mapped[Optional[date]] = mapped_column(Date)
    current_period_end: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
