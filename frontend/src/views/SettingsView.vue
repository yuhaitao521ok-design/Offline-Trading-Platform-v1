<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { useThemeStore, themePresets } from "../stores/theme";
import { useColorSchemeStore } from "../stores/colorScheme";
import type { ColorScheme } from "../stores/colorScheme";
import { useLocaleStore, localeLabels } from "../stores/locale";
import type { Locale } from "../stores/locale";

const themeStore = useThemeStore();
const colorSchemeStore = useColorSchemeStore();
const localeStore = useLocaleStore();
const activeTheme = ref(themeStore.currentTheme.id);
const activeColorScheme = ref(colorSchemeStore.current);
const activeLocale = ref(localeStore.current);

function selectLocale(locale: Locale) {
  activeLocale.value = locale;
  localeStore.setLocale(locale);
  ElMessage({
    message:
      locale === "zh-CN"
        ? "语言已切换为中文简体"
        : "Language switched to English",
    type: "success",
    duration: 1500,
  });
}

function selectTheme(themeId: string) {
  activeTheme.value = themeId;
  themeStore.setTheme(themeId);
  ElMessage({
    message: `Theme changed to ${themePresets.find((t) => t.id === themeId)?.name}`,
    type: "success",
    duration: 1500,
  });
}

function selectColorScheme(scheme: ColorScheme) {
  activeColorScheme.value = scheme;
  colorSchemeStore.setScheme(scheme);
  ElMessage({
    message:
      scheme === "red-up"
        ? "Up ▲ Red · Down ▼ Green (Chinese convention)"
        : "Up ▲ Green · Down ▼ Red (Western convention)",
    type: "success",
    duration: 1500,
  });
}

const colorSwatches = computed(() => {
  const root = getComputedStyle(document.documentElement);
  return [
    {
      label: "Page BG",
      value: root.getPropertyValue("--quant-bg-page").trim(),
    },
    {
      label: "Primary Accent",
      value: root.getPropertyValue("--quant-accent-1").trim(),
    },
    {
      label: "Text Primary",
      value: root.getPropertyValue("--quant-text-primary").trim(),
    },
    {
      label: "Text Muted",
      value: root.getPropertyValue("--quant-text-muted").trim(),
    },
    {
      label: "Border",
      value: root.getPropertyValue("--quant-glass-border").trim(),
    },
    {
      label: "Card BG",
      value: root.getPropertyValue("--quant-glass-bg").trim(),
    },
  ];
});
</script>

