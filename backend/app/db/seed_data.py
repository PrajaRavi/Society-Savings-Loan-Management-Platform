"""Pure SQLAlchemy seed data runner for Society Savings & Loan Platform.

Seeds:
- 14 Standard RBAC Permissions
- Demo Society (Greenwood Society)
- 5 Standard Roles and Role-Permission Mappings
- Standard Chart of Accounts (6 double-entry ledger accounts)
- 6 Development Personas & Society Memberships with assigned roles
- Default Contribution & Loan Policies
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.core.database import AsyncSessionLocal
from app.models.identity import (
    Permission,
    Role,
    RolePermission,
    Society,
    SocietyMembership,
    MembershipRole,
    User,
)
from app.models.ledger import LedgerAccount
from app.models.contribution import ContributionPolicy
from app.models.loan import LoanPolicy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("society.seed")

# Deterministic UUIDs for demo environment
SOCIETY_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")

PERMISSIONS_DATA = [
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000001"), "key": "society:manage", "description": "Manage society settings and policies", "module": "society"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000002"), "key": "member:invite", "description": "Generate member invitation links", "module": "membership"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000003"), "key": "member:view", "description": "View members directory and profiles", "module": "membership"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000004"), "key": "member:update_role", "description": "Assign committee roles to members", "module": "membership"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000005"), "key": "contribution:view", "description": "View member contribution obligations", "module": "contribution"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000006"), "key": "contribution:record", "description": "Record confirmed member contribution payments", "module": "contribution"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000007"), "key": "ledger:view", "description": "Inspect society double-entry cashbook and ledger", "module": "ledger"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000008"), "key": "ledger:post_entry", "description": "Post manual double-entry adjustments", "module": "ledger"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000009"), "key": "loan:apply", "description": "Apply for a member loan from the pool", "module": "loan"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000010"), "key": "loan:approve", "description": "Approve or reject member loan applications", "module": "loan"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000011"), "key": "loan:disburse", "description": "Disburse approved and reserved loans", "module": "loan"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000012"), "key": "loan:view", "description": "View loan portfolio and FIFO queue", "module": "loan"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000013"), "key": "report:view", "description": "Generate collection registers, arrears and statements", "module": "reports"},
    {"id": uuid.UUID("b0000000-0000-0000-0000-000000000014"), "key": "audit:view", "description": "Access immutable audit logs", "module": "audit"},
]

ROLES_DATA = [
    {"id": uuid.UUID("c0000000-0000-0000-0000-000000000001"), "society_id": SOCIETY_ID, "name": "President", "description": "Chief Executive Officer with comprehensive oversight and loan approval authority", "is_system": True},
    {"id": uuid.UUID("c0000000-0000-0000-0000-000000000002"), "society_id": SOCIETY_ID, "name": "Vice President", "description": "Executive oversight and secondary approval quorum", "is_system": True},
    {"id": uuid.UUID("c0000000-0000-0000-0000-000000000003"), "society_id": SOCIETY_ID, "name": "Secretary", "description": "Administrative workflows, invitations, notices and meetings", "is_system": True},
    {"id": uuid.UUID("c0000000-0000-0000-0000-000000000004"), "society_id": SOCIETY_ID, "name": "Treasurer", "description": "Financial custodian: ledger, collections, disbursements, and statements", "is_system": True},
    {"id": uuid.UUID("c0000000-0000-0000-0000-000000000005"), "society_id": SOCIETY_ID, "name": "Member", "description": "General society participant: monthly savings and loan borrower", "is_system": True},
]

ACCOUNTS_DATA = [
    {"id": uuid.UUID("d0000000-0000-0000-0000-000000000001"), "society_id": SOCIETY_ID, "account_code": "1010", "account_name": "Cash / Bank Main Pool", "account_type": "ASSET", "currency": "INR", "is_active": True},
    {"id": uuid.UUID("d0000000-0000-0000-0000-000000000002"), "society_id": SOCIETY_ID, "account_code": "1020", "account_name": "Loan Receivables (Principal)", "account_type": "ASSET", "currency": "INR", "is_active": True},
    {"id": uuid.UUID("d0000000-0000-0000-0000-000000000003"), "society_id": SOCIETY_ID, "account_code": "2010", "account_name": "Pending Loan Reserves", "account_type": "LIABILITY", "currency": "INR", "is_active": True},
    {"id": uuid.UUID("d0000000-0000-0000-0000-000000000004"), "society_id": SOCIETY_ID, "account_code": "3010", "account_name": "Member Contributions Capital", "account_type": "EQUITY", "currency": "INR", "is_active": True},
    {"id": uuid.UUID("d0000000-0000-0000-0000-000000000005"), "society_id": SOCIETY_ID, "account_code": "4010", "account_name": "Loan Interest Income", "account_type": "INCOME", "currency": "INR", "is_active": True},
    {"id": uuid.UUID("d0000000-0000-0000-0000-000000000006"), "society_id": SOCIETY_ID, "account_code": "4020", "account_name": "Late Fee & Penalty Income", "account_type": "INCOME", "currency": "INR", "is_active": True},
]

USERS_DATA = [
    {"id": uuid.UUID("e0000000-0000-0000-0000-000000000000"), "email": "admin@platform.local", "full_name": "Platform Super Administrator", "account_status": "ACTIVE"},
    {"id": uuid.UUID("e0000000-0000-0000-0000-000000000001"), "email": "president@society.local", "full_name": "Rajesh Sharma (President)", "account_status": "ACTIVE"},
    {"id": uuid.UUID("e0000000-0000-0000-0000-000000000002"), "email": "treasurer@society.local", "full_name": "Kavita Iyer (Treasurer)", "account_status": "ACTIVE"},
    {"id": uuid.UUID("e0000000-0000-0000-0000-000000000003"), "email": "secretary@society.local", "full_name": "Sunil Verma (Secretary)", "account_status": "ACTIVE"},
    {"id": uuid.UUID("e0000000-0000-0000-0000-000000000004"), "email": "member1@society.local", "full_name": "Arjun Patel (Member 1)", "account_status": "ACTIVE"},
    {"id": uuid.UUID("e0000000-0000-0000-0000-000000000005"), "email": "member2@society.local", "full_name": "Priya Deshmukh (Member 2)", "account_status": "ACTIVE"},
]

MEMBERSHIPS_DATA = [
    {"id": uuid.UUID("f0000000-0000-0000-0000-000000000001"), "society_id": SOCIETY_ID, "user_id": uuid.UUID("e0000000-0000-0000-0000-000000000001"), "member_number": "MEM-001", "status": "ACTIVE"},
    {"id": uuid.UUID("f0000000-0000-0000-0000-000000000002"), "society_id": SOCIETY_ID, "user_id": uuid.UUID("e0000000-0000-0000-0000-000000000002"), "member_number": "MEM-002", "status": "ACTIVE"},
    {"id": uuid.UUID("f0000000-0000-0000-0000-000000000003"), "society_id": SOCIETY_ID, "user_id": uuid.UUID("e0000000-0000-0000-0000-000000000003"), "member_number": "MEM-003", "status": "ACTIVE"},
    {"id": uuid.UUID("f0000000-0000-0000-0000-000000000004"), "society_id": SOCIETY_ID, "user_id": uuid.UUID("e0000000-0000-0000-0000-000000000004"), "member_number": "MEM-004", "status": "ACTIVE"},
    {"id": uuid.UUID("f0000000-0000-0000-0000-000000000005"), "society_id": SOCIETY_ID, "user_id": uuid.UUID("e0000000-0000-0000-0000-000000000005"), "member_number": "MEM-005", "status": "ACTIVE"},
]

MEMBERSHIP_ROLES_DATA = [
    {"membership_id": uuid.UUID("f0000000-0000-0000-0000-000000000001"), "role_id": uuid.UUID("c0000000-0000-0000-0000-000000000001")}, # President
    {"membership_id": uuid.UUID("f0000000-0000-0000-0000-000000000002"), "role_id": uuid.UUID("c0000000-0000-0000-0000-000000000004")}, # Treasurer
    {"membership_id": uuid.UUID("f0000000-0000-0000-0000-000000000003"), "role_id": uuid.UUID("c0000000-0000-0000-0000-000000000003")}, # Secretary
    {"membership_id": uuid.UUID("f0000000-0000-0000-0000-000000000004"), "role_id": uuid.UUID("c0000000-0000-0000-0000-000000000005")}, # Member
    {"membership_id": uuid.UUID("f0000000-0000-0000-0000-000000000005"), "role_id": uuid.UUID("c0000000-0000-0000-0000-000000000005")}, # Member
]


async def seed_database() -> None:
    """Executes idempotent seeding via SQLAlchemy ORM."""
    logger.info("Starting SQLAlchemy database seed routine...")

    async with AsyncSessionLocal() as session:
        # 1. Permissions
        for perm_data in PERMISSIONS_DATA:
            stmt = insert(Permission).values(**perm_data).on_conflict_do_nothing(index_elements=["key"])
            await session.execute(stmt)
        await session.commit()
        logger.info(f"Seeded {len(PERMISSIONS_DATA)} standard permissions.")

        # 2. Demo Society
        stmt = insert(Society).values(
            id=SOCIETY_ID,
            legal_name="Greenwood Mutual Aid & Thrift Society",
            display_name="Greenwood Society",
            registration_number="REG-2026-GW-001",
            address="12 Community Square, Mumbai, MH",
            jurisdiction="Maharashtra, India",
            currency="INR",
            timezone="Asia/Kolkata",
            financial_year_start="04-01",
            status="ACTIVE",
        ).on_conflict_do_nothing(index_elements=["id"])
        await session.execute(stmt)
        await session.commit()
        logger.info("Seeded Greenwood Demo Society.")

        # 3. Standard Roles
        for role_data in ROLES_DATA:
            stmt = insert(Role).values(**role_data).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)
        await session.commit()
        logger.info(f"Seeded {len(ROLES_DATA)} committee roles.")

        # 4. Role Permissions Mapping
        # Fetch all permissions
        result = await session.execute(select(Permission))
        all_perms = {p.key: p.id for p in result.scalars().all()}

        pres_role_id = uuid.UUID("c0000000-0000-0000-0000-000000000001")
        treas_role_id = uuid.UUID("c0000000-0000-0000-0000-000000000004")
        sec_role_id = uuid.UUID("c0000000-0000-0000-0000-000000000003")
        mem_role_id = uuid.UUID("c0000000-0000-0000-0000-000000000005")

        role_perms_to_insert = []
        # President: all permissions
        for pid in all_perms.values():
            role_perms_to_insert.append({"role_id": pres_role_id, "permission_id": pid})

        # Treasurer: Financial + member view + reports + audit
        treasurer_keys = ["contribution:view", "contribution:record", "ledger:view", "ledger:post_entry", "loan:disburse", "loan:view", "report:view", "audit:view", "member:view"]
        for k in treasurer_keys:
            if k in all_perms:
                role_perms_to_insert.append({"role_id": treas_role_id, "permission_id": all_perms[k]})

        # Secretary: Member management + invitations + reports
        sec_keys = ["member:invite", "member:view", "member:update_role", "loan:view", "report:view"]
        for k in sec_keys:
            if k in all_perms:
                role_perms_to_insert.append({"role_id": sec_role_id, "permission_id": all_perms[k]})

        # Member: Apply loan, view own contributions
        mem_keys = ["loan:apply", "loan:view", "contribution:view"]
        for k in mem_keys:
            if k in all_perms:
                role_perms_to_insert.append({"role_id": mem_role_id, "permission_id": all_perms[k]})

        for rp in role_perms_to_insert:
            stmt = insert(RolePermission).values(**rp).on_conflict_do_nothing()
            await session.execute(stmt)
        await session.commit()
        logger.info("Mapped permissions to committee roles.")

        # 5. Chart of Accounts
        for acc_data in ACCOUNTS_DATA:
            stmt = insert(LedgerAccount).values(**acc_data).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)
        await session.commit()
        logger.info(f"Seeded {len(ACCOUNTS_DATA)} chart of accounts.")

        # 6. Users
        for user_data in USERS_DATA:
            stmt = insert(User).values(**user_data).on_conflict_do_nothing(index_elements=["email"])
            await session.execute(stmt)
        await session.commit()
        logger.info(f"Seeded {len(USERS_DATA)} dev users.")

        # 7. Memberships
        for mem_data in MEMBERSHIPS_DATA:
            stmt = insert(SocietyMembership).values(**mem_data).on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)
        await session.commit()
        logger.info(f"Seeded {len(MEMBERSHIPS_DATA)} society memberships.")

        # 8. Membership Roles
        for mr_data in MEMBERSHIP_ROLES_DATA:
            stmt = insert(MembershipRole).values(
                id=uuid.uuid4(),
                membership_id=mr_data["membership_id"],
                role_id=mr_data["role_id"],
            ).on_conflict_do_nothing()
            await session.execute(stmt)
        await session.commit()
        logger.info("Assigned roles to demo society memberships.")

        # 9. Default Policies
        contrib_policy_stmt = insert(ContributionPolicy).values(
            id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
            society_id=SOCIETY_ID,
            amount=2000.0,
            currency="INR",
            frequency="MONTHLY",
            due_day=5,
            grace_period_days=5,
            late_fee=100.0,
            status="ACTIVE",
        ).on_conflict_do_nothing(index_elements=["id"])
        await session.execute(contrib_policy_stmt)

        loan_policy_stmt = insert(LoanPolicy).values(
            id=uuid.UUID("20000000-0000-0000-0000-000000000001"),
            society_id=SOCIETY_ID,
            interest_rate=Decimal("0.0800"),
            interest_period="ANNUAL",
            interest_method="REDUCING_BALANCE",
            calculation_convention="MONTHLY_AMORTIZATION",
            min_amount=10000.0,
            max_amount=100000.0,
            min_tenure_months=1,
            max_tenure_months=24,
            allocation_rule="STRICT_FIFO",
            partial_allocation_allowed=False,
            status="ACTIVE",
        ).on_conflict_do_nothing(index_elements=["id"])
        await session.execute(loan_policy_stmt)
        await session.commit()
        logger.info("Seeded default contribution and loan policies.")

    logger.info("SQLAlchemy seed routine completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
