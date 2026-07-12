<script setup lang="ts">
import {
  computed,
  nextTick,
  onMounted,
  onUnmounted,
  ref,
  shallowRef,
  watch,
  onBeforeUnmount,
} from "vue";
import type { ShallowRef } from "vue";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";
import { ElMessage } from "element-plus";

import { getApiData } from "../api/http";
import { useWatchlistStore } from "../stores/watchlist";
import {
  calculateMA,
  calculateEMA,
  calculateMACD,
  calculateRSI,
  calculateKDJ,
  calculateBOLL,
} from "../composables/useIndicators";
import {
  formatPrice,
  formatPercent,
  formatVolume,
  formatCompactNumber,
  formatDate,
  ratioToPercent,
  roundTo,
} from "../composables/useFormatters";
import type {
  KLineBar,
  FinancialIndicators,
  StockSearchResult,
  StockSearchSuggestion,
  PeriodOption,
  SubIndicator,
  OverlayIndicatorOption,
  RadarMetric,
} from "../composables/types";

interface TooltipParam {
  dataIndex?: number;
}

const periodOptions: PeriodOption[] = [
  { label: "1m", value: "1m" },
  { label: "5m", value: "5m" },
  { label: "1h", value: "1h" },
  { label: "4h", value: "4h" },
  { label: "1D", value: "1d" },
  { label: "1M", value: "1mo" },
  { label: "3M", value: "3mo" },
  { label: "6M", value: "6mo" },
  { label: "1Y", value: "1y" },
  { label: "2Y", value: "2y" },
  { label: "3Y", value: "3y" },
  { label: "5Y", value: "5y" },
  { label: "10Y", value: "10y" },
];

const overlayIndicatorOptions: OverlayIndicatorOption[] = [
  5, 10, 20, 60,
].flatMap((period) => [
  { label: `MA${period}`, value: `MA${period}`, type: "MA", period },
  { label: `EMA${period}`, value: `EMA${period}`, type: "EMA", period },
]);

const subIndicatorOptions: SubIndicator[] = ["MACD", "RSI", "KDJ", "BOLL"];
const chartType = ref<"candlestick" | "line">("candlestick");

const symbolInput = ref("AAPL");
const activeSymbol = ref("AAPL");
const activeStockName = ref("Apple Inc.");
const activePeriod = ref<PeriodOption["value"]>("1d");
const klineData = ref<KLineBar[]>([]);
const financeData = ref<FinancialIndicators[]>([]);
const isLoading = ref(false);
const selectedOverlayIndicators = ref<string[]>(["MA20", "EMA20"]);
const selectedSubIndicators = ref<SubIndicator[]>(["MACD"]);
const priceChartEl = ref<HTMLDivElement | null>(null);
const radarChartEl = ref<HTMLDivElement | null>(null);
const trendChartEl = ref<HTMLDivElement | null>(null);
const symbolSuggestionCache = new Map<string, StockSearchSuggestion[]>();
let symbolSearchTimer: number | null = null;
let symbolSearchSequence = 0;

const priceChart = shallowRef<echarts.ECharts | null>(null);
const radarChart = shallowRef<echarts.ECharts | null>(null);
const trendChart = shallowRef<echarts.ECharts | null>(null);

const watchlist = useWatchlistStore();

const latestBar = computed(() => klineData.value.at(-1) ?? null);
const previousBar = computed(() => klineData.value.at(-2) ?? null);
const latestFinance = computed(() => financeData.value[0] ?? null);
const chartBaseHeight = ref(560);
const priceChartHeight = computed(
  () => `${chartBaseHeight.value + selectedSubIndicators.value.length * 118}px`,
);

// Draggable chart resize
let isResizing = false;
let resizeStartY = 0;
let resizeStartHeight = 0;

function onResizeStart(event: MouseEvent): void {
  isResizing = true;
  resizeStartY = event.clientY;
  resizeStartHeight = chartBaseHeight.value;
  document.addEventListener("mousemove", onResizeMove);
  document.addEventListener("mouseup", onResizeEnd);
  document.body.style.cursor = "row-resize";
  document.body.style.userSelect = "none";
}

function onResizeMove(event: MouseEvent): void {
  if (!isResizing) return;
  const delta = event.clientY - resizeStartY;
  const newHeight = Math.max(300, Math.min(1200, resizeStartHeight + delta));
  chartBaseHeight.value = newHeight;
}

function onResizeEnd(): void {
  isResizing = false;
  document.removeEventListener("mousemove", onResizeMove);
  document.removeEventListener("mouseup", onResizeEnd);
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
  // Resize charts after height change
  setTimeout(resizeCharts, 50);
}

const priceChange = computed(() => {
  if (!latestBar.value || !previousBar.value) {
    return null;
  }
  return latestBar.value.close - previousBar.value.close;
});

const priceChangeRatio = computed(() => {
  if (!latestBar.value || !previousBar.value || previousBar.value.close === 0) {
    return null;
  }
  return latestBar.value.close / previousBar.value.close - 1;
});

const marketToneClass = computed(() => {
  if (priceChange.value === null || priceChange.value === 0) {
    return "market-flat";
  }
  return priceChange.value > 0 ? "market-up" : "market-down";
});

const latestTradeDate = computed(() => {
  if (!latestBar.value) {
    return "--";
  }
  return formatDate(latestBar.value.timestamp_utc);
});

const activePeriodLabel = computed(() => {
  const option = periodOptions.find((o) => o.value === activePeriod.value);
  return option ? option.label : activePeriod.value.toUpperCase();
});

function toggleOverlayIndicator(value: string): void {
  const idx = selectedOverlayIndicators.value.indexOf(value);
  if (idx >= 0) {
    selectedOverlayIndicators.value.splice(idx, 1);
  } else {
    selectedOverlayIndicators.value.push(value);
  }
  handleIndicatorConfigChange();
}

function toggleSubIndicator(value: SubIndicator): void {
  const idx = selectedSubIndicators.value.indexOf(value);
  if (idx >= 0) {
    selectedSubIndicators.value.splice(idx, 1);
  } else {
    selectedSubIndicators.value.push(value);
  }
  handleIndicatorConfigChange();
}

function normalizeDirectSymbol(value: string): string {
  return value.trim().toUpperCase();
}

function isDirectSymbolLike(value: string): boolean {
  const trimmed = value.trim();
  const upper = trimmed.toUpperCase();
  if (/^\d{6}\.(SH|SZ)$/.test(upper)) {
    return true;
  }
  if (/^\d{1,5}\.HK$/.test(upper)) {
    return true;
  }
  return trimmed === upper && /^[A-Z]{1,5}$/.test(upper);
}

