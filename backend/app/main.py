import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.stock import router as stock_router
from app.core.config import get_settings
from app.schemas.common import ApiError, ApiResponse


settings = get_settings()
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


def create_app() -> FastAPI:
    api = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )

    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent"],
    )

    @api.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        now_utc = datetime.now(timezone.utc)
        payload = ApiResponse[None](
            success=False,
            data=None,
            error=ApiError(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"path": str(request.url.path), "errors": exc.errors()},
            ),
            timestamp_utc=now_utc,
        )
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    @api.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        now_utc = datetime.now(timezone.utc)
        payload = ApiResponse[None](
            success=False,
            data=None,
            error=ApiError(
                code="INTERNAL_SERVER_ERROR",
                message="Internal server error",
                details={"path": str(request.url.path)} if settings.debug else None,
            ),
            timestamp_utc=now_utc,
        )
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))

    @api.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        now_utc = datetime.now(timezone.utc)
        detail = exc.detail
        if isinstance(detail, dict) and {"code", "message"}.issubset(detail.keys()):
            error = ApiError.model_validate(detail)
        else:
            error = ApiError(
                code="HTTP_ERROR",
                message=str(detail),
                details={"path": str(request.url.path)},
            )

        payload = ApiResponse[None](
            success=False,
            data=None,
            error=error,
            timestamp_utc=now_utc,
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    api.include_router(health_router, prefix=settings.api_v1_prefix)
    api.include_router(stock_router, prefix=settings.api_v1_prefix)

    return api


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
