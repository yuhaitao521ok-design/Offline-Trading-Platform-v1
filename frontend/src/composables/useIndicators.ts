/**
 * Technical indicator calculations composable.
 * Extracted from DashboardView for reusability and testability.
 */

export interface KLineBar {
  timestamp_utc: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MACDResult {
  dif: Array<number | null>;
  dea: Array<number | null>;
  histogram: Array<number | null>;
}

export interface KDJResult {
  k: Array<number | null>;
  d: Array<number | null>;
  j: Array<number | null>;
}

function roundTo(value: number, decimals: number): number {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
}

export function calculateMA(
  values: number[],
  period: number,
): Array<number | null> {
  return values.map((_, index) => {
    if (index < period - 1) {
      return null;
    }
    const windowValues = values.slice(index - period + 1, index + 1);
    return roundTo(
      windowValues.reduce((total, value) => total + value, 0) / period,
      4,
    );
  });
}

export function calculateEMA(
  values: number[],
  period: number,
): Array<number | null> {
  if (values.length === 0) {
    return [];
  }
  const multiplier = 2 / (period + 1);
  let previous = values[0];
  return values.map((value, index) => {
    if (index === 0) {
      previous = value;
      return roundTo(value, 4);
    }
    previous = value * multiplier + previous * (1 - multiplier);
    return roundTo(previous, 4);
  });
}

export function calculateMACD(values: number[]): MACDResult {
  const ema12 = calculateEMA(values, 12);
  const ema26 = calculateEMA(values, 26);
  let previousDea = 0;
  const dif: Array<number | null> = [];
  const dea: Array<number | null> = [];
  const histogram: Array<number | null> = [];
  values.forEach((_, index) => {
    const fast = ema12[index];
    const slow = ema26[index];
    if (fast === null || slow === null) {
      dif.push(null);
      dea.push(null);
      histogram.push(null);
      return;
    }
    const nextDif = fast - slow;
    previousDea = index === 0 ? nextDif : previousDea * 0.8 + nextDif * 0.2;
    dif.push(roundTo(nextDif, 4));
    dea.push(roundTo(previousDea, 4));
    histogram.push(roundTo((nextDif - previousDea) * 2, 4));
  });
  return { dif, dea, histogram };
}

export function calculateRSI(
  values: number[],
  period = 14,
): Array<number | null> {
  return values.map((_, index) => {
    if (index < period) {
      return null;
    }
    let gain = 0;
    let loss = 0;
    for (let cursor = index - period + 1; cursor <= index; cursor += 1) {
      const change = values[cursor] - values[cursor - 1];
      if (change >= 0) {
        gain += change;
      } else {
        loss += Math.abs(change);
      }
    }
    if (loss === 0) {
      return 100;
    }
    const relativeStrength = gain / loss;
    return roundTo(100 - 100 / (1 + relativeStrength), 2);
  });
}

export function calculateKDJ(bars: KLineBar[], period = 9): KDJResult {
  let previousK = 50;
  let previousD = 50;
  const k: Array<number | null> = [];
  const d: Array<number | null> = [];
  const j: Array<number | null> = [];
  bars.forEach((bar, index) => {
    if (index < period - 1) {
      k.push(null);
      d.push(null);
      j.push(null);
      return;
    }
    const windowBars = bars.slice(index - period + 1, index + 1);
    const low = Math.min(...windowBars.map((item) => item.low));
    const high = Math.max(...windowBars.map((item) => item.high));
    const rsv = high === low ? 50 : ((bar.close - low) / (high - low)) * 100;
    previousK = (2 / 3) * previousK + (1 / 3) * rsv;
    previousD = (2 / 3) * previousD + (1 / 3) * previousK;
    k.push(roundTo(previousK, 2));
    d.push(roundTo(previousD, 2));
    j.push(roundTo(3 * previousK - 2 * previousD, 2));
  });
  return { k, d, j };
}

/**
 * Calculate Bollinger Bands (BOLL) - additional indicator
 */
export function calculateBOLL(
  values: number[],
  period = 20,
  multiplier = 2,
): {
  upper: Array<number | null>;
  middle: Array<number | null>;
  lower: Array<number | null>;
} {
  const upper: Array<number | null> = [];
  const middle: Array<number | null> = [];
  const lower: Array<number | null> = [];

  values.forEach((_, index) => {
    if (index < period - 1) {
      upper.push(null);
      middle.push(null);
      lower.push(null);
      return;
    }
    const window = values.slice(index - period + 1, index + 1);
    const mean = window.reduce((sum, v) => sum + v, 0) / period;
    const variance =
      window.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / period;
    const stdDev = Math.sqrt(variance);
    middle.push(roundTo(mean, 4));
    upper.push(roundTo(mean + multiplier * stdDev, 4));
    lower.push(roundTo(mean - multiplier * stdDev, 4));
  });

  return { upper, middle, lower };
}