async function resolveStockFromInput(
  value: string,
): Promise<StockSearchResult> {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error("Please enter a stock symbol or company name.");
  }
  const results = await getApiData<StockSearchResult[]>("/stock/search", {
    keyword: trimmed,
    limit: 1,
  });
  const first = results[0];
  if (!first) {
    // Fallback: try uppercase symbol search for case-insensitive match
    const upperResults = await getApiData<StockSearchResult[]>(
      "/stock/search",
      {
        keyword: trimmed.toUpperCase(),
        limit: 1,
      },
    );
    const upperFirst = upperResults[0];
    if (!upperFirst) {
      throw new Error(`No stock found for "${trimmed}".`);
    }
    return upperFirst;
  }
  return first;
}

async function fetchSymbolSuggestions(
  query: string,
  callback: (items: StockSearchSuggestion[]) => void,
): Promise<void> {
  const keyword = query.trim();
  if (symbolSearchTimer !== null) {
    window.clearTimeout(symbolSearchTimer);
    symbolSearchTimer = null;
  }
  if (keyword.length < 1 && !isDirectSymbolLike(keyword)) {
    callback([]);
    return;
  }
  if (isDirectSymbolLike(keyword.toUpperCase())) {
    const symbol = normalizeDirectSymbol(keyword);
    callback([
      {
        symbol,
        name: symbol,
        market:
          symbol.endsWith(".SH") || symbol.endsWith(".SZ")
            ? "CN"
            : symbol.endsWith(".HK")
              ? "HK"
              : "US",
        currency: null,
        source: "direct",
        value: symbol,
        label: symbol,
      },
    ]);
    return;
  }
  const searchKeyword = keyword.toUpperCase();
  const cacheKey = searchKeyword;
  const cached = symbolSuggestionCache.get(cacheKey);
  if (cached) {
    callback(cached);
    return;
  }
  const requestId = ++symbolSearchSequence;
  symbolSearchTimer = window.setTimeout(() => {
    void (async () => {
      try {
        const results = await getApiData<StockSearchResult[]>("/stock/search", {
          keyword: searchKeyword,
          limit: 8,
        });
        if (requestId !== symbolSearchSequence) {
          return;
        }
        const suggestions = results.map((item) => ({
          ...item,
          value: `${item.symbol} ${item.name}`,
          label: `${item.symbol} ${item.name}`,
        }));
        symbolSuggestionCache.set(cacheKey, suggestions);
        callback(suggestions);
      } catch {
        if (requestId === symbolSearchSequence) {
          callback([]);
        }
      }
    })();
  }, 260);
}

function isPeriodValue(value: unknown): value is PeriodOption["value"] {
  return periodOptions.some((option) => option.value === value);
}

async function refreshDashboard(): Promise<void> {
  isLoading.value = true;
  try {
    const nextStock = await resolveStockFromInput(symbolInput.value);
    activeSymbol.value = nextStock.symbol;
    activeStockName.value = nextStock.name;
    symbolInput.value = nextStock.symbol;

    const [kline, finance] = await Promise.all([
      getApiData<KLineBar[]>("/stock/kline", {
        symbol: activeSymbol.value,
        period: activePeriod.value,
      }),
      getApiData<FinancialIndicators[]>("/stock/finance", {
        symbol: activeSymbol.value,
      }),
    ]);

    klineData.value = kline;
    financeData.value = finance;
    await nextTick();
    renderAllCharts();
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Market data request failed.";
    ElMessage.error(message);
  } finally {
    isLoading.value = false;
  }
}

function handleSymbolSelect(item: StockSearchSuggestion): void {
  symbolInput.value = item.symbol;
  activeStockName.value = item.name;
  void refreshDashboard();
}

function handlePeriodChange(
  value: string | number | boolean | undefined,
): void {
  if (!isPeriodValue(value)) {
    return;
  }
  activePeriod.value = value;
  void refreshDashboard();
}

function handleIndicatorConfigChange(): void {
  void nextTick(() => {
    renderPriceChart();
    resizeCharts();
  });
}

function renderAllCharts(): void {
  renderPriceChart();
  renderRadarChart();
  renderTrendChart();
}

function getChartInstance(
  element: HTMLDivElement | null,
  current: ShallowRef<echarts.ECharts | null>,
): echarts.ECharts | null {
  if (!element) {
    return null;
  }
  if (!current.value) {
    current.value = echarts.init(element, "dark", { renderer: "canvas" });
  }
  return current.value;
}

