import asyncio
import logging
import math
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

import pandas as pd

from app.schemas.market import FinancialIndicators, KLineBar, MarketCode, StockSearchResult

logger = logging.getLogger(__name__)
YFINANCE_CACHE_DIR = Path(tempfile.gettempdir()) / "offline_trading_platform" / "yfinance"


class StockDataError(RuntimeError):
    pass


@dataclass(frozen=True)
class LocalStockEntry:
    symbol: str
    name: str
    market: MarketCode
    currency: str
    aliases: tuple[str, ...]


LOCAL_STOCK_CATALOG: tuple[LocalStockEntry, ...] = (
    LocalStockEntry("AAPL", "Apple Inc. \u82f9\u679c", "US", "USD", ("apple", "pingguo", "iphone", "苹果")),
    LocalStockEntry("MSFT", "Microsoft Corporation \u5fae\u8f6f", "US", "USD", ("microsoft", "weiruan", "windows", "azure", "微软")),
    LocalStockEntry("NVDA", "NVIDIA Corporation \u82f1\u4f1f\u8fbe", "US", "USD", ("nvidia", "yingweida", "gpu", "英伟达")),
    LocalStockEntry("TSLA", "Tesla Inc. \u7279\u65af\u62c9", "US", "USD", ("tesla", "tesila", "elon", "特斯拉")),
    LocalStockEntry("AMZN", "Amazon.com Inc. \u4e9a\u9a6c\u900a", "US", "USD", ("amazon", "yamaxun", "aws", "亚马逊")),
    LocalStockEntry("GOOGL", "Alphabet Inc. \u8c37\u6b4c", "US", "USD", ("google", "alphabet", "guge", "谷歌")),
    LocalStockEntry("META", "Meta Platforms Inc.", "US", "USD", ("meta", "facebook", "fb")),
    LocalStockEntry("AMD", "Advanced Micro Devices Inc.", "US", "USD", ("amd", "advanced micro devices", "超威")),
    LocalStockEntry("NFLX", "Netflix Inc. \u5948\u98de", "US", "USD", ("netflix", "naifei", "奈飞")),
    LocalStockEntry("JPM", "JPMorgan Chase & Co. \u6469\u6839\u5927\u901a", "US", "USD", ("jpmorgan", "jp morgan", "mogen datong", "摩根大通")),
    LocalStockEntry("BAC", "Bank of America \u7f8e\u56fd\u94f6\u884c", "US", "USD", ("bank of america", "boa", "meiguo yinhang", "美国银行")),
    LocalStockEntry("V", "Visa Inc.", "US", "USD", ("visa", "维萨")),
    LocalStockEntry("MA", "Mastercard Incorporated", "US", "USD", ("mastercard", "万事达")),
    LocalStockEntry("BRK-B", "Berkshire Hathaway", "US", "USD", ("berkshire", "buffett", "巴菲特", "伯克希尔")),
    LocalStockEntry("UNH", "UnitedHealth Group", "US", "USD", ("unitedhealth", "united health", "联合健康")),
    LocalStockEntry("LLY", "Eli Lilly and Company \u793c\u6765", "US", "USD", ("eli lilly", "lilly", "lilai", "礼来")),
    LocalStockEntry("XOM", "Exxon Mobil Corporation \u57c3\u514b\u68ee\u7f8e\u5b5a", "US", "USD", ("exxon", "mobil", "aikesen", "埃克森")),
    LocalStockEntry("WMT", "Walmart Inc. \u6c83\u5c14\u739b", "US", "USD", ("walmart", "woerma", "沃尔玛")),
    LocalStockEntry("COST", "Costco Wholesale", "US", "USD", ("costco", "好市多")),
    LocalStockEntry("KO", "Coca-Cola Company \u53ef\u53e3\u53ef\u4e50", "US", "USD", ("coca cola", "coke", "kekoukele", "可口可乐")),
    LocalStockEntry("PEP", "PepsiCo Inc. \u767e\u4e8b", "US", "USD", ("pepsi", "pepsico", "baishi", "百事")),
    LocalStockEntry("MCD", "McDonald's Corporation \u9ea6\u5f53\u52b3", "US", "USD", ("mcdonald", "maidanglao", "麦当劳")),
    LocalStockEntry("DIS", "Walt Disney Company \u8fea\u58eb\u5c3c", "US", "USD", ("disney", "dishini", "迪士尼")),
    LocalStockEntry("CRM", "Salesforce Inc.", "US", "USD", ("salesforce", "crm")),
    LocalStockEntry("ORCL", "Oracle Corporation \u7532\u9aa8\u6587", "US", "USD", ("oracle", "jiaguwen", "甲骨文")),
    LocalStockEntry("INTC", "Intel Corporation \u82f1\u7279\u5c14", "US", "USD", ("intel", "yingteer", "英特尔")),
    LocalStockEntry("0700.HK", "Tencent Holdings \u817e\u8baf\u63a7\u80a1", "HK", "HKD", ("tencent", "tengxun", "wechat", "weixin", "腾讯", "微信")),
    LocalStockEntry("9988.HK", "Alibaba Group \u963f\u91cc\u5df4\u5df4", "HK", "HKD", ("alibaba", "ali", "alibab", "阿里", "阿里巴巴")),
    LocalStockEntry("3690.HK", "Meituan \u7f8e\u56e2", "HK", "HKD", ("meituan", "meituan dianping", "美团")),
    LocalStockEntry("1810.HK", "Xiaomi \u5c0f\u7c73\u96c6\u56e2", "HK", "HKD", ("xiaomi", "mi", "leijun", "小米", "雷军")),
    LocalStockEntry("9618.HK", "JD.com \u4eac\u4e1c", "HK", "HKD", ("jd", "jd.com", "jingdong", "京东")),
    LocalStockEntry("1299.HK", "AIA Group \u53cb\u90a6\u4fdd\u9669", "HK", "HKD", ("aia", "youbang", "友邦")),
    LocalStockEntry("0005.HK", "HSBC Holdings \u6c47\u4e30\u63a7\u80a1", "HK", "HKD", ("hsbc", "huifeng", "汇丰")),
    LocalStockEntry("0939.HK", "China Construction Bank \u5efa\u8bbe\u94f6\u884c", "HK", "HKD", ("ccb", "jianshe yinhang", "建设银行", "建行")),
    LocalStockEntry("1398.HK", "ICBC \u5de5\u5546\u94f6\u884c", "HK", "HKD", ("icbc", "gongshang yinhang", "工商银行", "工行")),
    LocalStockEntry("3988.HK", "Bank of China \u4e2d\u56fd\u94f6\u884c", "HK", "HKD", ("boc", "bank of china", "zhongguo yinhang", "中国银行", "中行")),
    LocalStockEntry("2318.HK", "Ping An Insurance \u4e2d\u56fd\u5e73\u5b89", "HK", "HKD", ("ping an", "pingan", "中国平安", "平安")),
    LocalStockEntry("0883.HK", "CNOOC \u4e2d\u56fd\u6d77\u6d0b\u77f3\u6cb9", "HK", "HKD", ("cnooc", "zhonghaiyou", "中国海油", "中海油")),
    LocalStockEntry("0857.HK", "PetroChina \u4e2d\u56fd\u77f3\u6cb9", "HK", "HKD", ("petrochina", "zhongshiyou", "中国石油", "中石油")),
    LocalStockEntry("0388.HK", "HKEX \u9999\u6e2f\u4ea4\u6613\u6240", "HK", "HKD", ("hkex", "hong kong exchange", "gangjiao suo", "港交所", "香港交易所")),
    LocalStockEntry("1211.HK", "BYD Company \u6bd4\u4e9a\u8fea", "HK", "HKD", ("byd", "biyadi", "比亚迪")),
    LocalStockEntry("600519.SH", "Kweichow Moutai \u8d35\u5dde\u8305\u53f0", "CN", "CNY", ("moutai", "maotai", "kweichow moutai", "guizhou maotai", "贵州茅台", "茅台")),
    LocalStockEntry("000858.SZ", "Wuliangye \u4e94\u7cae\u6db2", "CN", "CNY", ("wuliangye", "五粮液")),
    LocalStockEntry("300750.SZ", "CATL \u5b81\u5fb7\u65f6\u4ee3", "CN", "CNY", ("catl", "ningde shidai", "宁德时代")),
    LocalStockEntry("601318.SH", "Ping An Insurance \u4e2d\u56fd\u5e73\u5b89", "CN", "CNY", ("ping an", "pingan", "中国平安", "平安")),
    LocalStockEntry("600036.SH", "China Merchants Bank \u62db\u5546\u94f6\u884c", "CN", "CNY", ("cmb", "zhaoshang yinhang", "招商银行", "招行")),
    LocalStockEntry("000001.SZ", "Ping An Bank \u5e73\u5b89\u94f6\u884c", "CN", "CNY", ("ping an bank", "pingan bank", "平安银行")),
    LocalStockEntry("600276.SH", "Hengrui Medicine \u6052\u745e\u533b\u836f", "CN", "CNY", ("hengrui", "hengrui medicine", "恒瑞医药", "恒瑞")),
    LocalStockEntry("002594.SZ", "BYD \u6bd4\u4e9a\u8fea", "CN", "CNY", ("byd", "biyadi", "比亚迪")),
    LocalStockEntry("600030.SH", "CITIC Securities \u4e2d\u4fe1\u8bc1\u5238", "CN", "CNY", ("citic securities", "zhongxin zhengquan", "中信证券")),
    LocalStockEntry("601166.SH", "Industrial Bank \u5174\u4e1a\u94f6\u884c", "CN", "CNY", ("industrial bank", "xingye yinhang", "兴业银行")),
    LocalStockEntry("600900.SH", "China Yangtze Power \u957f\u6c5f\u7535\u529b", "CN", "CNY", ("yangtze power", "changjiang dianli", "长江电力")),
    LocalStockEntry("601398.SH", "ICBC \u5de5\u5546\u94f6\u884c", "CN", "CNY", ("icbc", "gongshang yinhang", "工商银行", "工行")),
    LocalStockEntry("601939.SH", "China Construction Bank \u5efa\u8bbe\u94f6\u884c", "CN", "CNY", ("ccb", "jianshe yinhang", "建设银行", "建行")),
    LocalStockEntry("601288.SH", "Agricultural Bank of China \u519c\u4e1a\u94f6\u884c", "CN", "CNY", ("abc", "nongye yinhang", "农业银行", "农行")),
    LocalStockEntry("601988.SH", "Bank of China \u4e2d\u56fd\u94f6\u884c", "CN", "CNY", ("boc", "zhongguo yinhang", "中国银行", "中行")),
    LocalStockEntry("600887.SH", "Yili \u4f0a\u5229\u80a1\u4efd", "CN", "CNY", ("yili", "伊利", "伊利股份")),
    LocalStockEntry("000333.SZ", "Midea Group \u7f8e\u7684\u96c6\u56e2", "CN", "CNY", ("midea", "meide", "美的", "美的集团")),
    LocalStockEntry("000651.SZ", "Gree Electric \u683c\u529b\u7535\u5668", "CN", "CNY", ("gree", "geli", "格力", "格力电器")),
    LocalStockEntry("300760.SZ", "Mindray Medical \u8fc8\u745e\u533b\u7597", "CN", "CNY", ("mindray", "mairui", "迈瑞医疗", "迈瑞")),
    LocalStockEntry("600406.SH", "NARI Technology \u56fd\u7535\u5357\u745e", "CN", "CNY", ("nari", "guodian nanrui", "国电南瑞")),
    LocalStockEntry("600309.SH", "Wanhua Chemical \u4e07\u534e\u5316\u5b66", "CN", "CNY", ("wanhua", "wanhua chemical", "万华化学")),
    LocalStockEntry("601899.SH", "Zijin Mining \u7d2b\u91d1\u77ff\u4e1a", "CN", "CNY", ("zijin mining", "zijin", "紫金矿业")),
)


