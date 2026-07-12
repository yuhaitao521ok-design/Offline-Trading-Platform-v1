/**
 * Shared market data types - single source of truth for frontend.
 */

export interface KLineBar {
  timestamp_utc: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface FinancialIndicators {
  period: string;
  report_type: 'annual' | 'quarterly';
  roe: number | null;
  roic: number | null;
  revenue: number | null;
  net_profit: number | null;
  gross_margin: number | null;
  net_margin: number | null;
}

export interface StockSearchResult {
  symbol: string;
  name: string;
  market: 'CN' | 'HK' | 'US';
  currency: string | null;
  source: string;
}

export interface StockSearchSuggestion extends StockSearchResult {
  value: string;
  label: string;
}

export type PeriodValue =
  | '1m'
  | '5m'
  | '1h'
  | '4h'
  | '1d'
  | '1mo'
  | '3mo'
  | '6mo'
  | '1y'
  | '2y'
  | '3y'
  | '5y'
  | '10y'
  | 'max';

export interface PeriodOption {
  label: string;
  value: PeriodValue;
}

export type SubIndicator = 'MACD' | 'RSI' | 'KDJ' | 'BOLL';

export interface OverlayIndicatorOption {
  label: string;
  value: string;
  type: 'MA' | 'EMA';
  period: number;
}

export interface RadarMetric {
  name: string;
  value: number;
  raw: number | null;
}