function getCssVar(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

function renderPriceChart(): void {
  const chart = getChartInstance(priceChartEl.value, priceChart);
  if (!chart) {
    return;
  }

  // Resolve dynamic up/down colors from CSS variables
  const upFill = getCssVar("--quant-up-fill");
  const upFillSoft = getCssVar("--quant-up-fill-soft");
  const upBorder = getCssVar("--quant-up-border");
  const downFill = getCssVar("--quant-down-fill");
  const downFillSoft = getCssVar("--quant-down-fill-soft");
  const downBorder = getCssVar("--quant-down-border");

  const labels = klineData.value.map((item) => formatDate(item.timestamp_utc));
  const candleData = klineData.value.map((item) => [
    item.open,
    item.close,
    item.low,
    item.high,
  ]);
  const closeValues = klineData.value.map((item) => item.close);
  const volumeData = klineData.value.map((item, index) => ({
    value: item.volume,
    itemStyle: {
      color: item.close >= item.open ? upFillSoft : downFillSoft,
    },
    xAxis: index,
  }));
  const subIndicators = selectedSubIndicators.value;
  const xAxisIndexes = Array.from(
    { length: 2 + subIndicators.length },
    (_, index) => index,
  );

  // Calculate grid heights based on chartBaseHeight for scaling
  const mainHeight = Math.max(200, chartBaseHeight.value - 310);
  const volTop = 36 + mainHeight + 18;
  const grid: NonNullable<EChartsOption["grid"]> = [
    {
      left: 16,
      right: 16,
      top: 36,
      height: mainHeight,
      containLabel: true,
    },
    {
      left: 16,
      right: 16,
      top: volTop,
      height: 60,
      containLabel: true,
    },
  ];

  const xAxis: NonNullable<EChartsOption["xAxis"]> = [
    {
      type: "category",
      boundaryGap: true,
      data: labels,
      axisLine: {
        lineStyle: {
          color: "rgba(255, 255, 255, 0.06)",
        },
      },
      axisLabel: {
        color: "#6b7a8f",
        fontSize: 11,
      },
      axisTick: {
        show: false,
      },
    },
    {
      type: "category",
      gridIndex: 1,
      boundaryGap: true,
      data: labels,
      axisLine: {
        lineStyle: {
          color: "rgba(255, 255, 255, 0.06)",
        },
      },
      axisLabel: {
        show: false,
      },
      axisTick: {
        show: false,
      },
    },
  ];

  const yAxis: NonNullable<EChartsOption["yAxis"]> = [
    {
      type: "value",
      scale: true,
      splitNumber: 4,
      splitLine: {
        lineStyle: {
          color: "rgba(255, 255, 255, 0.04)",
          type: "dashed",
        },
      },
      axisLabel: {
        color: "#6b7a8f",
        fontSize: 11,
        formatter: (value: number) => formatCompactNumber(value),
      },
    },
    {
      type: "value",
      gridIndex: 1,
      splitNumber: 2,
      splitLine: {
        show: false,
      },
      axisLabel: {
        color: "#6b7a8f",
        fontSize: 10,
        formatter: (value: number) => formatCompactNumber(value),
      },
    },
  ];

  const series: NonNullable<EChartsOption["series"]> = [];

  if (chartType.value === "candlestick") {
    series.push({
      name: "OHLC",
      type: "candlestick",
      data: candleData,
      barMaxWidth: 14,
      itemStyle: {
        color: upFill,
        color0: downFill,
        borderColor: upBorder,
        borderColor0: downBorder,
      },
    });
  } else {
    series.push({
      name: "Close",
      type: "line",
      data: closeValues,
      smooth: false,
      symbol: "none",
      lineStyle: {
        width: 2,
        color: getCssVar("--quant-accent-1"),
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "rgba(99, 102, 241, 0.15)" },
          { offset: 1, color: "rgba(99, 102, 241, 0.01)" },
        ]),
      },
    });
  }

  selectedOverlayIndicators.value.forEach((indicatorKey, index) => {
    const option = overlayIndicatorOptions.find(
      (item) => item.value === indicatorKey,
    );
    if (!option) {
      return;
    }
    const data =
      option.type === "MA"
        ? calculateMA(closeValues, option.period)
        : calculateEMA(closeValues, option.period);
    const palette = [
      "#818cf8",
      "#f59e0b",
      "#67e8f9",
      "#f472b6",
      "#a78bfa",
      "#22d3ee",
      "#fb923c",
      "#a3e635",
    ];
    series.push({
      name: option.label,
      type: "line",
      data,
      smooth: true,
      symbol: "none",
      lineStyle: {
        width: 1.6,
        color: palette[index % palette.length],
      },
      emphasis: {
        focus: "series",
      },
    });
  });

  series.push({
    name: "Volume",
    type: "bar",
    xAxisIndex: 1,
    yAxisIndex: 1,
    data: volumeData,
    barWidth: "52%",
    emphasis: {
      disabled: true,
    },
  });

  subIndicators.forEach((indicator, index) => {
    const gridIndex = 2 + index;
    const top = 432 + index * 110;

    grid.push({
      left: 16,
      right: 16,
      top,
      height: 80,
      containLabel: true,
    });

    xAxis.push({
      type: "category",
      gridIndex,
      boundaryGap: true,
      data: labels,
      axisLine: {
        lineStyle: {
          color: "rgba(255, 255, 255, 0.06)",
        },
      },
      axisLabel: {
        color: index === subIndicators.length - 1 ? "#6b7a8f" : "transparent",
        fontSize: 11,
      },
      axisTick: {
        show: false,
      },
    });

    yAxis.push({
      type: "value",
      gridIndex,
      scale: true,
      name: indicator,
      nameTextStyle: {
        color: "#6b7a8f",
        fontSize: 10,
        fontWeight: 600,
      },
      splitNumber: 2,
      splitLine: {
        lineStyle: {
          color: "rgba(255, 255, 255, 0.04)",
          type: "dashed",
        },
      },
      axisLabel: {
        color: "#6b7a8f",
        fontSize: 10,
        formatter: (value: number) => formatCompactNumber(value),
      },
    });

    if (indicator === "MACD") {
      const macd = calculateMACD(closeValues);
      series.push(
        {
          name: "MACD Hist",
          type: "bar",
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          data: macd.histogram.map((value) => ({
            value,
            itemStyle: {
              color: value !== null && value >= 0 ? upFillSoft : downFillSoft,
            },
          })),
          barWidth: "40%",
        },
        {
          name: "DIF",
          type: "line",
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          data: macd.dif,
          smooth: true,
          symbol: "none",
          lineStyle: {
            width: 1.5,
            color: "#818cf8",
          },
        },
        {
          name: "DEA",
          type: "line",
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          data: macd.dea,
          smooth: true,
          symbol: "none",
          lineStyle: {
            width: 1.5,
            color: "#f59e0b",
          },
        },
      );
    }

    if (indicator === "RSI") {
      series.push({
        name: "RSI14",
        type: "line",
        xAxisIndex: gridIndex,
        yAxisIndex: gridIndex,
        data: calculateRSI(closeValues, 14),
        smooth: true,
        symbol: "none",
        lineStyle: {
          width: 1.8,
          color: "#67e8f9",
        },
        markLine: {
          symbol: "none",
          lineStyle: {
            color: "rgba(255, 255, 255, 0.12)",
            type: "dashed",
          },
          data: [{ yAxis: 70 }, { yAxis: 30 }],
        },
      });
    }

    if (indicator === "KDJ") {
      const kdj = calculateKDJ(klineData.value);
      series.push(
        {
          name: "K",
          type: "line",
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          data: kdj.k,
          smooth: true,
          symbol: "none",
          lineStyle: {
            width: 1.5,
            color: "#818cf8",
          },
        },
        {
          name: "D",
          type: "line",
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          data: kdj.d,
          smooth: true,
          symbol: "none",
          lineStyle: {
            width: 1.5,
            color: "#f59e0b",
          },
        },
        {
          name: "J",
          type: "line",
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          data: kdj.j,
          smooth: true,
          symbol: "none",
          lineStyle: {
            width: 1.5,
            color: "#f472b6",
          },
        },
      );
    }

    if (indicator === "BOLL") {
      const boll = calculateBOLL(closeValues, 20, 2);
      series.push(
        {
          name: "BOLL Upper",
          type: "line",
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          data: boll.upper,
          smooth: true,
          symbol: "none",
          lineStyle: {
            width: 1.2,
            color: "rgba(99, 102, 241, 0.5)",
            type: "dashed",
          },
        },
        {
          name: "BOLL Mid",
          type: "line",
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          data: boll.middle,
          smooth: true,
          symbol: "none",
          lineStyle: { width: 1.2, color: "rgba(245, 158, 11, 0.5)" },
        },
        {
          name: "BOLL Lower",
          type: "line",
          xAxisIndex: gridIndex,
          yAxisIndex: gridIndex,
          data: boll.lower,
          smooth: true,
          symbol: "none",
          lineStyle: {
            width: 1.2,
            color: "rgba(236, 72, 153, 0.5)",
            type: "dashed",
          },
        },
      );
    }
  });

  const option: EChartsOption = {
    backgroundColor: "transparent",
    animation: false,
    grid,
    legend: {
      top: 2,
      right: 8,
      type: "scroll",
      textStyle: {
        color: "#8b96a8",
        fontSize: 11,
      },
      pageIconColor: "#818cf8",
      pageTextStyle: {
        color: "#6b7a8f",
      },
    },
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        lineStyle: {
          color: "#818cf8",
          width: 1,
          type: "dashed",
        },
      },
      borderColor: "rgba(99, 102, 241, 0.3)",
      backgroundColor: "rgba(13, 17, 23, 0.95)",
      textStyle: {
        color: "#f0f4f8",
        fontSize: 12,
      },
      formatter: (params: unknown) => {
        const items = Array.isArray(params) ? params : [params];
        const first = items[0] as TooltipParam | undefined;
        const dataIndex =
          typeof first?.dataIndex === "number" ? first.dataIndex : 0;
        const bar = klineData.value[dataIndex];
        if (!bar) {
          return "";
        }
        const changeRatio = getBarChangeRatio(dataIndex);
        const changeColor =
          changeRatio !== null && changeRatio >= 0
            ? getCssVar("--quant-up")
            : getCssVar("--quant-down");
        return [
          `<div class="chart-tooltip-title">${formatDate(bar.timestamp_utc)}</div>`,
          `<div>Open ${formatPrice(bar.open)}</div>`,
          `<div>Close <b style="color:#818cf8">${formatPrice(bar.close)}</b></div>`,
          `<div>High ${formatPrice(bar.high)}</div>`,
          `<div>Low ${formatPrice(bar.low)}</div>`,
          `<div>Change <b style="color:${changeColor}">${formatPercent(changeRatio)}</b></div>`,
          `<div>Volume ${formatVolume(bar.volume)}</div>`,
        ].join("");
      },
    },
    axisPointer: {
      link: [
        {
          xAxisIndex: "all",
        },
      ],
    },
    xAxis,
    yAxis,
    dataZoom: [
      {
        type: "inside",
        xAxisIndex: xAxisIndexes,
        throttle: 32,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true,
      },
      {
        type: "slider",
        xAxisIndex: xAxisIndexes,
        height: 24,
        bottom: 14,
        borderColor: "rgba(255, 255, 255, 0.06)",
        backgroundColor: "rgba(13, 17, 23, 0.8)",
        fillerColor: "rgba(99, 102, 241, 0.12)",
        handleStyle: {
          color: "#818cf8",
          borderColor: "#818cf8",
        },
        textStyle: {
          color: "#6b7a8f",
          fontSize: 10,
        },
      },
    ],
    series,
  };

  chart.setOption(option, true);
}

