import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

export type ThemeMode = "light" | "dark";

export interface ThemeColors {
  bg: string;
  bgCard: string;
  bgHover: string;
  border: string;
  text: string;
  textMuted: string;
  accent: string;
  accentHover: string;
  navActive: string;
  navActiveBg: string;
  success: string;
  error: string;
  warning: string;
}

const darkColors: ThemeColors = {
  bg: "#0f172a",
  bgCard: "#1e293b",
  bgHover: "#334155",
  border: "#1e293b",
  text: "#f1f5f9",
  textMuted: "#94a3b8",
  accent: "#38bdf8",
  accentHover: "#7dd3fc",
  navActive: "#fff",
  navActiveBg: "#1e40af",
  success: "#22c55e",
  error: "#ef4444",
  warning: "#f59e0b",
};

const lightColors: ThemeColors = {
  bg: "#f8fafc",
  bgCard: "#ffffff",
  bgHover: "#f1f5f9",
  border: "#e2e8f0",
  text: "#0f172a",
  textMuted: "#64748b",
  accent: "#0284c7",
  accentHover: "#0369a1",
  navActive: "#fff",
  navActiveBg: "#2563eb",
  success: "#16a34a",
  error: "#dc2626",
  warning: "#d97706",
};

interface ThemeContextValue {
  mode: ThemeMode;
  colors: ThemeColors;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  mode: "dark",
  colors: darkColors,
  toggle: () => {},
});

function getInitialMode(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  const stored = localStorage.getItem("chronos-theme");
  if (stored === "light" || stored === "dark") return stored;
  if (typeof window.matchMedia === "function") {
    return window.matchMedia("(prefers-color-scheme: light)").matches
      ? "light"
      : "dark";
  }
  return "dark";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(getInitialMode);

  useEffect(() => {
    localStorage.setItem("chronos-theme", mode);
  }, [mode]);

  const toggle = useCallback(() => {
    setMode((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const colors = mode === "dark" ? darkColors : lightColors;

  const value = useMemo(
    () => ({ mode, colors, toggle }),
    [mode, colors, toggle],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}
