from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


MarketCode = Literal["CN", "HK", "US"]


class KLineBar(BaseModel):
    timestamp_utc: datetime = Field(..., description="K line timestamp stored in UTC")
    open: Decimal = Field(..., ge=0)
    high: Decimal = Field(..., ge=0)
    low: Decimal = Field(..., ge=0)
    close: Decimal = Field(..., ge=0)
    volume: int = Field(..., ge=0)

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda value: float(value),
            datetime: lambda value: value.isoformat().replace("+00:00", "Z"),
        },
    )

    @field_validator("timestamp_utc")
    @classmethod
    def validate_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp_utc must be timezone-aware")

        if value.utcoffset() is None:
            raise ValueError("timestamp_utc must have a valid UTC offset")

        return value.astimezone(timezone.utc)


class FinancialIndicators(BaseModel):
    period: str = Field(..., description="Financial period label, such as 2024 or 2024Q4")
    report_type: Literal["annual", "quarterly"] = Field(default="annual")
    roe: Decimal | None = Field(default=None, description="Return on equity, decimal ratio")
    roic: Decimal | None = Field(default=None, description="Return on invested capital, decimal ratio")
    revenue: Decimal | None = Field(default=None, ge=0)
    net_profit: Decimal | None = Field(default=None)
    gross_margin: Decimal | None = Field(default=None, description="Gross margin, decimal ratio")
    net_margin: Decimal | None = Field(default=None, description="Net margin, decimal ratio")

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda value: float(value),
        },
    )


class StockDetailResponse(BaseModel):
    symbol: str = Field(..., examples=["600519.SH", "0700.HK", "AAPL"])
    market: MarketCode
    currency: str | None = Field(default=None, examples=["CNY", "HKD", "USD"])
    name: str | None = Field(default=None)
    kline: list[KLineBar] = Field(default_factory=list)
    financial_indicators: list[FinancialIndicators] = Field(default_factory=list)


class StockSearchResult(BaseModel):
    symbol: str = Field(..., examples=["600519.SH", "0700.HK", "AAPL"])
    name: str = Field(..., examples=["Kweichow Moutai", "Tencent Holdings", "Apple Inc."])
    market: MarketCode
    currency: str | None = Field(default=None, examples=["CNY", "HKD", "USD"])
    source: str = Field(..., examples=["akshare", "yfinance"])