<template>
  <div class="settings-page">
    <div class="settings-header">
      <div>
        <h1 class="page-title">Settings</h1>
        <p class="page-subtitle">Customize your experience</p>
      </div>
    </div>

    <!-- Theme Section -->
    <section class="settings-section">
      <div class="section-heading">
        <div class="section-icon">🎨</div>
        <div>
          <h2>Theme & Appearance</h2>
          <p class="section-desc">Choose from 8 handcrafted color schemes</p>
        </div>
      </div>

      <div class="theme-grid">
        <div
          v-for="theme in themePresets"
          :key="theme.id"
          class="theme-card"
          :class="{ active: activeTheme === theme.id }"
          @click="selectTheme(theme.id)"
        >
          <!-- Preview Swatches -->
          <div class="theme-preview" :style="{ background: theme.preview.bg }">
            <div class="swatch-row">
              <span
                class="swatch"
                :style="{ background: theme.preview.primary }"
              />
              <span
                class="swatch"
                :style="{ background: theme.preview.secondary }"
              />
              <span
                class="swatch"
                :style="{ background: theme.preview.surface }"
              />
            </div>
            <div class="preview-bars">
              <div
                class="preview-bar"
                :style="{ background: theme.preview.surface }"
              />
              <div
                class="preview-bar short"
                :style="{ background: theme.preview.surface }"
              />
            </div>
          </div>

          <!-- Card Body -->
          <div class="theme-info">
            <div class="theme-name-row">
              <span class="theme-name">{{ theme.name }}</span>
              <span v-if="activeTheme === theme.id" class="theme-check">✓</span>
            </div>
            <p class="theme-desc">{{ theme.description }}</p>
          </div>

          <!-- Active indicator glow -->
          <div v-if="activeTheme === theme.id" class="active-glow" />
        </div>
      </div>
    </section>

    <!-- Color Scheme Section -->
    <section class="settings-section">
      <div class="section-heading">
        <div class="section-icon">📈</div>
        <div>
          <h2>Up/Down Color Convention</h2>
          <p class="section-desc">
            Choose how price increases and decreases are displayed
          </p>
        </div>
      </div>

      <div class="scheme-row">
        <div
          class="scheme-card"
          :class="{ active: activeColorScheme === 'red-up' }"
          @click="selectColorScheme('red-up')"
        >
          <div class="scheme-preview">
            <div class="scheme-bar up-red">▲ +5.20%</div>
            <div class="scheme-bar down-green">▼ -2.10%</div>
          </div>
          <div class="scheme-info">
            <div class="scheme-name-row">
              <span class="scheme-name">Red Up / Green Down</span>
              <span v-if="activeColorScheme === 'red-up'" class="scheme-check"
                >✓</span
              >
            </div>
            <p class="scheme-desc">
              Chinese convention — red for gains, green for losses
            </p>
          </div>
        </div>

        <div
          class="scheme-card"
          :class="{ active: activeColorScheme === 'green-up' }"
          @click="selectColorScheme('green-up')"
        >
          <div class="scheme-preview">
            <div class="scheme-bar up-green">▲ +5.20%</div>
            <div class="scheme-bar down-red">▼ -2.10%</div>
          </div>
          <div class="scheme-info">
            <div class="scheme-name-row">
              <span class="scheme-name">Green Up / Red Down</span>
              <span v-if="activeColorScheme === 'green-up'" class="scheme-check"
                >✓</span
              >
            </div>
            <p class="scheme-desc">
              Western convention — green for gains, red for losses
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Language Section -->
    <section class="settings-section">
      <div class="section-heading">
        <div class="section-icon">🌐</div>
        <div>
          <h2>Language / 语言</h2>
          <p class="section-desc">Choose your preferred display language</p>
        </div>
      </div>

      <div class="scheme-row">
        <div
          v-for="(meta, locale) in localeLabels"
          :key="locale"
          class="scheme-card"
          :class="{ active: activeLocale === locale }"
          @click="selectLocale(locale)"
        >
          <div class="scheme-preview language-preview">
            <span class="language-flag">{{ meta.flag }}</span>
            <span class="language-name">{{ meta.name }}</span>
          </div>
          <div class="scheme-info">
            <div class="scheme-name-row">
              <span class="scheme-name">{{ meta.name }}</span>
              <span v-if="activeLocale === locale" class="scheme-check">✓</span>
            </div>
            <p class="scheme-desc">
              {{ locale === "zh-CN" ? "简体中文界面" : "English interface" }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Color Guide -->
    <section class="settings-section">
      <div class="section-heading">
        <div class="section-icon">🔤</div>
        <div>
          <h2>Current Theme Colors</h2>
          <p class="section-desc">
            {{ themePresets.find((t) => t.id === activeTheme)?.name }}
          </p>
        </div>
      </div>

      <div class="color-guide">
        <div
          v-for="swatch in colorSwatches"
          :key="swatch.label"
          class="color-item"
        >
          <div class="color-block" :style="{ background: swatch.value }" />
          <div class="color-label">{{ swatch.label }}</div>
          <div class="color-value">{{ swatch.value }}</div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.settings-page {
  padding: 24px 28px 48px;
  min-height: 100vh;
}

/* ===== Header ===== */
.settings-header {
  margin-bottom: 32px;
}

.page-title {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--quant-text-primary);
}

.page-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--quant-text-muted);
}

/* ===== Section ===== */
.settings-section {
  margin-bottom: 40px;
}

.section-heading {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
}

.section-icon {
  font-size: 24px;
  line-height: 1;
  flex-shrink: 0;
}

