<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useWatchlistStore } from "./stores/watchlist";
import { useLocaleStore } from "./stores/locale";
import WatchlistSidebar from "./components/WatchlistSidebar.vue";

const router = useRouter();
const route = useRoute();
const watchlist = useWatchlistStore();
const localeStore = useLocaleStore();
const sidebarCollapsed = ref(false);
const mobileNavOpen = ref(false);
const isMobile = ref(false);

function checkMobile() {
  isMobile.value = window.innerWidth < 768;
}

onMounted(() => {
  checkMobile();
  window.addEventListener("resize", checkMobile);
});

onUnmounted(() => {
  window.removeEventListener("resize", checkMobile);
});

const navItems = [
  { path: "/", label: "Dashboard", icon: "📊" },
  { path: "/settings", label: "Settings", icon: "⚙️" },
];

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value;
}

function handleNavClick(item: { path: string; label: string }) {
  if (item.label === "Watchlist") {
    watchlist.toggleSidebar();
  } else {
    router.push(item.path);
  }
  mobileNavOpen.value = false;
}

function toggleMobileNav() {
  mobileNavOpen.value = !mobileNavOpen.value;
}
</script>

<template>
  <div
    class="app-layout"
    :class="{
      'sidebar-collapsed': sidebarCollapsed,
      'is-mobile': isMobile,
    }"
  >
    <!-- Desktop Sidebar -->
    <aside class="app-sidebar" v-if="!isMobile">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <span class="logo-icon">◆</span>
          <span class="logo-text" v-show="!sidebarCollapsed">QuantView</span>
        </div>
        <button class="sidebar-toggle" @click="toggleSidebar">
          <span v-if="sidebarCollapsed">→</span>
          <span v-else>←</span>
        </button>
      </div>

      <nav class="sidebar-nav">
        <a
          v-for="item in navItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
          @click="handleNavClick(item)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label" v-show="!sidebarCollapsed">{{
            item.label
          }}</span>
        </a>

        <!-- Watchlist toggle -->
        <a
          class="nav-item"
          :class="{ active: watchlist.sidebarOpen }"
          @click="watchlist.toggleSidebar()"
        >
          <span class="nav-icon">⭐</span>
          <span class="nav-label" v-show="!sidebarCollapsed">
            Watchlist
            <span v-if="watchlist.items.length > 0" class="nav-badge">{{
              watchlist.items.length
            }}</span>
          </span>
        </a>
      </nav>

      <div class="sidebar-footer" v-show="!sidebarCollapsed">
        <div class="user-info">
          <div class="user-avatar">U</div>
          <div class="user-details">
            <span class="user-name">Trader</span>
            <span class="user-status">Online</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- Mobile Top Bar -->
    <header class="mobile-topbar" v-if="isMobile">
      <div class="mobile-topbar-left">
        <button class="mobile-menu-btn" @click="toggleMobileNav">
          <span>☰</span>
        </button>
        <span class="mobile-logo">◆ QuantView</span>
      </div>
      <div class="mobile-topbar-right">
        <button class="mobile-watchlist-btn" @click="watchlist.toggleSidebar()">
          <span>⭐</span>
          <span v-if="watchlist.items.length > 0" class="mobile-badge">{{
            watchlist.items.length
          }}</span>
        </button>
      </div>
    </header>

    <!-- Mobile Drawer Navigation -->
    <transition name="mobile-nav">
      <div
        v-if="isMobile && mobileNavOpen"
        class="mobile-nav-overlay"
        @click="mobileNavOpen = false"
      >
        <nav class="mobile-nav-drawer" @click.stop>
          <div class="mobile-nav-header">
            <span class="mobile-nav-title">Navigation</span>
            <button class="mobile-nav-close" @click="mobileNavOpen = false">
              ✕
            </button>
          </div>
          <a
            v-for="item in navItems"
            :key="item.path"
            class="mobile-nav-item"
            :class="{ active: route.path === item.path }"
            @click="handleNavClick(item)"
          >
            <span class="mobile-nav-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </a>
          <a
            class="mobile-nav-item"
            :class="{ active: watchlist.sidebarOpen }"
            @click="
              watchlist.toggleSidebar();
              mobileNavOpen = false;
            "
          >
            <span class="mobile-nav-icon">⭐</span>
            <span>Watchlist</span>
          </a>
        </nav>
      </div>
    </transition>

    <!-- Main Content -->
    <main class="app-main">
      <RouterView />
    </main>

    <!-- Watchlist Sidebar -->
    <WatchlistSidebar />
  </div>
