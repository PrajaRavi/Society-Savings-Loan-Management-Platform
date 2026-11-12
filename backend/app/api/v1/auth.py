"""Authentication endpoints."""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.auth_provider import DEV_PERSONAS, get_auth_provider
from app.core.database import get_db
from app.models.identity import User
from app.schemas.auth import (
    DevLoginRequest,
    DevUser,
    SocietyMembershipSummary,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def build_user_response(user: User) -> UserResponse:
    """Helper to assemble a clean UserResponse with memberships and roles."""
    memberships_summary = []
    for m in user.memberships:
        active_roles = [
            mr.role.name
            for mr in m.membership_roles
            if mr.role and mr.effective_to is None
        ]
        memberships_summary.append(
            SocietyMembershipSummary(
                id=m.id,
                society_id=m.society_id,
                society_name=m.society.display_name if m.society else None,
                member_number=m.member_number,
                status=m.status,
                roles=active_roles,
            )
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        account_status=user.account_status,
        created_at=user.created_at or datetime.now(),
        memberships=memberships_summary,
    )


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Returns the authenticated user's profile and active society memberships."""
    return build_user_response(current_user)


@router.get("/dev-users", response_model=List[DevUser])
async def list_dev_personas() -> List[DevUser]:
    """Lists available pre-configured development personas for quick local switching."""
    provider = get_auth_provider()
    personas = provider.list_dev_personas()
    return [DevUser(**p) for p in personas]


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(
    payload: DevLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Simulates instant login as any dev persona, returning a bearer token and user DTO."""
    persona = DEV_PERSONAS.get(payload.email.lower())
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona '{payload.email}' not found. Available personas: {', '.join(DEV_PERSONAS.keys())}",
        )

    # Use existing current user resolution logic
    from app.core.auth_provider import AuthUser
    auth_user = AuthUser(
        id=persona["id"],
        email=persona["email"],
        full_name=persona["full_name"],
        is_superadmin=persona["is_superadmin"],
        provider="dummy",
    )
    user = await get_current_user(auth_user=auth_user, db=db)
    
    return TokenResponse(
        access_token=f"dev:{user.email}",
        token_type="bearer",
        user=build_user_response(user),
    )