.section-heading h2 {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 600;
  color: var(--quant-text-primary);
}

.section-desc {
  margin: 0;
  font-size: 13px;
  color: var(--quant-text-muted);
}

/* ===== Theme Grid ===== */
.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.theme-card {
  position: relative;
  border: 1px solid var(--quant-glass-border);
  border-radius: var(--quant-radius-lg);
  background: var(--quant-glass-bg);
  backdrop-filter: blur(12px);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.theme-card:hover {
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
}

.theme-card.active {
  border-color: var(--quant-accent-1);
  box-shadow:
    0 0 0 1px var(--quant-accent-1),
    0 8px 32px rgba(0, 0, 0, 0.25);
}

/* Preview */
.theme-preview {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.swatch-row {
  display: flex;
  gap: 8px;
}

.swatch {
  width: 32px;
  height: 32px;
  border-radius: var(--quant-radius-sm);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.preview-bars {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preview-bar {
  height: 6px;
  border-radius: 3px;
  opacity: 0.6;
  width: 80%;
}

.preview-bar.short {
  width: 55%;
}

/* Info */
.theme-info {
  padding: 14px 20px;
  border-top: 1px solid var(--quant-glass-border);
}

.theme-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.theme-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--quant-text-primary);
}

.theme-check {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--quant-accent-1);
  color: white;
  font-size: 11px;
  font-weight: 700;
}

.theme-desc {
  margin: 0;
  font-size: 12px;
  color: var(--quant-text-muted);
  line-height: 1.4;
}

/* Active glow border */
.active-glow {
  position: absolute;
  inset: -1px;
  border-radius: var(--quant-radius-lg);
  background: transparent;
  pointer-events: none;
  box-shadow:
    0 0 20px rgba(99, 102, 241, 0.15),
    inset 0 0 20px rgba(99, 102, 241, 0.05);
}

/* ===== Scheme Cards ===== */
.scheme-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.scheme-card {
  border: 1px solid var(--quant-glass-border);
  border-radius: var(--quant-radius-lg);
  background: var(--quant-glass-bg);
  backdrop-filter: blur(12px);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.scheme-card:hover {
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
}

.scheme-card.active {
  border-color: var(--quant-accent-1);
  box-shadow:
    0 0 0 1px var(--quant-accent-1),
    0 8px 32px rgba(0, 0, 0, 0.25);
}

.scheme-preview {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--quant-bg-page);
}

.language-preview {
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.language-flag {
  font-size: 32px;
  line-height: 1;
}

.language-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--quant-text-primary);
}

.scheme-bar {
  padding: 8px 14px;
  border-radius: var(--quant-radius-sm);
  font-size: 14px;
  font-weight: 700;
  font-family: "SF Mono", "Fira Code", monospace;
}

.scheme-bar.up-red {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.scheme-bar.down-green {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.scheme-bar.up-green {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.scheme-bar.down-red {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.scheme-info {
  padding: 14px 20px;
  border-top: 1px solid var(--quant-glass-border);
}

.scheme-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.scheme-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--quant-text-primary);
}

.scheme-check {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--quant-accent-1);
  color: white;
  font-size: 11px;
  font-weight: 700;
}

.scheme-desc {
  margin: 0;
  font-size: 12px;
  color: var(--quant-text-muted);
  line-height: 1.4;
}

/* ===== Color Guide ===== */
.color-guide {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.color-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--quant-glass-border);
  border-radius: var(--quant-radius-md);
  background: var(--quant-glass-bg);
}

.color-block {
  width: 28px;
  height: 28px;
  border-radius: var(--quant-radius-sm);
  border: 1px solid var(--quant-glass-border);
  flex-shrink: 0;
}

.color-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--quant-text-secondary);
  flex: 1;
}

.color-value {
  font-size: 11px;
  font-family: "SF Mono", "Fira Code", monospace;
  color: var(--quant-text-muted);
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .settings-page {
    padding: 16px;
  }

  .theme-grid {
    grid-template-columns: 1fr;
  }

  .color-guide {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
