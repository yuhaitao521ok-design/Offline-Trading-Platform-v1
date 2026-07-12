import { ref } from "vue";
import { defineStore } from "pinia";

export type Locale = "zh-CN" | "en";

export const localeLabels: Record<Locale, { name: string; flag: string }> = {
  "zh-CN": { name: "中文简体", flag: "🇨🇳" },
  en: { name: "English", flag: "🇬🇧" },
};

export const useLocaleStore = defineStore("locale", () => {
  const saved = localStorage.getItem("quant-locale");
  const current = ref<Locale>(
    saved === "zh-CN" || saved === "en" ? saved : "en",
  );

  function applyLocale(locale: Locale): void {
    const root = document.documentElement;
    if (locale === "zh-CN") {
      root.style.setProperty(
        "--quant-font-family",
        '"Noto Sans SC", "PingFang SC", "Microsoft YaHei", "Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      );
    } else {
      root.style.setProperty(
        "--quant-font-family",
        '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif',
      );
    }
  }

  function setLocale(locale: Locale): void {
    current.value = locale;
    localStorage.setItem("quant-locale", locale);
    applyLocale(locale);
  }

  // Apply initial locale
  applyLocale(current.value);

  return {
    current,
    setLocale,
  };
});
