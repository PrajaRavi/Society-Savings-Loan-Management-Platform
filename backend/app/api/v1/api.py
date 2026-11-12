from fastapi import APIRouter
from app.core.config import settings
from app.api.v1.auth import router as auth_router

api_router = APIRouter()

# Core Authentication & Dev Persona Switcher
api_router.include_router(auth_router)


@api_router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend service readiness."""
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }
