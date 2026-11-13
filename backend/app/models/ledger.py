"""Double-Entry Accounting Ledger Models."""
import uuid
from datetime import datetime,timezone
from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, UUIDPrimaryKeyMixin



"""
In accounting, money never appears or disappears out of nowhere—it moves from one place to another[---------similar to conservation of energy->energy can't be created or destroyed it can transfrom one form to another-------------------]:
LedgerAccount (The "Pockets" or "Buckets"): Categories where money sits or flows (e.g., Bank Account, Cash in Hand, Maintenance Income, Lift Repair Expense).                        
  • LedgerTransaction (The "Event"): The header of an overall financial action (e.g., "Flat 101 paid November Maintenance of ₹5,000").                                                   
  • LedgerEntry (The "Legs" / Line items): The individual movements of money inside a transaction.                                                                                       
  • Every transaction must have at least two entries: a Debit and a Credit.                                                                                                          
  • The Golden Rule: The sum of all Debits must always equal the sum of all Credits (Total Debits == Total Credits).

"""
class LedgerAccount(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ledger_accounts"
    __table_args__ = (
        UniqueConstraint("society_id", "account_code", name="uq_account_society_code"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    account_code: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False) # ASSET, LIABILITY, EQUITY, INCOME, EXPENSE
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    entries: Mapped[List["LedgerEntry"]] = relationship("LedgerEntry", back_populates="account")



"""
Although effective_date (or effective_at) and created_at frequently hold the exact same value in real-time digital payments, they represent two completely different timelines in accounting and software auditing: business reality versus system reality.   effective_date (Business / Accounting Date): When the financial event actually happened in the real world and which accounting period (month or financial year) it belongs to.
created_at (System / Audit Timestamp): The exact server timestamp when the database row was inserted into PostgreSQL.

"""
class LedgerTransaction(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ledger_transactions"
    __table_args__ = (
        Index("idx_ledger_tx_society_type_date", "society_id", "transaction_type", text("effective_at DESC")),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False) # CONTRIBUTION, DISBURSEMENT, REPAYMENT, ADJUSTMENT--> Category of event: CONTRIBUTION (incoming payments), DISBURSEMENT (vendor payouts), REPAYMENT, or ADJUSTMENT
    reference_type: Mapped[Optional[str]] = mapped_column(String(50)) #! Which external entity triggered this (e.g., "INVOICE", "PAYMENT_RECEIPT","EXPENSE_CLAIM")
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    description: Mapped[Optional[str]] = mapped_column(Text)

    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(50), default="POSTED", nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    entries: Mapped[List["LedgerEntry"]] = relationship("LedgerEntry", back_populates="transaction", cascade="all, delete-orphan")


"""
1. The Standard Case: 2 Entries (1 Debit + 1 Credit)Most everyday movements involve just two buckets:
Example: Member pays ₹1,000 monthly contribution   
Entry 1 (Debit): Society Bank Account = ₹1,000 (Cash increases)   
Entry 2 (Credit): Member Contributions Account = ₹1,000 (Source recorded)   
Check: ₹1,000 Debit = ₹1,000 Credit.


2.The Split Case: 3 or More Entries (Compound Transaction)Sometimes a single payment splits into multiple purposes at the exact same moment. Even then, the total Debits still equal the total Credits:   
Example: Borrower pays a ₹5,500 loan installment (₹5,000 toward principal + ₹500 toward interest)   
Entry 1 (Debit): Society Bank Account = ₹5,500 (Total cash received)   
Entry 2 (Credit): Loan Receivables Account = ₹5,000 (Principal owed goes down)   
Entry 3 (Credit): Interest Income Account = ₹500 (Society profit earned)   
Check: ₹5,500 Debit = ₹5,000 + ₹500 Credit (₹5,500).
"""

class LedgerEntry(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        Index("idx_ledger_entries_tx_acc", "transaction_id", "account_id"),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ledger_transactions.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ledger_accounts.id", ondelete="RESTRICT"), nullable=False)
    
    debit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    credit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    transaction: Mapped["LedgerTransaction"] = relationship("LedgerTransaction", back_populates="entries")
    account: Mapped["LedgerAccount"] = relationship("LedgerAccount", back_populates="entries")

    