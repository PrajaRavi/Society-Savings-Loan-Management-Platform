"""Identity, Multi-Tenancy, and RBAC Models."""
import uuid
from datetime import datetime,timezone

from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


"""
->Inherits from Base, UUIDPrimaryKeyMixin (which provides a UUID id primary key), and TimestampMixin (which provides automated created_at and updated_at tracking).
->cascade="all, delete-orphan": Ensures that if this user account is hard-deleted from the platform, all of their underlying society_memberships (and cascading roles) are automatically removed.
"""
class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    account_status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    memberships: Mapped[List["SocietyMembership"]] = relationship("SocietyMembership", back_populates="user", cascade="all, delete-orphan") 
    # ! this relationship will help me to get all memberships of a particular user
    # ! relationship() gives you the navigation; back_populates keeps them synchronized
    # ! back_populates={feild inside the relationship table} ->here in users table their is a field user inside SocietyMembership {Model} thats why i did back_populates="user"



class Society(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "societies"

    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text) #!Physical postal address of the society.
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata", nullable=False)
    financial_year_start: Mapped[str] = mapped_column(String(10), default="04-01", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)

    memberships: Mapped[List["SocietyMembership"]] = relationship("SocietyMembership", back_populates="society", cascade="all, delete-orphan")
    roles: Mapped[List["Role"]] = relationship("Role", back_populates="society", cascade="all, delete-orphan") #! this is  for defining the custom role to members inside a society


# ! The join table linking a User to a Society.
"""
__table_args__ ==> is a special SQLAlchemy class attribute used to define table-level rules, constraints, and indexes that involve multiple columns (as opposed to  single-column options like unique=True inside mapped_column). It must be written as a Python tuple.
"""
class SocietyMembership(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "society_memberships"
    __table_args__ = (
        UniqueConstraint("society_id", "user_id", name="uq_society_user"),
        Index("idx_memberships_society_user", "society_id", "user_id"),
        Index("idx_memberships_society_status", "society_id", "status"),
    )

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    member_number: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    society: Mapped["Society"] = relationship("Society", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="memberships")
    membership_roles: Mapped[List["MembershipRole"]] = relationship("MembershipRole", back_populates="membership", cascade="all, delete-orphan")
    #! The roles assigned to this specific member


#! Defines roles like Admin, Secretary, Treasurer, Resident, or Security
class Role(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("society_id", "name", name="uq_role_society_name"),
    )

    society_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text) #! Explanation of what duties this role entails.
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) #! If True, means this role is defined by the super-admin and it can't be deleted or renamed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    society: Mapped[Optional["Society"]] = relationship("Society", back_populates="roles")
    permissions: Mapped[List["Permission"]] = relationship("Permission", secondary="role_permissions", back_populates="roles")
    #! The secondary parameter inside SQLAlchemy's relationship() is used to define a direct Many-to-Many relationship between two models by pointing to the association (join) table that sits in between them.
    # ! ex->we are connecting {roles} and {permission} tables through {role_permissions} table
    # ! so we can say one role can have multiple permissions and one permissions can assigned to mutliple roles[many->many]
    #! List of permissions granted to this role (linked through role_permissions).


#! The atomic privileges in the system (e.g., create announcements, collect payments)
class Permission(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False) #!Code used in the backend to check authorization (e.g., "notices:create", "finances:view")
    description: Mapped[Optional[str]] = mapped_column(Text) #!Human-readable explanation of what this permission allows
    module: Mapped[str] = mapped_column(String(50), nullable=False) #!Category or feature area (e.g., "billing", "gatekeeping", "notices")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    roles: Mapped[List["Role"]] = relationship("Role", secondary="role_permissions", back_populates="permissions") #! All roles that include this permission


# ! A Bridge (Many-to-Many) Table between roles and permissions. One role can have multiple permissions, and one permission can belong to multiple roles.
class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)



# ! Assigns a Role to a SocietyMembership. Includes time-bounding (effective dates).
class MembershipRole(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "membership_roles"

    membership_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("society_memberships.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()")) #! when this role starts
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))#! when this role ends
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))

    membership: Mapped["SocietyMembership"] = relationship("SocietyMembership", back_populates="membership_roles")
    role: Mapped["Role"] = relationship("Role")


class Invitation(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "invitations"

    society_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("societies.id", ondelete="CASCADE"), nullable=False)
    invited_email: Mapped[Optional[str]] = mapped_column(String(255))
    invited_phone: Mapped[Optional[str]] = mapped_column(String(50))
    intended_role_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="SET NULL"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    invited_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=text("NOW()"))