function renderRadarChart(): void {
  const chart = getChartInstance(radarChartEl.value, radarChart);
  if (!chart) {
    return;
  }

  const metrics = buildRadarMetrics(latestFinance.value);
  const values = metrics.map((metric) => metric.value);
  const averageScore = roundTo(
    values.reduce((sum, v) => sum + v, 0) / values.length,
    1,
  );

  // Build axis indicators with actual raw values shown as suffix
  const indicators = metrics.map((metric) => ({
    name: `${metric.name}\n${metric.raw === null ? "--" : formatPercent(metric.raw)}`,
    max: 100,
  }));

  const option: EChartsOption = {
    backgroundColor: "transparent",
    tooltip: {
      borderColor: "rgba(99, 102, 241, 0.3)",
      backgroundColor: "rgba(13, 17, 23, 0.95)",
      textStyle: {
        color: "#f0f4f8",
      },
      formatter: () =>
        metrics
          .map(
            (metric) =>
              `<div style="display:flex;justify-content:space-between;gap:24px">
                <span>${metric.name}</span>
                <b>${metric.raw === null ? "--" : formatPercent(metric.raw)}</b>
              </div>`,
          )
          .join("") +
        `<div style="display:flex;justify-content:space-between;gap:24px;margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.08)">
          <span>Composite Score</span>
          <b style="color:#818cf8">${averageScore.toFixed(1)} / 100</b>
        </div>`,
    },
    radar: {
      radius: "60%",
      center: ["50%", "52%"],
      splitNumber: 4,
      indicator: indicators,
      shape: "polygon",
      axisName: {
        color: "#b0bccd",
        fontSize: 12,
        fontWeight: 600,
        lineHeight: 20,
      },
      axisLine: {
        lineStyle: {
          color: "rgba(255, 255, 255, 0.06)",
        },
      },
      splitLine: {
        lineStyle: {
          color: "rgba(255, 255, 255, 0.06)",
        },
      },
      splitArea: {
        areaStyle: {
          color: ["rgba(99, 102, 241, 0.03)", "rgba(139, 92, 246, 0.03)"],
        },
      },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: values,
            name: "Profitability Moat",
            areaStyle: {
              color: "rgba(99, 102, 241, 0.18)",
            },
            lineStyle: {
              color: "#818cf8",
              width: 2,
            },
            itemStyle: {
              color: "#818cf8",
            },
          },
        ],
        // Add value labels at each vertex
        label: {
          show: true,
          formatter: ((params: { value?: number[]; dataIndex?: number }) => {
            if (!params.value) return "";
            const idx = params.dataIndex ?? 0;
            const val = params.value[idx];
            if (val === undefined || val === 0) return "";
            return val.toFixed(0);
          }) as unknown as string,
          color: "#818cf8",
          fontSize: 11,
          fontWeight: 700,
          distance: 8,
        },
      },
    ],
    // Add center score as a graphic overlay
    graphic: [
      {
        type: "group",
        left: "center",
        top: "center",
        children: [
          {
            type: "text",
            left: "center",
            top: "center",
            style: {
              text: `${averageScore.toFixed(0)}`,
              fill: "#818cf8",
              font: 'bold 28px "Inter", sans-serif',
            },
            textAlign: "center",
            textVerticalAlign: "middle",
          } as any,
          {
            type: "text",
            left: "center",
            top: 22,
            style: {
              text: "SCORE",
              fill: "#6b7a8f",
              font: '11px "Inter", sans-serif',
            },
            textAlign: "center",
            textVerticalAlign: "middle",
          } as any,
        ],
      },
    ],
  };

  chart.setOption(option, true);
}