</template>

<style scoped lang="scss">
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--quant-bg-page);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ===== Sidebar ===== */
.app-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  width: 240px;
  height: 100vh;
  border-right: 1px solid var(--quant-glass-border);
  background: var(--quant-glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-collapsed .app-sidebar {
  width: 64px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px;
  border-bottom: 1px solid var(--quant-glass-border);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  font-size: 22px;
  background: var(--quant-gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
  background: var(--quant-gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--quant-glass-border);
  border-radius: var(--quant-radius-sm);
  background: transparent;
  color: var(--quant-text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.sidebar-toggle:hover {
  border-color: var(--quant-accent-1);
  color: var(--quant-text-primary);
  background: rgba(99, 102, 241, 0.1);
}

/* ===== Navigation ===== */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 8px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--quant-radius-md);
  color: var(--quant-text-muted);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
}

.nav-item:hover {
  color: var(--quant-text-secondary);
  background: rgba(255, 255, 255, 0.04);
}

.nav-item.active {
  color: var(--quant-text-primary);
  background: rgba(99, 102, 241, 0.12);
}

.nav-icon {
  flex-shrink: 0;
  font-size: 18px;
  width: 24px;
  text-align: center;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.nav-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: var(--quant-accent-1);
  color: white;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

/* ===== Sidebar Footer ===== */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--quant-glass-border);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--quant-radius-full);
  background: var(--quant-gradient-primary);
  color: white;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--quant-text-primary);
}

.user-status {
  font-size: 11px;
  color: var(--quant-down-green);
}

/* ===== Main Content ===== */
.app-main {
  flex: 1;
  margin-left: 240px;
  min-height: 100vh;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-collapsed .app-main {
  margin-left: 64px;
}

/* ===== Mobile Layout ===== */
.is-mobile .app-main {
  margin-left: 0;
  padding-top: 52px;
}

.mobile-topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 12px;
  background: var(--quant-glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--quant-glass-border);
}

.mobile-topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mobile-menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--quant-radius-sm);
  background: transparent;
  color: var(--quant-text-primary);
  font-size: 20px;
  cursor: pointer;
}

.mobile-menu-btn:active {
  background: rgba(255, 255, 255, 0.06);
}

.mobile-logo {
  font-size: 16px;
  font-weight: 700;
  background: var(--quant-gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.mobile-topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-watchlist-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--quant-radius-sm);
  background: transparent;
  color: var(--quant-text-primary);
  font-size: 18px;
  cursor: pointer;
}

.mobile-watchlist-btn:active {
  background: rgba(255, 255, 255, 0.06);
}

.mobile-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: var(--quant-accent-1);
  color: white;
  font-size: 9px;
  font-weight: 700;
  line-height: 1;
}

/* ===== Mobile Nav Overlay ===== */
.mobile-nav-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 300;
  background: rgba(0, 0, 0, 0.5);
}

.mobile-nav-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  display: flex;
  flex-direction: column;
  background: var(--quant-bg-panel);
  border-right: 1px solid var(--quant-glass-border);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
}

.mobile-nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 16px;
  border-bottom: 1px solid var(--quant-glass-border);
}

.mobile-nav-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--quant-text-primary);
}

.mobile-nav-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--quant-radius-sm);
  background: transparent;
  color: var(--quant-text-muted);
  font-size: 16px;
  cursor: pointer;
}

.mobile-nav-close:active {
  background: rgba(255, 255, 255, 0.06);
}

.mobile-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  color: var(--quant-text-muted);
  font-size: 15px;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s;
}

.mobile-nav-item:active {
  background: rgba(255, 255, 255, 0.04);
}

.mobile-nav-item.active {
  color: var(--quant-text-primary);
  background: rgba(99, 102, 241, 0.12);
}

.mobile-nav-icon {
  font-size: 20px;
  width: 28px;
  text-align: center;
  flex-shrink: 0;
}

/* ===== Mobile Nav Transition ===== */
.mobile-nav-enter-active,
.mobile-nav-leave-active {
  transition: opacity 0.2s ease;
}

.mobile-nav-enter-active .mobile-nav-drawer,
.mobile-nav-leave-active .mobile-nav-drawer {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.mobile-nav-enter-from,
.mobile-nav-leave-to {
  opacity: 0;
}

.mobile-nav-enter-from .mobile-nav-drawer,
.mobile-nav-leave-to .mobile-nav-drawer {
  transform: translateX(-100%);
}
</style>
