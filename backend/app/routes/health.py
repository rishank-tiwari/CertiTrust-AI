"""
Health Check Router Module.
Provides health monitoring endpoints for system status.
"""

from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Root Health Status Endpoint",
    description="Returns current project name and running status.",
)
async def get_root_health() -> HealthResponse:
    """
    Root health endpoint returning system metadata.
    """
    return HealthResponse(
        project=settings.PROJECT_NAME,
        status="running",
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Detailed System Health Check",
)
async def get_health_check() -> HealthResponse:
    """
    Health check endpoint under API v1 prefix.
    """
    return HealthResponse(
        project=settings.PROJECT_NAME,
        status="running",
    )