function renderTrendChart(): void {
  const chart = getChartInstance(trendChartEl.value, trendChart);
  if (!chart) {
    return;
  }

  const sorted = [...financeData.value]
    .filter((item) => item.period)
    .sort((a, b) => Number(a.period.slice(0, 4)) - Number(b.period.slice(0, 4)))
    .slice(-5);

  const periods = sorted.map((item) => item.period);
  const roeSeries = sorted.map((item) => ratioToPercent(item.roe));
  const roicSeries = sorted.map((item) => ratioToPercent(item.roic));
  const profitGrowth = sorted.map((item, index) => {
    if (index === 0) {
      return null;
    }
    const previous = sorted[index - 1]?.net_profit;
    if (
      previous === null ||
      previous === undefined ||
      previous === 0 ||
      item.net_profit === null
    ) {
      return null;
    }
    return roundTo((item.net_profit / previous - 1) * 100, 2);
  });

  const option: EChartsOption = {
    backgroundColor: "transparent",
    color: ["#818cf8", "#67e8f9", "#f472b6"],
    legend: {
      top: 2,
      right: 8,
      textStyle: {
        color: "#8b96a8",
        fontSize: 11,
      },
    },
    grid: {
      left: 10,
      right: 16,
      top: 44,
      bottom: 16,
      containLabel: true,
    },
    tooltip: {
      trigger: "axis",
      borderColor: "rgba(99, 102, 241, 0.3)",
      backgroundColor: "rgba(13, 17, 23, 0.95)",
      textStyle: {
        color: "#f0f4f8",
      },
      valueFormatter: (value: unknown) =>
        typeof value === "number" ? `${value.toFixed(2)}%` : "--",
    },
    xAxis: {
      type: "category",
      data: periods,
      axisLine: {
        lineStyle: {
          color: "rgba(255, 255, 255, 0.06)",
        },
      },
      axisLabel: {
        color: "#6b7a8f",
        fontSize: 11,
      },
    },
    yAxis: [
      {
        type: "value",
        name: "ROE / ROIC",
        axisLabel: {
          color: "#6b7a8f",
          fontSize: 11,
          formatter: "{value}%",
        },
        splitLine: {
          lineStyle: {
            color: "rgba(255, 255, 255, 0.04)",
            type: "dashed",
          },
        },
      },
      {
        type: "value",
        name: "Profit Growth",
        axisLabel: {
          color: "#6b7a8f",
          fontSize: 11,
          formatter: "{value}%",
        },
        splitLine: {
          show: false,
        },
      },
    ],
    series: [
      {
        name: "ROE",
        type: "bar",
        data: roeSeries,
        barWidth: 14,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#818cf8" },
            { offset: 1, color: "rgba(99, 102, 241, 0.2)" },
          ]),
        },
      },
      {
        name: "ROIC",
        type: "bar",
        data: roicSeries,
        barWidth: 14,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#67e8f9" },
            { offset: 1, color: "rgba(6, 182, 212, 0.18)" },
          ]),
        },
      },
      {
        name: "Net Profit Growth",
        type: "line",
        yAxisIndex: 1,
        data: profitGrowth,
        smooth: true,
        symbolSize: 6,
        lineStyle: {
          width: 2.5,
          color: "#f472b6",
        },
        itemStyle: {
          color: "#f472b6",
        },
      },
    ],
  };

  chart.setOption(option, true);
}

function buildRadarMetrics(item: FinancialIndicators | null): RadarMetric[] {
  return [
    {
      name: "ROE",
      raw: item?.roe ?? null,
      value: normalizeRatio(item?.roe ?? null, 0.35),
    },
    {
      name: "ROIC",
      raw: item?.roic ?? null,
      value: normalizeRatio(item?.roic ?? null, 0.3),
    },
    {
      name: "Gross Margin",
      raw: item?.gross_margin ?? null,
      value: normalizeRatio(item?.gross_margin ?? null, 0.7),
    },
    {
      name: "Net Margin",
      raw: item?.net_margin ?? null,
      value: normalizeRatio(item?.net_margin ?? null, 0.35),
    },
  ];
}

function getBarChangeRatio(index: number): number | null {
  const current = klineData.value[index];
  const previous = klineData.value[index - 1];
  if (!current || !previous || previous.close === 0) {
    return null;
  }
  return current.close / previous.close - 1;
}

function normalizeRatio(value: number | null, excellentValue: number): number {
  if (value === null || !Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(100, roundTo((value / excellentValue) * 100, 2)));
}

function resizeCharts(): void {
  priceChart.value?.resize();
  radarChart.value?.resize();
  trendChart.value?.resize();
}

function disposeCharts(): void {
  priceChart.value?.dispose();
  radarChart.value?.dispose();
  trendChart.value?.dispose();
  priceChart.value = null;
  radarChart.value = null;
  trendChart.value = null;
}

function handleWatchlistSelect(event: Event): void {
  const detail = (event as CustomEvent).detail;
  if (detail?.symbol && detail.symbol !== activeSymbol.value) {
    symbolInput.value = detail.symbol;
    void (async () => {
      try {
        const result = await resolveStockFromInput(detail.symbol);
        await refreshDashboard();
      } catch {
        // Already handled in refreshDashboard
      }
    })();
  }
}

// Watch sidebar changes for chart resize after transition completes
watch(
  () => watchlist.sidebarOpen,
  (newVal, oldVal) => {
    if (newVal === oldVal) return;
    setTimeout(resizeCharts, 350);
  },
);

onMounted(() => {
  window.addEventListener("resize", resizeCharts);
  window.addEventListener("quant-select-stock", handleWatchlistSelect);
  void refreshDashboard();
});

onUnmounted(() => {
  window.removeEventListener("resize", resizeCharts);
  window.removeEventListener("quant-select-stock", handleWatchlistSelect);
  if (symbolSearchTimer !== null) {
    window.clearTimeout(symbolSearchTimer);
  }
  disposeCharts();
});
</script>

