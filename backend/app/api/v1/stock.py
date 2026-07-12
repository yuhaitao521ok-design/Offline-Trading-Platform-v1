import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.schemas.common import ApiError, ApiResponse
from app.schemas.market import FinancialIndicators, KLineBar, StockSearchResult
from app.services.stock_service import StockDataError, StockService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stock", tags=["stock"])
stock_service = StockService()


@router.get("/search", response_model=ApiResponse[list[StockSearchResult]])
async def search_stock_symbols(
    keyword: str = Query(..., min_length=1, examples=["Apple", "Tencent", "600519", "AAPL"]),
    limit: int = Query(default=10, ge=1, le=30),
) -> ApiResponse[list[StockSearchResult]]:
    try:
        data = await stock_service.search_symbols(keyword=keyword, limit=limit)
        return ApiResponse[list[StockSearchResult]](
            success=True,
            data=data,
            error=None,
            timestamp_utc=datetime.now(timezone.utc),
        )
    except StockDataError as exc:
        logger.warning("Symbol search failed: keyword=%s error=%s", keyword, exc)
        raise HTTPException(
            status_code=400,
            detail=ApiError(code="STOCK_SEARCH_ERROR", message=str(exc), details=None).model_dump(mode="json"),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected symbol search error: keyword=%s", keyword)
        raise HTTPException(
            status_code=500,
            detail=ApiError(
                code="STOCK_SEARCH_INTERNAL_ERROR",
                message="Unexpected stock search service error",
                details=None,
            ).model_dump(mode="json"),
        ) from exc


@router.get("/kline", response_model=ApiResponse[list[KLineBar]])
async def get_stock_kline(
    symbol: str = Query(..., min_length=1, examples=["AAPL", "0700.HK", "600519.SH"]),
    period: str = Query(default="1y", examples=["1mo", "3mo", "6mo", "1y", "2y", "5y"]),
) -> ApiResponse[list[KLineBar]]:
    try:
        data = await stock_service.get_history_kline(symbol=symbol, period=period)
        return ApiResponse[list[KLineBar]](
            success=True,
            data=data,
            error=None,
            timestamp_utc=datetime.now(timezone.utc),
        )
    except StockDataError as exc:
        logger.warning("Kline request failed: symbol=%s period=%s error=%s", symbol, period, exc)
        raise HTTPException(
            status_code=400,
            detail=ApiError(code="STOCK_DATA_ERROR", message=str(exc), details=None).model_dump(mode="json"),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected kline request error: symbol=%s period=%s", symbol, period)
        raise HTTPException(
            status_code=500,
            detail=ApiError(
                code="STOCK_DATA_INTERNAL_ERROR",
                message="Unexpected stock kline service error",
                details=None,
            ).model_dump(mode="json"),
        ) from exc


@router.get("/kline/batch", response_model=ApiResponse[dict[str, list[KLineBar]]])
async def get_stock_kline_batch(
    symbols: str = Query(..., min_length=1, examples=["AAPL,MSFT", "0700.HK,9988.HK"]),
    period: str = Query(default="1d", examples=["1d", "1mo", "3mo"]),
    limit: int = Query(default=30, ge=1, le=365),
) -> ApiResponse[dict[str, list[KLineBar]]]:
    symbol_list = [symbol.strip().upper() for symbol in symbols.split(",") if symbol.strip()]
    if not symbol_list:
        raise HTTPException(
            status_code=400,
            detail=ApiError(
                code="INVALID_SYMBOLS",
                message="No valid symbols provided",
                details=None,
            ).model_dump(mode="json"),
        )

    try:
        data: dict[str, list[KLineBar]] = {}
        for symbol in symbol_list:
            bars = await stock_service.get_history_kline(symbol=symbol, period=period)
            data[symbol] = bars[-limit:] if len(bars) > limit else bars
        return ApiResponse[dict[str, list[KLineBar]]](
            success=True,
            data=data,
            error=None,
            timestamp_utc=datetime.now(timezone.utc),
        )
    except StockDataError as exc:
        logger.warning("Batch kline request failed: symbols=%s period=%s error=%s", symbols, period, exc)
        raise HTTPException(
            status_code=400,
            detail=ApiError(code="STOCK_DATA_ERROR", message=str(exc), details=None).model_dump(mode="json"),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected batch kline request error: symbols=%s period=%s", symbols, period)
        raise HTTPException(
            status_code=500,
            detail=ApiError(
                code="STOCK_DATA_INTERNAL_ERROR",
                message="Unexpected batch kline service error",
                details=None,
            ).model_dump(mode="json"),
        ) from exc


@router.get("/finance", response_model=ApiResponse[list[FinancialIndicators]])
async def get_stock_finance(
    symbol: str = Query(..., min_length=1, examples=["AAPL", "0700.HK", "600519.SH"]),
) -> ApiResponse[list[FinancialIndicators]]:
    try:
        data = await stock_service.get_financial_indicators(symbol=symbol)
        return ApiResponse[list[FinancialIndicators]](
            success=True,
            data=data,
            error=None,
            timestamp_utc=datetime.now(timezone.utc),
        )
    except StockDataError as exc:
        logger.warning("Finance request failed: symbol=%s error=%s", symbol, exc)
        raise HTTPException(
            status_code=400,
            detail=ApiError(code="STOCK_DATA_ERROR", message=str(exc), details=None).model_dump(mode="json"),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected finance request error: symbol=%s", symbol)
        raise HTTPException(
            status_code=500,
            detail=ApiError(
                code="STOCK_DATA_INTERNAL_ERROR",
                message="Unexpected stock finance service error",
                details=None,
            ).model_dump(mode="json"),
        ) from exc
