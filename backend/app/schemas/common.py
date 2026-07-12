from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class ApiError(BaseModel):
    code: str = Field(..., examples=["VALIDATION_ERROR"])
    message: str = Field(..., examples=["Request validation failed"])
    details: dict[str, object] | list[object] | None = Field(default=None)


class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(..., examples=[True])
    data: T | None = Field(default=None)
    error: ApiError | None = Field(default=None)
    timestamp_utc: datetime = Field(..., description="Server response time in UTC")

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda value: value.isoformat().replace("+00:00", "Z"),
        },
    )


class HealthStatus(BaseModel):
    status: str = Field(..., examples=["ok"])
    app_name: str = Field(..., examples=["Offline Trading Platform API"])
    app_env: str = Field(..., examples=["development"])
    app_version: str = Field(..., examples=["0.1.0"])
    server_time_utc: datetime = Field(..., description="Current server time in UTC")
