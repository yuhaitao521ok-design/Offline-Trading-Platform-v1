from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import ApiResponse, HealthStatus


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse[HealthStatus])
async def health_check() -> ApiResponse[HealthStatus]:
    settings = get_settings()
    now_utc = datetime.now(timezone.utc)

    return ApiResponse[HealthStatus](
        success=True,
        data=HealthStatus(
            status="ok",
            app_name=settings.app_name,
            app_env=settings.app_env,
            app_version=settings.app_version,
            server_time_utc=now_utc,
        ),
        error=None,
        timestamp_utc=now_utc,
    )
