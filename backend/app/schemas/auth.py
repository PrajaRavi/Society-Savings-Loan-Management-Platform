"""Authentication and user DTO schemas."""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_system: bool = False
    model_config = ConfigDict(from_attributes=True)



class SocietyMembershipSummary(BaseModel):
    id: uuid.UUID
    society_id: uuid.UUID
    society_name: Optional[str] = None
    member_number: Optional[str] = None
    status: str
    roles: List[str] = []
    model_config = ConfigDict(from_attributes=True) #! tells Pydantic to read data from an object's attributes instead of expecting only a dictionary.



class UserResponse(BaseModel):
    id: uuid.UUID
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: str
    account_status: str
    created_at: Optional[datetime] = None
    memberships: List[SocietyMembershipSummary] = []
    model_config = ConfigDict(from_attributes=True)



class DevUser(BaseModel):
    email: str
    full_name: str
    role_title: str
    role_description: str
    avatar_badge: str
    is_superadmin: bool = False


class DevLoginRequest(BaseModel):
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