<template>
  <div
    v-loading="isLoading"
    class="dashboard"
    element-loading-background="rgba(13, 17, 23, 0.7)"
  >
    <!-- Top Header Bar -->
    <header class="dashboard-header">
      <div class="header-left">
        <div class="stock-info">
          <div class="stock-name-row">
            <h1 class="stock-name">{{ activeStockName }}</h1>
            <button
              class="star-btn"
              :class="{ active: watchlist.isWatched(activeSymbol) }"
              :title="
                watchlist.isWatched(activeSymbol)
                  ? 'Remove from watchlist'
                  : 'Add to watchlist'
              "
              @click="
                watchlist.toggleItem({
                  symbol: activeSymbol,
                  name: activeStockName,
                  market: 'US',
                })
              "
            >
              <span class="star-icon" v-if="watchlist.isWatched(activeSymbol)"
                >★</span
              >
              <span class="star-icon" v-else>☆</span>
              <span class="star-label">{{
                watchlist.isWatched(activeSymbol) ? "Watched" : "Watch"
              }}</span>
            </button>
          </div>
          <div class="stock-meta">
            <span class="stock-symbol quant-badge quant-badge-indigo">{{
              activeSymbol
            }}</span>
            <span class="stock-market">{{ latestTradeDate }}</span>
          </div>
        </div>
        <div class="stock-price">
          <span class="price-value">{{
            latestBar ? formatPrice(latestBar.close) : "--"
          }}</span>
          <span class="price-change" :class="marketToneClass">
            <span v-if="priceChange !== null && priceChange > 0">▲</span>
            <span v-else-if="priceChange !== null && priceChange < 0">▼</span>
            {{ priceChange === null ? "--" : formatPrice(priceChange) }}
            ({{
              priceChangeRatio === null
                ? "--"
                : formatPercent(priceChangeRatio)
            }})
          </span>
        </div>
      </div>

      <div class="header-right">
        <div class="search-group">
          <el-autocomplete
            v-model="symbolInput"
            class="symbol-input"
            :fetch-suggestions="fetchSymbolSuggestions"
            size="large"
            clearable
            placeholder="Search symbol or company..."
            popper-class="symbol-search-popper"
            value-key="label"
            @select="handleSymbolSelect"
            @keyup.enter="refreshDashboard"
          >
            <template #prefix>
              <span class="search-icon">🔍</span>
            </template>
            <template #default="{ item }">
              <div class="symbol-suggestion">
                <strong>{{ item.symbol }}</strong>
                <span>{{ item.name }}</span>
                <em>{{ item.market }}</em>
              </div>
            </template>
          </el-autocomplete>
          <el-button class="refresh-btn" size="large" @click="refreshDashboard">
            <span class="btn-icon">⟳</span>
            Refresh
          </el-button>
        </div>
      </div>
    </header>

    <!-- Metric Cards Row -->
    <section class="metrics-row">
      <div class="metric-card">
        <div class="metric-icon" style="background: rgba(99, 102, 241, 0.12)">
          <span style="color: #818cf8">$</span>
        </div>
        <div class="metric-body">
          <span class="metric-label">Latest Close</span>
          <strong class="metric-value">{{
            latestBar ? formatPrice(latestBar.close) : "--"
          }}</strong>
        </div>
      </div>
      <div class="metric-card">
        <div
          class="metric-icon"
          :class="marketToneClass"
          :style="
            priceChange !== null && priceChange > 0
              ? 'background: var(--quant-up-soft);'
              : priceChange !== null && priceChange < 0
                ? 'background: var(--quant-down-soft);'
                : 'background: rgba(107, 122, 143, 0.12);'
          "
        >
          <span>{{
            priceChange === null ? "–" : priceChange > 0 ? "▲" : "▼"
          }}</span>
        </div>
        <div class="metric-body">
          <span class="metric-label">Daily Change</span>
          <strong class="metric-value" :class="marketToneClass">
            {{ priceChange === null ? "--" : formatPrice(priceChange) }}
          </strong>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon" style="background: rgba(6, 182, 212, 0.12)">
          <span style="color: #67e8f9">%</span>
        </div>
        <div class="metric-body">
          <span class="metric-label">Change Ratio</span>
          <strong class="metric-value" :class="marketToneClass">
            {{
              priceChangeRatio === null ? "--" : formatPercent(priceChangeRatio)
            }}
          </strong>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon" style="background: rgba(245, 158, 11, 0.12)">
          <span style="color: #f59e0b">R</span>
        </div>
        <div class="metric-body">
          <span class="metric-label">Latest ROE</span>
          <strong class="metric-value">{{
            formatPercent(latestFinance?.roe ?? null)
          }}</strong>
        </div>
      </div>
    </section>

    <!-- Main Chart Area -->
    <section class="chart-section">
      <div class="chart-card">
        <!-- Header: title + period bar -->
        <div class="chart-card-header">
          <div class="chart-card-title">
            <h2>Price Chart</h2>
          </div>
          <div class="chart-controls">
            <div class="chart-type-toggle">
              <button
                :class="[
                  'chart-type-btn',
                  { active: chartType === 'candlestick' },
                ]"
                @click="
                  chartType = 'candlestick';
                  handleIndicatorConfigChange();
                "
                title="Candlestick"
              >
                📊
              </button>
              <button
                :class="['chart-type-btn', { active: chartType === 'line' }]"
                @click="
                  chartType = 'line';
                  handleIndicatorConfigChange();
                "
                title="Line chart"
              >
                📈
              </button>
            </div>
            <div class="period-bar">
              <button
                v-for="option in periodOptions"
                :key="option.value"
                :class="[
                  'period-btn',
                  { active: activePeriod === option.value },
                ]"
                @click="handlePeriodChange(option.value)"
              >
                {{ option.label }}
              </button>
            </div>
          </div>
        </div>

        <div class="chart-canvas-wrapper" :style="{ height: priceChartHeight }">
          <LoadingState
            v-if="isLoading"
            overlay
            text="Loading market data..."
          />
          <div
            ref="priceChartEl"
            class="chart-canvas"
            :style="{ height: '100%' }"
          />
        </div>

        <!-- Draggable resize handle -->
        <div
          class="chart-resize-handle"
          @mousedown.prevent="onResizeStart"
          title="Drag to resize chart height"
        >
          <span class="resize-dots">⋮</span>
        </div>

        <!-- Bottom toolbar like Tiger/Futu -->
        <div class="chart-toolbar">
          <!-- Overlay indicators (MA/EMA) -->
          <div class="toolbar-group">
            <span class="toolbar-group-label">Overlay</span>
            <div class="toolbar-btns">
              <button
                v-for="option in overlayIndicatorOptions"
                :key="option.value"
                :class="[
                  'toolbar-btn',
                  { active: selectedOverlayIndicators.includes(option.value) },
                ]"
                @click="toggleOverlayIndicator(option.value)"
              >
                {{ option.label }}
              </button>
            </div>
            <span class="toolbar-sep" />
          </div>

          <!-- Lower indicators (MACD/RSI/KDJ) -->
          <div class="toolbar-group">
            <span class="toolbar-group-label">Lower</span>
            <div class="toolbar-btns">
              <button
                v-for="option in subIndicatorOptions"
                :key="option"
                :class="[
                  'toolbar-btn',
                  { active: selectedSubIndicators.includes(option) },
                ]"
                @click="toggleSubIndicator(option)"
              >
                {{ option }}
              </button>
            </div>
          </div>

          <span class="toolbar-fill" />
          <span class="toolbar-period-label">{{ activePeriodLabel }}</span>
        </div>
      </div>
    </section>

    <!-- Empty state when no data loaded -->
    <section
      v-if="!isLoading && klineData.length === 0"
      class="empty-dashboard"
    >
      <div class="empty-icon-large">📊</div>
      <h3>No data loaded</h3>
      <p>Search for a stock symbol above to view charts and financial data</p>
    </section>

    <!-- Bottom Grid: Radar + Trend -->
    <section v-if="klineData.length > 0" class="bottom-grid">
      <div class="chart-card">
        <div class="chart-card-header">
          <div class="chart-card-title">
            <h2>Financial Moat</h2>
            <span class="chart-badge">{{ latestFinance?.period ?? "--" }}</span>
          </div>
        </div>
        <div ref="radarChartEl" class="chart-canvas-sm" />
      </div>

      <div class="chart-card">
        <div class="chart-card-header">
          <div class="chart-card-title">
            <h2>Capital Efficiency</h2>
            <span class="chart-note">ROE / ROIC / Net Profit Growth</span>
          </div>
        </div>
        <div ref="trendChartEl" class="chart-canvas-sm" />
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.dashboard {
  padding: 24px 28px 32px;
  min-height: 100vh;
}

