"""Tests for Pluggable Authentication, Dev Personas, and RBAC Guards."""
import pytest
import uuid
from httpx import AsyncClient
from fastapi import FastAPI, Depends, APIRouter
from app.api.deps import require_society_role, get_current_membership
from app.models.identity import SocietyMembership


DEMO_SOCIETY_ID = "a0000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_list_dev_users(async_client: AsyncClient):
    """Verify endpoint lists all configured development personas."""
    response = await async_client.get("/api/v1/auth/dev-users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    emails = [u["email"] for u in data]
    assert "president@society.local" in emails
    assert "treasurer@society.local" in emails
    assert "secretary@society.local" in emails
    assert "member1@society.local" in emails
    assert "member2@society.local" in emails
    assert "admin@platform.local" in emails


@pytest.mark.asyncio
async def test_get_current_user_default(async_client: AsyncClient):
    """Verify default persona is President when no auth headers are provided."""
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "president@society.local"
    assert "President" in data["full_name"]


@pytest.mark.asyncio
async def test_switch_persona_via_header(async_client: AsyncClient):
    """Verify X-Dev-User switches identity dynamically with zero credentials."""
    # 1. Switch to Treasurer
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"X-Dev-User": "treasurer@society.local"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "treasurer@society.local"
    assert "Treasurer" in data["full_name"]

    # 2. Switch to Member 1
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"X-Dev-User": "member1@society.local"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "member1@society.local"
    assert "Arjun Patel" in data["full_name"]


@pytest.mark.asyncio
async def test_bearer_token_dev_auth(async_client: AsyncClient):
    """Verify Authorization: Bearer dev:<email> works identically to dev header."""
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer dev:secretary@society.local"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "secretary@society.local"
    assert "Secretary" in data["full_name"]


@pytest.mark.asyncio
async def test_dev_login_endpoint(async_client: AsyncClient):
    """Verify /auth/dev-login generates token and user object."""
    response = await async_client.post(
        "/api/v1/auth/dev-login",
        json={"email": "president@society.local"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"] == "dev:president@society.local"
    assert data["user"]["email"] == "president@society.local"
