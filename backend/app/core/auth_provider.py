"""Pluggable Authentication Provider Architecture (DummyAuthProvider & SupabaseGoogleAuthProvider)."""
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.core.config import settings


class AuthUser(BaseModel):
    """Represents a verified identity returned by any AuthProvider."""
    id: uuid.UUID
    email: str
    full_name: str
    is_superadmin: bool = False
    provider: str = "dummy"


# Canonical mock dev personas for rapid local RBAC testing
DEV_PERSONAS: Dict[str, Dict] = {
    "admin@platform.local": {
        "id": uuid.UUID("e0000000-0000-0000-0000-000000000000"),
        "email": "admin@platform.local",
        "full_name": "Platform Super Administrator",
        "role_title": "Super Admin",
        "role_description": "Platform operator with global configuration controls",
        "avatar_badge": "🛠️",
        "is_superadmin": True,
    },
    "president@society.local": {
        "id": uuid.UUID("e0000000-0000-0000-0000-000000000001"),
        "email": "president@society.local",
        "full_name": "Rajesh Sharma (President)",
        "role_title": "President",
        "role_description": "Society head with loan approval and executive oversight",
        "avatar_badge": "👑",
        "is_superadmin": False,
    },
    "treasurer@society.local": {
        "id": uuid.UUID("e0000000-0000-0000-0000-000000000002"),
        "email": "treasurer@society.local",
        "full_name": "Kavita Iyer (Treasurer)",
        "role_title": "Treasurer",
        "role_description": "Financial custodian: collections, ledger, and disbursements",
        "avatar_badge": "💰",
        "is_superadmin": False,
    },
    "secretary@society.local": {
        "id": uuid.UUID("e0000000-0000-0000-0000-000000000003"),
        "email": "secretary@society.local",
        "full_name": "Sunil Verma (Secretary)",
        "role_title": "Secretary",
        "role_description": "Administrative manager: memberships, notices, and invites",
        "avatar_badge": "📝",
        "is_superadmin": False,
    },
    "member1@society.local": {
        "id": uuid.UUID("e0000000-0000-0000-0000-000000000004"),
        "email": "member1@society.local",
        "full_name": "Arjun Patel (Member 1)",
        "role_title": "Member",
        "role_description": "Active contributor and first FIFO loan applicant",
        "avatar_badge": "👤",
        "is_superadmin": False,
    },
    "member2@society.local": {
        "id": uuid.UUID("e0000000-0000-0000-0000-000000000005"),
        "email": "member2@society.local",
        "full_name": "Priya Deshmukh (Member 2)",
        "role_title": "Member",
        "role_description": "Active contributor and second FIFO loan applicant",
        "avatar_badge": "👤",
        "is_superadmin": False,
    },
}

DEFAULT_DEV_USER_EMAIL = "president@society.local"


class AuthProvider(ABC):
    """Abstract interface defining required authentication behaviors."""

    @abstractmethod
    async def authenticate_request(
        self, dev_header: Optional[str] = None, bearer_token: Optional[str] = None
    ) -> Optional[AuthUser]:
        """Resolves an AuthUser from headers/tokens or returns None if unauthenticated."""
        pass

    @abstractmethod
    def list_dev_personas(self) -> List[Dict]:
        """Returns available mock personas for the UI switcher."""
        pass


class DummyAuthProvider(AuthProvider):
    """Local Development AuthProvider with instant persona switching without credentials."""

    async def authenticate_request(
        self, dev_header: Optional[str] = None, bearer_token: Optional[str] = None
    ) -> Optional[AuthUser]:
        target_email: Optional[str] = None

        # 1. Inspect X-Dev-User header first
        if dev_header and dev_header.strip():
            target_email = dev_header.strip().lower()

        # 2. Inspect Bearer token (format: "Bearer dev:<email>" or standard token)
        elif bearer_token and bearer_token.strip():
            token_clean = bearer_token.replace("Bearer ", "").strip()
            if token_clean.startswith("dev:"):
                target_email = token_clean.replace("dev:", "").strip().lower()
            elif token_clean in DEV_PERSONAS:
                target_email = token_clean.lower()

        # 3. Fallback default in development if neither is provided
        if not target_email:
            target_email = DEFAULT_DEV_USER_EMAIL

        persona = DEV_PERSONAS.get(target_email)
        if not persona:
            # Allow arbitrary dev emails on the fly
            new_id = uuid.uuid5(uuid.NAMESPACE_DNS, target_email)
            return AuthUser(
                id=new_id,
                email=target_email,
                full_name=target_email.split("@")[0].replace(".", " ").title(),
                is_superadmin=(target_email == "admin@platform.local"),
                provider="dummy",
            )

        return AuthUser(
            id=persona["id"],
            email=persona["email"],
            full_name=persona["full_name"],
            is_superadmin=persona["is_superadmin"],
            provider="dummy",
        )

    def list_dev_personas(self) -> List[Dict]:
        return list(DEV_PERSONAS.values())


class SupabaseGoogleAuthProvider(AuthProvider):
    """Production AuthProvider verifying Google OAuth tokens issued via Supabase."""

    async def authenticate_request(
        self, dev_header: Optional[str] = None, bearer_token: Optional[str] = None
    ) -> Optional[AuthUser]:
        if not bearer_token:
            return None
        token = bearer_token.replace("Bearer ", "").strip()
        try:
            from jose import jwt
            # Decodes Supabase JWT containing Google claims (sub, email, user_metadata)
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            user_id = uuid.UUID(payload.get("sub"))
            email = payload.get("email", "")
            metadata = payload.get("user_metadata", {})
            full_name = metadata.get("full_name") or metadata.get("name") or email
            return AuthUser(
                id=user_id,
                email=email,
                full_name=full_name,
                is_superadmin=payload.get("is_superadmin", False),
                provider="supabase_google",
            )
        except Exception:
            return None

    def list_dev_personas(self) -> List[Dict]:
        return []


def get_auth_provider() -> AuthProvider:
    """Factory creating configured AuthProvider based on settings.AUTH_MODE."""
    if settings.AUTH_MODE.lower() in ("supabase_google", "google", "production"):
        return SupabaseGoogleAuthProvider()
    return DummyAuthProvider()