/* ===== Header ===== */
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: flex-end;
  gap: 28px;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stock-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stock-name {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.3px;
  color: var(--quant-text-primary);
}

.star-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border: 1px solid var(--quant-glass-border);
  border-radius: var(--quant-radius-md);
  background: transparent;
  color: var(--quant-text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  line-height: 1;
}

.star-btn:hover {
  border-color: rgba(251, 191, 36, 0.3);
  background: rgba(251, 191, 36, 0.08);
  color: #fbbf24;
}

.star-btn.active {
  border-color: rgba(251, 191, 36, 0.3);
  background: rgba(251, 191, 36, 0.12);
  color: #fbbf24;
}

.star-btn.active:hover {
  background: rgba(251, 191, 36, 0.18);
  color: #f59e0b;
}

.star-icon {
  font-size: 16px;
  line-height: 1;
}

.star-label {
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
}

.stock-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stock-symbol {
  font-size: 11px;
  padding: 2px 10px;
}

.stock-market {
  font-size: 12px;
  color: var(--quant-text-muted);
}

.stock-price {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  padding-bottom: 2px;
}

.price-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.5px;
  color: var(--quant-text-primary);
}

.price-change {
  font-size: 14px;
  font-weight: 600;
}

/* ===== Header Right ===== */
.header-right {
  flex-shrink: 0;
}

.search-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.symbol-input {
  width: 300px;

  :deep(.el-input__wrapper) {
    border: 1px solid var(--quant-glass-border);
    border-radius: var(--quant-radius-md);
    background: var(--quant-glass-bg);
    backdrop-filter: blur(12px);
    box-shadow: none;
    padding-left: 8px;
  }

  :deep(.el-input__wrapper:hover) {
    border-color: var(--quant-border-strong);
  }

  :deep(.el-input__wrapper.is-focus) {
    border-color: var(--quant-accent-1);
    box-shadow: 0 0 0 3px var(--quant-accent-1-soft, rgba(99, 102, 241, 0.1));
  }

  :deep(.el-input__inner) {
    color: var(--quant-text-primary);
    font-size: 14px;
    &::placeholder {
      color: var(--quant-text-muted);
    }
  }
}

.search-icon {
  font-size: 14px;
  line-height: 1;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 40px;
  padding: 0 18px;
  border: 1px solid var(--quant-glass-border);
  border-radius: var(--quant-radius-md);
  background: var(--quant-glass-bg);
  backdrop-filter: blur(12px);
  color: var(--quant-text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: rgba(99, 102, 241, 0.3);
    background: rgba(99, 102, 241, 0.08);
  }

  .btn-icon {
    font-size: 16px;
  }
}

/* ===== Metrics Row ===== */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border: 1px solid var(--quant-glass-border);
  border-radius: var(--quant-radius-lg);
  background: var(--quant-glass-bg);
  backdrop-filter: blur(12px);
  box-shadow: var(--quant-glass-shadow);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card:hover {
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transform: translateY(-1px);
}

.metric-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--quant-radius-md);
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}

.metric-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.metric-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--quant-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--quant-text-primary);
  overflow-wrap: break-word;
}

/* ===== Chart Card ===== */
.chart-section {
  margin-bottom: 24px;
}

.chart-card {
  border: 1px solid var(--quant-glass-border);
  border-radius: var(--quant-radius-lg);
  background: var(--quant-glass-bg);
  backdrop-filter: blur(12px);
  box-shadow: var(--quant-glass-shadow);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chart-card:hover {
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.35);
}

.chart-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 22px 0;
}

.chart-card-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-card-title h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--quant-text-primary);
}

.chart-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: var(--quant-radius-full);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.12);
}

.chart-note {
  font-size: 12px;
  color: var(--quant-text-muted);
}

/* ===== Period Bar (header) ===== */
.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-type-toggle {
  display: flex;
  gap: 2px;
  padding: 4px;
  border-radius: var(--quant-radius-md);
  background: rgba(0, 0, 0, 0.15);
}

.chart-type-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--quant-text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}

.chart-type-btn:hover {
  color: var(--quant-text-secondary);
  background: rgba(255, 255, 255, 0.04);
}