@dataclass(frozen=True)
class SymbolMeta:
    original_symbol: str
    market: MarketCode
    akshare_symbol: str | None
    yfinance_symbol: str
    timezone_name: str
    currency: str | None


class StockService:
    async def search_symbols(self, keyword: str, limit: int = 10) -> list[StockSearchResult]:
        normalized_keyword = keyword.strip()
        if not normalized_keyword:
            raise StockDataError("keyword must not be empty")

        bounded_limit = max(1, min(limit, 30))
        local_matches = self._search_local_symbol_catalog(normalized_keyword, bounded_limit)
        if local_matches:
            return local_matches

        direct_match = self._try_direct_symbol_match(normalized_keyword)
        if direct_match is not None:
            return [direct_match]

        return []

    async def get_history_kline(self, symbol: str, period: str = "1y") -> list[KLineBar]:
        meta = self._parse_symbol(symbol)
        normalized_period = self._normalize_period(period)

        try:
            if meta.market == "CN":
                frame = await asyncio.to_thread(self._fetch_akshare_kline, meta, normalized_period)
            else:
                frame = await asyncio.to_thread(self._fetch_yfinance_kline, meta, normalized_period)
            return self._frame_to_kline_bars(frame, meta)
        except StockDataError:
            raise
        except Exception as exc:
            logger.exception("Failed to fetch kline data for symbol=%s period=%s", symbol, period)
            if self._is_network_error(exc):
                raise StockDataError(
                    f"Unable to connect to the external market data provider for {symbol}. "
                    "Please check network access to Yahoo Finance or try again later."
                ) from exc
            raise StockDataError(f"Failed to fetch kline data for {symbol}") from exc

    async def get_financial_indicators(self, symbol: str) -> list[FinancialIndicators]:
        meta = self._parse_symbol(symbol)

        try:
            if meta.market == "CN":
                indicators = await asyncio.to_thread(self._fetch_akshare_financial_indicators, meta)
                if indicators:
                    return indicators
            return await asyncio.to_thread(self._fetch_yfinance_financial_indicators, meta)
        except StockDataError:
            raise
        except Exception as exc:
            logger.exception("Failed to fetch financial indicators for symbol=%s", symbol)
            if self._is_network_error(exc):
                raise StockDataError(
                    f"Unable to connect to the external financial data provider for {symbol}. "
                    "Please check network access to Yahoo Finance or try again later."
                ) from exc
            raise StockDataError(f"Failed to fetch financial indicators for {symbol}") from exc

    def _parse_symbol(self, symbol: str) -> SymbolMeta:
        normalized = symbol.strip().upper()
        if not normalized:
            raise StockDataError("symbol must not be empty")

        if normalized.endswith(".SH"):
            code = normalized.removesuffix(".SH")
            return SymbolMeta(normalized, "CN", code, f"{code}.SS", "Asia/Shanghai", "CNY")

        if normalized.endswith(".SZ"):
            code = normalized.removesuffix(".SZ")
            return SymbolMeta(normalized, "CN", code, f"{code}.SZ", "Asia/Shanghai", "CNY")

        if normalized.endswith(".HK"):
            code = normalized.removesuffix(".HK").zfill(4)
            return SymbolMeta(normalized, "HK", None, f"{code}.HK", "Asia/Hong_Kong", "HKD")

        if "." in normalized:
            raise StockDataError("Unsupported symbol suffix. Use .SH, .SZ, .HK, or a US ticker like AAPL")

        return SymbolMeta(normalized, "US", None, normalized, "America/New_York", "USD")

    def _normalize_period(self, period: str) -> str:
        normalized = period.strip().lower()
        allowed = {
            # Minute intervals
            "1m", "5m",
            # Hour intervals
            "1h", "4h",
            # Day intervals
            "1d",
            # Month and range periods
            "1mo", "3mo", "6mo", "1y", "2y", "3y", "5y", "10y", "max"
        }
        if normalized not in allowed:
            raise StockDataError(f"Unsupported period: {period}. Allowed: {', '.join(sorted(allowed))}")
        return normalized

    def _fetch_akshare_kline(self, meta: SymbolMeta, period: str) -> pd.DataFrame:
        import akshare as ak

        if meta.akshare_symbol is None:
            raise StockDataError("AkShare symbol is required for A-share data")

        # AkShare only supports daily data, so only allow day and above periods
        if period not in {"1d", "1mo", "3mo", "6mo", "1y", "2y", "3y", "5y", "10y", "max"}:
            raise StockDataError(f"AkShare only supports daily data. Got period: {period}")

        frame = ak.stock_zh_a_hist(
            symbol=meta.akshare_symbol,
            period="daily",
            start_date=self._period_to_start_date(period),
            end_date=datetime.now(timezone.utc).strftime("%Y%m%d"),
            adjust="qfq",
        )
        if frame is None or frame.empty:
            raise StockDataError(f"No kline data returned by AkShare for {meta.original_symbol}")

        rename_map = {
            "\u65e5\u671f": "date",
            "\u5f00\u76d8": "open",
            "\u6700\u9ad8": "high",
            "\u6700\u4f4e": "low",
            "\u6536\u76d8": "close",
            "\u6210\u4ea4\u91cf": "volume",
        }
        frame = frame.rename(columns=rename_map)
        return self._select_required_columns(frame, ["date", "open", "high", "low", "close", "volume"], "AkShare kline")

    def _fetch_yfinance_kline(self, meta: SymbolMeta, period: str) -> pd.DataFrame:
        import yfinance as yf

        self._configure_yfinance_cache(yf)
        ticker = yf.Ticker(meta.yfinance_symbol)
        
        # Convert period to yfinance interval and date range
        interval, date_range = self._period_to_yfinance_params(period)
        
        if date_range:
            # For specific periods like "1y", "3y", etc.
            start_date, end_date = date_range
            frame = ticker.history(start=start_date, end=end_date, interval=interval, auto_adjust=True, actions=False)
        else:
            # For simple period strings
            frame = ticker.history(period=period, interval=interval, auto_adjust=True, actions=False)

        if frame is None or frame.empty:
            raise StockDataError(f"No kline data returned by yfinance for {meta.original_symbol}")

        frame = frame.reset_index()
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = [self._normalize_column_name(column[-1]) for column in frame.columns]
        else:
            frame.columns = [self._normalize_column_name(column) for column in frame.columns]

        date_column = self._find_column(frame, ["date", "datetime", "index"])
        if date_column is None:
            logger.warning(
                "yfinance kline response missing date column for %s. columns=%s",
                meta.original_symbol,
                list(frame.columns),
            )
            raise StockDataError("yfinance kline response missing date column")

        frame = frame.rename(columns={date_column: "date"})
        return self._select_required_columns(frame, ["date", "open", "high", "low", "close", "volume"], "yfinance kline")

    def _frame_to_kline_bars(self, frame: pd.DataFrame, meta: SymbolMeta) -> list[KLineBar]:
        clean = frame.copy()
        clean = clean.dropna(subset=["date", "open", "high", "low", "close"])

        for column in ["open", "high", "low", "close", "volume"]:
            clean[column] = pd.to_numeric(clean[column], errors="coerce")

        clean = clean.dropna(subset=["open", "high", "low", "close", "volume"])
        clean = clean[clean["volume"] >= 0]
        clean = clean.sort_values("date")

        bars = [
            KLineBar(
                timestamp_utc=self._to_utc_datetime(row["date"], meta.timezone_name),
                open=self._to_decimal(row["open"]),
                high=self._to_decimal(row["high"]),
                low=self._to_decimal(row["low"]),
                close=self._to_decimal(row["close"]),
                volume=int(row["volume"]),
            )
            for row in clean.to_dict(orient="records")
        ]

        if not bars:
            raise StockDataError(f"Kline data is empty after cleaning for {meta.original_symbol}")
        return bars

    def _fetch_akshare_financial_indicators(self, meta: SymbolMeta) -> list[FinancialIndicators]:
        import akshare as ak

        if meta.akshare_symbol is None:
            return []

        frame = ak.stock_financial_analysis_indicator(symbol=meta.akshare_symbol)
        if frame is None or frame.empty:
            logger.warning("AkShare returned empty financial indicators for %s", meta.original_symbol)
            return []

        frame = frame.rename(columns={column: str(column).strip() for column in frame.columns})
        date_column = self._find_column(frame, ["\u65e5\u671f", "\u62a5\u544a\u671f", "\u62a5\u8868\u65e5\u671f"])
        if date_column is None:
            logger.warning("AkShare financial response missing report date for %s", meta.original_symbol)
            return []

        records: list[FinancialIndicators] = []
        for row in frame.head(5).to_dict(orient="records"):
            revenue = self._pick_decimal(
                row,
                ["\u4e3b\u8425\u4e1a\u52a1\u6536\u5165", "\u8425\u4e1a\u603b\u6536\u5165", "\u8425\u4e1a\u6536\u5165"],
            )
            net_profit = self._pick_decimal(
                row,
                [
                    "\u51c0\u5229\u6da6",
                    "\u5f52\u5c5e\u6bcd\u516c\u53f8\u80a1\u4e1c\u7684\u51c0\u5229\u6da6",
                    "\u6263\u9664\u975e\u7ecf\u5e38\u6027\u635f\u76ca\u540e\u7684\u51c0\u5229\u6da6",
                ],
            )
            gross_margin = self._percent_to_ratio(
                self._pick_decimal(row, ["\u9500\u552e\u6bdb\u5229\u7387", "\u6bdb\u5229\u7387"])
            )
            net_margin = self._percent_to_ratio(
                self._pick_decimal(row, ["\u9500\u552e\u51c0\u5229\u7387", "\u51c0\u5229\u7387"])
            )
            roe = self._percent_to_ratio(
                self._pick_decimal(
                    row,
                    [
                        "\u51c0\u8d44\u4ea7\u6536\u76ca\u7387",
                        "\u52a0\u6743\u51c0\u8d44\u4ea7\u6536\u76ca\u7387",
                        "\u644a\u8584\u51c0\u8d44\u4ea7\u6536\u76ca\u7387",
                    ],
                )
            )
            roic = self._percent_to_ratio(
                self._pick_decimal(row, ["\u6295\u5165\u8d44\u672c\u56de\u62a5\u7387", "ROIC"])
            )

            report_date = str(row[date_column])
            records.append(
                FinancialIndicators(
                    period=report_date[:4] if len(report_date) >= 4 else report_date,
                    report_type="annual",
                    roe=roe,
                    roic=roic,
                    revenue=revenue,
                    net_profit=net_profit,
                    gross_margin=gross_margin,
                    net_margin=net_margin,
                )
            )

        return records

    def _fetch_yfinance_financial_indicators(self, meta: SymbolMeta) -> list[FinancialIndicators]:
        import yfinance as yf

        self._configure_yfinance_cache(yf)
        ticker = yf.Ticker(meta.yfinance_symbol)
        financials = ticker.financials
        balance_sheet = ticker.balance_sheet
        cashflow = ticker.cashflow

        if financials is None or financials.empty:
            raise StockDataError(f"No financial data returned by yfinance for {meta.original_symbol}")

        indicators: list[FinancialIndicators] = []
        for period_end in list(financials.columns)[:5]:
            revenue = self._statement_value(financials, period_end, ["Total Revenue", "Operating Revenue"])
            gross_profit = self._statement_value(financials, period_end, ["Gross Profit"])
            net_profit = self._statement_value(financials, period_end, ["Net Income", "Net Income Common Stockholders"])
            ebit = self._statement_value(financials, period_end, ["EBIT", "Operating Income"])
            equity = self._statement_value(balance_sheet, period_end, ["Stockholders Equity", "Total Equity Gross Minority Interest"])
            long_term_debt = self._statement_value(balance_sheet, period_end, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"])
            cash = self._statement_value(balance_sheet, period_end, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"])

            free_cash_flow = self._statement_value(cashflow, period_end, ["Free Cash Flow"])
            if net_profit is None and free_cash_flow is not None:
                net_profit = free_cash_flow

            indicators.append(
                FinancialIndicators(
                    period=self._period_label(period_end),
                    report_type="annual",
                    roe=self._safe_divide(net_profit, equity),
                    roic=self._calculate_roic(ebit=ebit, equity=equity, long_term_debt=long_term_debt, excess_cash=cash),
                    revenue=revenue,
                    net_profit=net_profit,
                    gross_margin=self._safe_divide(gross_profit, revenue),
                    net_margin=self._safe_divide(net_profit, revenue),
                )
            )

        if not indicators:
            raise StockDataError(f"Financial data is empty after parsing for {meta.original_symbol}")
        return indicators

    def _try_direct_symbol_match(self, keyword: str) -> StockSearchResult | None:
        stripped = keyword.strip()
        normalized = stripped.upper()
        if not normalized:
            return None
        if stripped != normalized:
            return None
        if re.fullmatch(r"[A-Z0-9.\-]+", normalized) is None:
            return None

        if normalized.isdigit() and len(normalized) == 6:
            symbol = self._standardize_cn_symbol(normalized)
            return StockSearchResult(
                symbol=symbol,
                name=symbol,
                market="CN",
                currency="CNY",
                source="direct",
            )

        if normalized.isdigit() and 1 <= len(normalized) <= 5:
            symbol = f"{normalized.zfill(4)}.HK"
            return StockSearchResult(
                symbol=symbol,
                name=symbol,
                market="HK",
                currency="HKD",
                source="direct",
            )

        try:
            meta = self._parse_symbol(normalized)
        except StockDataError:
            return None

        if "." not in normalized and not normalized.isalpha():
            return None

        return StockSearchResult(
            symbol=meta.original_symbol,
            name=meta.original_symbol,
            market=meta.market,
            currency=meta.currency,
            source="direct",
        )

    def _search_local_symbol_catalog(self, keyword: str, limit: int) -> list[StockSearchResult]:
        normalized_keyword = self._normalize_search_text(keyword)
        scored: list[tuple[float, StockSearchResult]] = []

        for item in LOCAL_STOCK_CATALOG:
            result = StockSearchResult(
                symbol=item.symbol,
                name=item.name,
                market=item.market,
                currency=item.currency,
                source="local",
            )
            terms = (item.symbol, item.name, *item.aliases)
            score = self._score_search_result(normalized_keyword, terms)
            if score < 1000:
                scored.append((score, result))

        scored.sort(key=lambda pair: pair[0])
        return [item for _, item in scored[:limit]]

    def _score_search_result(self, keyword: str, terms: tuple[str, ...]) -> float:
        if not keyword:
            return 1000

        best_score = 1000.0
        for term in terms:
            normalized_term = self._normalize_search_text(term)
            if not normalized_term:
                continue

            if normalized_term == keyword:
                best_score = min(best_score, 0)
                continue
            if normalized_term.startswith(keyword):
                best_score = min(best_score, 10 + (len(normalized_term) - len(keyword)) / 100)
                continue
            if keyword in normalized_term:
                best_score = min(best_score, 30 + normalized_term.index(keyword) / 100)
                continue

            similarity = SequenceMatcher(None, keyword, normalized_term).ratio()
            if similarity >= 0.58:
                best_score = min(best_score, 80 - similarity * 40)

        return best_score

    def _normalize_search_text(self, value: str) -> str:
        return re.sub(r"[\s\-_.,&()（）·]+", "", value.strip().lower())

    def _search_a_share_symbols(self, keyword: str, limit: int) -> list[StockSearchResult]:
        import akshare as ak

        frame = ak.stock_info_a_code_name()
        if frame is None or frame.empty:
            return []

        code_column = self._find_column(frame, ["code", "symbol", "\u4ee3\u7801"])
        name_column = self._find_column(frame, ["name", "\u540d\u79f0"])
        if code_column is None or name_column is None:
            logger.warning("A-share symbol search missing columns: %s", list(frame.columns))
            return []

        return self._rows_to_search_results(
            frame=frame,
            keyword=keyword,
            code_column=code_column,
            name_column=name_column,
            market="CN",
            currency="CNY",
            source="akshare",
            limit=limit,
        )

    def _search_hk_symbols(self, keyword: str, limit: int) -> list[StockSearchResult]:
        import akshare as ak

        frame = ak.stock_hk_spot_em()
        if frame is None or frame.empty:
            return []

        code_column = self._find_column(frame, ["\u4ee3\u7801", "code", "symbol"])
        name_column = self._find_column(frame, ["\u540d\u79f0", "name"])
        if code_column is None or name_column is None:
            logger.warning("HK symbol search missing columns: %s", list(frame.columns))
            return []

        matches: list[StockSearchResult] = []
        normalized_keyword = keyword.strip().lower()
        for row in frame.to_dict(orient="records"):
            code = str(row.get(code_column, "")).strip()
            name = str(row.get(name_column, "")).strip()
            if not code or not name:
                continue
            if normalized_keyword not in code.lower() and normalized_keyword not in name.lower():
                continue

            matches.append(
                StockSearchResult(
                    symbol=f"{code.zfill(4)}.HK",
                    name=name,
                    market="HK",
                    currency="HKD",
                    source="akshare",
                )
            )
            if len(matches) >= limit:
                break

        return matches

    def _search_yfinance_symbols(self, keyword: str, limit: int) -> list[StockSearchResult]:
        import yfinance as yf

        self._configure_yfinance_cache(yf)
        if not hasattr(yf, "Search"):
            return []

        search = yf.Search(keyword, max_results=limit)
        quotes = getattr(search, "quotes", None)
        if not isinstance(quotes, list):
            return []

        results: list[StockSearchResult] = []
        for item in quotes:
            if not isinstance(item, dict):
                continue

            raw_symbol = str(item.get("symbol") or "").strip().upper()
            if not raw_symbol:
                continue

            quote_type = str(item.get("quoteType") or "").lower()
            if quote_type and quote_type not in {"equity", "etf"}:
                continue

            exchange = str(item.get("exchange") or "").upper()
            market = self._market_from_yfinance_symbol(raw_symbol, exchange)
            if market is None:
                continue

            name = str(item.get("shortname") or item.get("longname") or raw_symbol).strip()
            results.append(
                StockSearchResult(
                    symbol=self._standardize_yfinance_search_symbol(raw_symbol, market),
                    name=name,
                    market=market,
                    currency=self._currency_for_market(market),
                    source="yfinance",
                )
            )
            if len(results) >= limit:
                break

        return results

    def _rows_to_search_results(
        self,
        *,
        frame: pd.DataFrame,
        keyword: str,
        code_column: str,
        name_column: str,
        market: MarketCode,
        currency: str,
        source: str,
        limit: int,
    ) -> list[StockSearchResult]:
        normalized_keyword = keyword.strip().lower()
        matches: list[StockSearchResult] = []

        for row in frame.to_dict(orient="records"):
            code = str(row.get(code_column, "")).strip()
            name = str(row.get(name_column, "")).strip()
            if not code or not name:
                continue
            if normalized_keyword not in code.lower() and normalized_keyword not in name.lower():
                continue

            matches.append(
                StockSearchResult(
                    symbol=self._standardize_cn_symbol(code) if market == "CN" else code,
                    name=name,
                    market=market,
                    currency=currency,
                    source=source,
                )
            )
            if len(matches) >= limit:
                break

        return matches

    def _standardize_cn_symbol(self, code: str) -> str:
        normalized = code.strip().upper().removesuffix(".SH").removesuffix(".SZ")
        suffix = "SH" if normalized.startswith(("5", "6", "9")) else "SZ"
        return f"{normalized}.{suffix}"

    def _standardize_yfinance_search_symbol(self, symbol: str, market: MarketCode) -> str:
        if market == "HK":
            return f"{symbol.removesuffix('.HK').zfill(4)}.HK"
        return symbol

    def _market_from_yfinance_symbol(self, symbol: str, exchange: str) -> MarketCode | None:
        if symbol.endswith(".HK") or exchange in {"HKG", "HKSE"}:
            return "HK"
        if "." not in symbol and exchange in {"NMS", "NYQ", "ASE", "PCX", "NGM", "NCM", "BTS"}:
            return "US"
        if "." not in symbol and not exchange:
            return "US"
        return None

    def _currency_for_market(self, market: MarketCode) -> str:
        if market == "CN":
            return "CNY"
        if market == "HK":
            return "HKD"
        return "USD"

    def _deduplicate_search_results(self, results: list[StockSearchResult]) -> list[StockSearchResult]:
        seen: set[str] = set()
        deduplicated: list[StockSearchResult] = []
        for item in results:
            if item.symbol in seen:
                continue
            seen.add(item.symbol)
            deduplicated.append(item)
        return deduplicated

    def _calculate_roic(
        self,
        *,
        ebit: Decimal | None,
        equity: Decimal | None,
        long_term_debt: Decimal | None,
        excess_cash: Decimal | None,
    ) -> Decimal | None:
        invested_capital = self._sum_decimal(equity, long_term_debt)
        if invested_capital is None:
            return None
        if excess_cash is not None:
            invested_capital -= excess_cash
        return self._safe_divide(ebit, invested_capital)

    def _period_to_start_date(self, period: str) -> str:
        days_by_period = {
            "1m": 7,
            "5m": 30,
            "1h": 90,
            "4h": 180,
            "1d": 365,
            "1mo": 40,
            "3mo": 120,
            "6mo": 220,
            "1y": 380,
            "2y": 760,
            "3y": 1140,
            "5y": 1900,
            "10y": 3800,
            "max": 12000,
        }
        days = days_by_period.get(period, 380)
        return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y%m%d")

    def _period_to_yfinance_params(self, period: str) -> tuple[str, tuple[str, str] | None]:
        """
        Convert period string to yfinance interval and date range.
        Returns: (interval, (start_date, end_date) or None)
        """
        # Map of period to (interval, date_range_days or None)
        intraday_periods = {
            "1m": ("1m", 7),
            "5m": ("5m", 30),
        }
        
        hourly_periods = {
            "1h": ("1h", 90),
            "4h": ("4h", 180),
        }
        
        daily_periods = {
            "1d": ("1d", 365),
            "1mo": ("1d", None),
            "3mo": ("1d", None),
            "6mo": ("1d", None),
            "1y": ("1d", None),
            "2y": ("1d", None),
            "3y": ("1d", None),
            "5y": ("1d", None),
            "10y": ("1d", None),
            "max": ("1d", None),
        }
        
        if period in intraday_periods:
            interval, days = intraday_periods[period]
            start_date = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
            end_date = datetime.now(timezone.utc).date().isoformat()
            return interval, (start_date, end_date)
        
        if period in hourly_periods:
            interval, days = hourly_periods[period]
            start_date = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
            end_date = datetime.now(timezone.utc).date().isoformat()
            return interval, (start_date, end_date)
        
        if period in daily_periods:
            interval, days = daily_periods[period]
            if days:
                start_date = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
                end_date = datetime.now(timezone.utc).date().isoformat()
                return interval, (start_date, end_date)
            return interval, None
        
        # Default to 1d interval with 1 year of data
        return "1d", None

    def _select_required_columns(self, frame: pd.DataFrame, required: list[str], source_name: str) -> pd.DataFrame:
        missing = [column for column in required if column not in frame.columns]
        if missing:
            raise StockDataError(f"{source_name} response missing columns: {missing}")
        return frame[required].copy()

    def _to_utc_datetime(self, value: Any, timezone_name: str) -> datetime:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize(ZoneInfo(timezone_name))
        else:
            timestamp = timestamp.tz_convert(ZoneInfo(timezone_name))
        return timestamp.to_pydatetime().astimezone(timezone.utc)

    def _to_decimal(self, value: Any) -> Decimal:
        if value is None:
            raise StockDataError("Cannot convert None to Decimal")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise StockDataError(f"Cannot convert non-finite value to Decimal: {value}")
        try:
            return Decimal(str(round(numeric, 8)))
        except InvalidOperation as exc:
            raise StockDataError(f"Cannot convert value to Decimal: {value}") from exc

    def _statement_value(self, frame: pd.DataFrame | None, period_end: Any, row_names: list[str]) -> Decimal | None:
        if frame is None or frame.empty or period_end not in frame.columns:
            return None
        for row_name in row_names:
            if row_name in frame.index:
                return self._nullable_decimal(frame.at[row_name, period_end])
        return None

    def _nullable_decimal(self, value: Any) -> Decimal | None:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, str):
            normalized = value.strip().replace(",", "").replace("%", "")
            if normalized.lower() in {"", "-", "--", "nan", "none", "null"}:
                return None
            value = normalized
        numeric = float(value)
        if not math.isfinite(numeric):
            return None
        return Decimal(str(round(numeric, 8)))

    def _safe_divide(self, numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
        if numerator is None or denominator is None or denominator == 0:
            return None
        return Decimal(str(round(float(numerator / denominator), 8)))

    def _sum_decimal(self, *values: Decimal | None) -> Decimal | None:
        valid_values = [value for value in values if value is not None]
        if not valid_values:
            return None
        total = Decimal("0")
        for value in valid_values:
            total += value
        return total

    def _period_label(self, value: Any) -> str:
        timestamp = pd.Timestamp(value)
        if pd.isna(timestamp):
            return str(value)
        return str(timestamp.year)

    def _find_column(self, frame: pd.DataFrame, candidates: list[str]) -> str | None:
        for candidate in candidates:
            if candidate in frame.columns:
                return candidate
        return None

    def _normalize_column_name(self, value: Any) -> str:
        return str(value).strip().lower().replace(" ", "_")

    def _configure_yfinance_cache(self, yf_module: Any) -> None:
        YFINANCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        yf_module.set_tz_cache_location(str(YFINANCE_CACHE_DIR))

    def _pick_decimal(self, row: dict[str, Any], candidates: list[str]) -> Decimal | None:
        for candidate in candidates:
            if candidate in row:
                value = self._nullable_decimal(row[candidate])
                if value is not None:
                    return value
        return None

    def _percent_to_ratio(self, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        if abs(value) > 1:
            return Decimal(str(round(float(value / Decimal("100")), 8)))
        return value

    def _is_network_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        network_markers = [
            "failed to connect",
            "could not connect",
            "connectionerror",
            "connection refused",
            "timed out",
            "timeout",
            "name resolution",
            "temporary failure",
            "network",
            "curl:",
        ]
        return any(marker in message for marker in network_markers)
