import { ref } from "vue";
import { defineStore } from "pinia";

export interface WatchlistItem {
  symbol: string;
  name: string;
  market: string;
}

const STORAGE_KEY = "quant-watchlist";

function loadWatchlist(): WatchlistItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (item) =>
        typeof item === "object" &&
        typeof item.symbol === "string" &&
        typeof item.name === "string",
    );
  } catch {
    return [];
  }
}

function saveWatchlist(items: WatchlistItem[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export const useWatchlistStore = defineStore("watchlist", () => {
  const items = ref<WatchlistItem[]>(loadWatchlist());
  const sidebarOpen = ref(false);

  function isWatched(symbol: string): boolean {
    return items.value.some((item) => item.symbol === symbol);
  }

  function addItem(item: WatchlistItem): void {
    if (isWatched(item.symbol)) return;
    items.value.push(item);
    saveWatchlist(items.value);
  }

  function removeItem(symbol: string): void {
    items.value = items.value.filter((item) => item.symbol !== symbol);
    saveWatchlist(items.value);
  }

  function toggleItem(item: WatchlistItem): void {
    if (isWatched(item.symbol)) {
      removeItem(item.symbol);
    } else {
      addItem(item);
    }
  }

  function toggleSidebar(): void {
    sidebarOpen.value = !sidebarOpen.value;
  }

  function closeSidebar(): void {
    sidebarOpen.value = false;
  }

  function openSidebar(): void {
    sidebarOpen.value = true;
  }

  return {
    items,
    sidebarOpen,
    isWatched,
    addItem,
    removeItem,
    toggleItem,
    toggleSidebar,
    openSidebar,
    closeSidebar,
  };
});
