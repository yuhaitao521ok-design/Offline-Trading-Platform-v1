<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useWatchlistStore } from "../stores/watchlist";
import { getApiData } from "../api/http";
import type { KLineBar } from "../composables/types";
import { formatPrice, formatPercent } from "../composables/useFormatters";

const router = useRouter();
const watchlist = useWatchlistStore();

interface QuoteSnapshot {
  symbol: string;
  close: number;
  changeRatio: number | null;
}

const quotes = ref<Record<string, QuoteSnapshot>>({});
let refreshTimer: number | null = null;

const watchedSymbols = computed(() =>
  watchlist.items.map((item) => item.symbol),
);

async function refreshQuotes(): Promise<void> {
  if (watchedSymbols.value.length === 0) {
    quotes.value = {};
    return;
  }
  try {
    const results = await getApiData<Record<string, KLineBar[]>>(
      "/stock/kline/batch",
      {
        symbols: watchedSymbols.value.join(","),
        period: "1d",
        limit: 30,
      },
    );
    const nextQuotes: Record<string, QuoteSnapshot> = {};
    for (const symbol of watchedSymbols.value) {
      const bars = results[symbol] ?? [];
      const latest = bars.at(-1);
      const previous = bars.at(-2);
      if (!latest) continue;
      const changeRatio =
        previous && previous.close !== 0
          ? latest.close / previous.close - 1
          : null;
      nextQuotes[symbol] = {
        symbol,
        close: latest.close,
        changeRatio,
      };
    }
    quotes.value = nextQuotes;
  } catch {
    // Silently fail; quotes are best-effort
  }
}

function quoteClass(ratio: number | null): string {
  if (ratio === null || ratio === 0) return "quote-flat";
  return ratio > 0 ? "quote-up" : "quote-down";
}

function navigateToStock(symbol: string): void {
  router.push("/").then(() => {
    setTimeout(() => {
      window.dispatchEvent(
        new CustomEvent("quant-select-stock", { detail: { symbol } }),
      );
    }, 100);
  });
}

onMounted(() => {
  void refreshQuotes();
  refreshTimer = window.setInterval(refreshQuotes, 30_000);
});

onUnmounted(() => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer);
    refreshTimer = null;
  }
});
</script>

<template>
  <aside class="watchlist-sidebar" :class="{ open: watchlist.sidebarOpen }">
    <div class="sidebar-header">
      <h2 class="sidebar-title">
        <span class="title-icon">⭐</span>
        Watchlist
      </h2>
      <button class="close-btn" @click="watchlist.closeSidebar()">✕</button>
    </div>

    <div class="sidebar-body">
      <div v-if="watchlist.items.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <p class="empty-text">Your watchlist is empty</p>
        <p class="empty-hint">Search a stock and tap the star ☆ to add it</p>
      </div>

      <div v-else class="stock-list">
        <div
          v-for="item in watchlist.items"
          :key="item.symbol"
          class="stock-item"
          @click="navigateToStock(item.symbol)"
        >
          <div class="stock-left">
            <div class="stock-symbol-info">
              <span class="stock-symbol">{{ item.symbol }}</span>
              <span class="stock-market-tag">{{ item.market }}</span>
            </div>
            <div class="stock-name-line">
              <span class="stock-name">{{ item.name }}</span>
            </div>
          </div>
          <div class="stock-quote">
            <span class="quote-price">
              {{
                quotes[item.symbol]?.close !== undefined
                  ? formatPrice(quotes[item.symbol].close)
                  : "--"
              }}
            </span>
            <span
              v-if="quotes[item.symbol]?.changeRatio !== undefined"
              class="quote-change"
              :class="quoteClass(quotes[item.symbol].changeRatio)"
            >
              {{ formatPercent(quotes[item.symbol].changeRatio) }}
            </span>
          </div>
          <button
            class="remove-btn"
            title="Remove from watchlist"
            @click.stop="watchlist.removeItem(item.symbol)"
          >
            ✕
          </button>
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <span class="footer-count">{{ watchlist.items.length }} stocks</span>
    </div>
  </aside>
</template>

<style scoped lang="scss">
.watchlist-sidebar {
  display: flex;
  flex-direction: column;
  width: 0;
  min-width: 0;
  height: 100vh;
  border-left: none;
  background: var(--quant-bg-panel);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.watchlist-sidebar.open {
  width: 340px;
  min-width: 340px;
  border-left: 1px solid var(--quant-glass-border);
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--quant-glass-border);
}

.sidebar-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--quant-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 20px;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--quant-radius-sm);
  background: transparent;
  color: var(--quant-text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.06);
    color: var(--quant-text-primary);
  }
}

/* Body */
.sidebar-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 40px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--quant-text-secondary);
}

.empty-hint {
  margin: 0;
  font-size: 12px;
  color: var(--quant-text-muted);
}

/* Stock List */
.stock-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.stock-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.03);
  }

  &:hover .remove-btn {
    opacity: 1;
  }
}

.stock-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.stock-quote {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
  text-align: right;
  padding-right: 28px;
}

.quote-price {
  font-size: 14px;
  font-weight: 700;
  color: var(--quant-text-primary);
}

.quote-change {
  font-size: 11px;
  font-weight: 600;
}

.quote-up {
  color: var(--quant-up-red);
}

.quote-down {
  color: var(--quant-down-green);
}

.quote-flat {
  color: var(--quant-flat-gray);
}

.stock-symbol-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stock-symbol {
  font-size: 14px;
  font-weight: 700;
  color: var(--quant-text-primary);
  letter-spacing: -0.2px;
}

.stock-market-tag {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  color: #a5b4fc;
  background: rgba(99, 102, 241, 0.12);
}

.stock-name-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stock-name {
  font-size: 12px;
  color: var(--quant-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 4px;
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
  font-size: 10px;
  cursor: pointer;
  opacity: 0;
  transition: all 0.15s;

  &:hover {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }
}

/* Footer */
.sidebar-footer {
  padding: 14px 20px;
  border-top: 1px solid var(--quant-glass-border);
}

.footer-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--quant-text-muted);
}

/* ===== Mobile Responsive ===== */
@media (max-width: 768px) {
  .watchlist-sidebar.open {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    z-index: 400;
    width: 100%;
    min-width: 100%;
    background: var(--quant-bg-page);
  }

  .sidebar-header {
    padding: 16px 16px 12px;
  }

  .sidebar-title {
    font-size: 16px;
  }

  .stock-item {
    padding: 10px 16px;
  }

  .stock-symbol {
    font-size: 13px;
  }

  .quote-price {
    font-size: 13px;
  }

  .sidebar-footer {
    padding: 12px 16px;
  }
}
</style>
