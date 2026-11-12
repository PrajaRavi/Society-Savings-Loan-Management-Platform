"""FastAPI dependencies for Authentication, Tenant Scoping, and RBAC authorization."""
import uuid
from typing import Callable, List, Optional
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth_provider import AuthUser, get_auth_provider
from app.core.database import get_db
from app.models.identity import MembershipRole, Role, Society, SocietyMembership, User


async def get_auth_user(
    request: Request,
    x_dev_user: Optional[str] = Header(None, alias="X-Dev-User"),
    authorization: Optional[str] = Header(None),
) -> AuthUser:
    """Extracts and verifies raw authentication identity using the configured AuthProvider."""
    provider = get_auth_provider()
    auth_user = await provider.authenticate_request(
        dev_header=x_dev_user,
        bearer_token=authorization,
    )
    if not auth_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid token or X-Dev-User persona.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_user


async def get_current_user(
    auth_user: AuthUser = Depends(get_auth_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolves and ensures the database User record matching the authenticated identity."""
    try:
        stmt = (
            select(User)
            .where((User.id == auth_user.id) | (User.email == auth_user.email))
            .options(
                selectinload(User.memberships).selectinload(SocietyMembership.membership_roles).selectinload(MembershipRole.role),
                selectinload(User.memberships).selectinload(SocietyMembership.society),
            )
        )
        result = await db.execute(stmt)
        user = result.scalars().first()

        # In development mode, auto-provision the dev user in DB if it was not seeded yet
        if not user:
            user = User(
                id=auth_user.id,
                email=auth_user.email,
                full_name=auth_user.full_name,
                account_status="ACTIVE",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        if user.account_status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User account is {user.account_status}. Please contact support.",
            )

        return user
    except HTTPException:
        raise
    except Exception as exc:
        # If DB connection is temporarily unreachable in dummy dev mode, provide fallback persona
        from app.core.config import settings
        from app.core.auth_provider import DEV_PERSONAS
        if settings.AUTH_MODE == "dummy":
            persona = DEV_PERSONAS.get(auth_user.email.lower(), {})
            demo_society = Society(
                id=uuid.UUID("a0000000-0000-0000-0000-000000000001"),
                legal_name="Greenwood Mutual Aid & Thrift Society",
                display_name="Greenwood Society",
                currency="INR",
                timezone="Asia/Kolkata",
                status="ACTIVE",
            )
            role_title = persona.get("role_title", "Member")
            role_obj = Role(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, role_title),
                name=role_title,
                is_system=True,
            )
            mem_role = MembershipRole(
                id=uuid.uuid4(),
                role=role_obj,
            )
            membership = SocietyMembership(
                id=uuid.uuid5(uuid.NAMESPACE_DNS, f"{auth_user.email}:a0000000-0000-0000-0000-000000000001"),
                society_id=demo_society.id,
                user_id=auth_user.id,
                society=demo_society,
                member_number="MEM-DEV",
                status="ACTIVE",
                membership_roles=[mem_role],
            )
            synth_user = User(
                id=auth_user.id,
                email=auth_user.email,
                full_name=auth_user.full_name,
                account_status="ACTIVE",
                memberships=[membership],
            )
            return synth_user
        raise


async def get_current_membership(
    society_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SocietyMembership:
    """
    Enforces multi-tenant boundary: verifies the user holds an active membership
    in the requested society.
    """
    stmt = (
        select(SocietyMembership)
        .where(
            SocietyMembership.society_id == society_id,
            SocietyMembership.user_id == current_user.id,
        )
        .options(
            selectinload(SocietyMembership.membership_roles).selectinload(MembershipRole.role),
            selectinload(SocietyMembership.society),
        )
    )
    result = await db.execute(stmt)
    membership = result.scalars().first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a registered member of this society.",
        )

    if membership.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Your membership is currently {membership.status}.",
        )

    return membership


def require_society_role(allowed_roles: List[str]) -> Callable:
    """
    RBAC dependency factory.
    Enforces that the authenticated member holds at least one of the required committee roles.
    """
    async def role_checker(
        membership: SocietyMembership = Depends(get_current_membership),
        current_user: User = Depends(get_current_user),
    ) -> SocietyMembership:
        # Platform superadmin bypass
        if current_user.email == "admin@platform.local":
            return membership

        user_roles = [
            mr.role.name.lower()
            for mr in membership.membership_roles
            if mr.role and mr.effective_to is None
        ]
        allowed_normalized = [r.lower() for r in allowed_roles]

        has_permission = any(role in allowed_normalized for role in user_roles)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of the following roles: {', '.join(allowed_roles)}. Your current roles: {', '.join(user_roles) or 'None'}.",
            )
        return membership

    return role_checker
