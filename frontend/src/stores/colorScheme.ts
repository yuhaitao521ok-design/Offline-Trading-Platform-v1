import { ref } from "vue";
import { defineStore } from "pinia";

export type ColorScheme = "red-up" | "green-up";

export const useColorSchemeStore = defineStore("colorScheme", () => {
  const saved = localStorage.getItem("quant-color-scheme");
  const current = ref<ColorScheme>(
    saved === "red-up" || saved === "green-up" ? saved : "red-up",
  );

  function applyScheme(scheme: ColorScheme): void {
    const root = document.documentElement;
    if (scheme === "red-up") {
      // Red for up, green for down (Chinese convention)
      root.style.setProperty("--quant-up", "#ef4444");
      root.style.setProperty("--quant-up-soft", "rgba(239, 68, 68, 0.12)");
      root.style.setProperty("--quant-up-border", "#ef4444");
      root.style.setProperty("--quant-up-fill", "rgba(239, 68, 68, 0.85)");
      root.style.setProperty("--quant-up-fill-soft", "rgba(239, 68, 68, 0.45)");
      root.style.setProperty("--quant-down", "#22c55e");
      root.style.setProperty("--quant-down-soft", "rgba(34, 197, 94, 0.12)");
      root.style.setProperty("--quant-down-border", "#22c55e");
      root.style.setProperty("--quant-down-fill", "rgba(34, 197, 94, 0.85)");
      root.style.setProperty(
        "--quant-down-fill-soft",
        "rgba(34, 197, 94, 0.45)",
      );
    } else {
      // Green for up, red for down (Western convention)
      root.style.setProperty("--quant-up", "#22c55e");
      root.style.setProperty("--quant-up-soft", "rgba(34, 197, 94, 0.12)");
      root.style.setProperty("--quant-up-border", "#22c55e");
      root.style.setProperty("--quant-up-fill", "rgba(34, 197, 94, 0.85)");
      root.style.setProperty("--quant-up-fill-soft", "rgba(34, 197, 94, 0.45)");
      root.style.setProperty("--quant-down", "#ef4444");
      root.style.setProperty("--quant-down-soft", "rgba(239, 68, 68, 0.12)");
      root.style.setProperty("--quant-down-border", "#ef4444");
      root.style.setProperty("--quant-down-fill", "rgba(239, 68, 68, 0.85)");
      root.style.setProperty(
        "--quant-down-fill-soft",
        "rgba(239, 68, 68, 0.45)",
      );
    }
  }

  function setScheme(scheme: ColorScheme): void {
    current.value = scheme;
    localStorage.setItem("quant-color-scheme", scheme);
    applyScheme(scheme);
  }

  // Apply initial scheme
  applyScheme(current.value);

  return {
    current,
    setScheme,
  };
});