.chart-type-btn.active {
  color: var(--quant-text-primary);
  background: rgba(99, 102, 241, 0.15);
}

.period-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--quant-radius-sm);
  padding: 2px;
}

.period-btn {
  padding: 4px 10px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--quant-text-muted);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.period-btn:hover {
  color: var(--quant-text-secondary);
  background: rgba(255, 255, 255, 0.04);
}

.period-btn.active {
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.15);
  font-weight: 600;
}

/* ===== Bottom Toolbar (Tiger/Futu style) ===== */
.chart-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-top: 1px solid var(--quant-glass-border);
  background: rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.toolbar-group-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--quant-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-right: 2px;
}

.toolbar-btns {
  display: flex;
  gap: 2px;
}

.toolbar-btn {
  padding: 3px 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--quant-text-muted);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.toolbar-btn:hover {
  color: var(--quant-text-secondary);
  background: rgba(255, 255, 255, 0.04);
}

.toolbar-btn.active {
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.15);
  font-weight: 600;
}

.toolbar-sep {
  display: inline-block;
  width: 1px;
  height: 16px;
  background: var(--quant-glass-border);
  margin: 0 4px;
}

.toolbar-fill {
  flex: 1;
}

.toolbar-period-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--quant-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  flex-shrink: 0;
}

/* ===== Resize Handle ===== */
.chart-resize-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 10px;
  cursor: row-resize;
  background: transparent;
  transition: background 0.2s;
  user-select: none;
}

.chart-resize-handle:hover {
  background: rgba(99, 102, 241, 0.08);
}

.resize-dots {
  font-size: 12px;
  color: var(--quant-text-muted);
  line-height: 1;
  letter-spacing: 2px;
  transition: color 0.2s;
}

.chart-resize-handle:hover .resize-dots {
  color: #818cf8;
}

.chart-canvas-wrapper {
  position: relative;
  width: 100%;
}

.chart-canvas {
  width: 100%;
  height: 100%;
  padding: 6px 6px 0;
}

.empty-dashboard {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-icon-large {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.3;
}

.empty-dashboard h3 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: var(--quant-text-secondary);
}

.empty-dashboard p {
  margin: 0;
  font-size: 14px;
  color: var(--quant-text-muted);
}

.chart-canvas-sm {
  width: 100%;
  height: 340px;
  padding: 6px 6px 0;
}

/* ===== Bottom Grid ===== */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

/* ===== Search Popper Overrides ===== */
:global(.symbol-search-popper) {
  border: 1px solid var(--quant-glass-border);
  border-radius: var(--quant-radius-md);
  background: var(--quant-bg-elevated);
  backdrop-filter: blur(16px);
  box-shadow: var(--quant-glass-shadow);
}

:global(.symbol-search-popper .el-autocomplete-suggestion__wrap) {
  background: transparent;
}

:global(.symbol-search-popper .el-autocomplete-suggestion__list) {
  background: transparent;
}

:global(.symbol-search-popper li) {
  background: transparent !important;
  color: var(--quant-text-secondary);
  transition: background 0.15s;
}

:global(.symbol-search-popper li:hover) {
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--quant-text-primary);
}

:global(.symbol-search-popper li.highlighted) {
  background: rgba(99, 102, 241, 0.1) !important;
  color: var(--quant-text-primary);
}

:global(.symbol-suggestion) {
  display: grid;
  grid-template-columns: 92px minmax(120px, 1fr) 38px;
  align-items: center;
  gap: 10px;
  width: 100%;
}

:global(.symbol-suggestion strong) {
  color: var(--quant-text-primary);
  font-size: 13px;
}

:global(.symbol-suggestion span) {
  overflow: hidden;
  color: var(--quant-text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:global(.symbol-suggestion em) {
  color: var(--quant-accent-1);
  font-size: 11px;
  font-style: normal;
  font-weight: 700;
}

/* ===== Tooltip ===== */
:global(.chart-tooltip-title) {
  margin-bottom: 6px;
  color: var(--quant-text-primary);
  font-weight: 700;
  font-size: 13px;
}

/* ===== Responsive ===== */
@media (max-width: 1200px) {
  .dashboard-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }

  .header-left {
    flex-wrap: wrap;
  }

  .header-right {
    width: 100%;
  }

  .search-group {
    width: 100%;
  }

  .symbol-input {
    flex: 1;
  }

  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 12px;
  }

  .dashboard-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .header-left {
    flex-wrap: wrap;
    gap: 12px;
    align-items: flex-start;
  }

  .stock-name {
    font-size: 20px;
  }

  .price-value {
    font-size: 24px;
  }

  .header-right {
    width: 100%;
  }

  .search-group {
    width: 100%;
    flex-wrap: wrap;
  }

  .symbol-input {
    flex: 1;
    min-width: 160px;
  }

  .refresh-btn {
    flex-shrink: 0;
  }

  .stock-price {
    align-items: flex-start;
  }

  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .metric-card {
    padding: 12px;
    gap: 10px;
  }

  .metric-icon {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }

  .metric-value {
    font-size: 16px;
  }

  .metric-label {
    font-size: 10px;
  }

  .chart-card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 14px 14px 0;
  }

  .chart-controls {
    flex-wrap: wrap;
    gap: 8px;
    width: 100%;
  }

  .period-bar {
    flex-wrap: wrap;
  }

  .period-btn {
    padding: 3px 7px;
    font-size: 10px;
  }

  .chart-type-btn {
    width: 28px;
    height: 24px;
    font-size: 12px;
  }

  .chart-toolbar {
    flex-wrap: wrap;
    gap: 4px;
    padding: 6px 10px;
  }

  .toolbar-btn {
    padding: 2px 6px;
    font-size: 10px;
  }

  .toolbar-group-label {
    font-size: 9px;
  }

  .chart-canvas-sm {
    height: 240px;
  }

  .bottom-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .star-btn {
    padding: 4px 10px;
    font-size: 12px;
  }

  .star-icon {
    font-size: 14px;
  }

  .star-label {
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .dashboard {
    padding: 8px;
  }

  .header-left {
    flex-direction: column;
    gap: 8px;
  }

  .stock-name-row {
    flex-wrap: wrap;
  }

  .stock-name {
    font-size: 18px;
  }

  .price-value {
    font-size: 22px;
  }

  .metrics-row {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .metric-value {
    font-size: 14px;
  }

  .symbol-input {
    min-width: 120px;
  }

  .search-group {
    flex-direction: column;
    gap: 8px;
  }

  .refresh-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
