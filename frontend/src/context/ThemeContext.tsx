/**
 * Theme context for dark/light mode toggle.
 *
 * Persists preference in localStorage and defaults to system preference.
 */

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

export type ThemeMode = "light" | "dark";

export interface ThemePalette {
  background: string;
  surface: string;
  surfaceHover: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  border: string;
  primary: string;
  secondary: string;
  error: string;
  success: string;
  warning: string;
}

const lightPalette: ThemePalette = {
  background: "#f8fafc",
  surface: "#ffffff",
  surfaceHover: "#f1f5f9",
  textPrimary: "#0f172a",
  textSecondary: "#475569",
  textMuted: "#94a3b8",
  border: "#e2e8f0",
  primary: "#2563eb",
  secondary: "#7c3aed",
  error: "#dc2626",
  success: "#16a34a",
  warning: "#ca8a04",
};

const darkPalette: ThemePalette = {
  background: "#0f172a",
  surface: "#1e293b",
  surfaceHover: "#334155",
  textPrimary: "#e2e8f0",
  textSecondary: "#94a3b8",
  textMuted: "#64748b",
  border: "#334155",
  primary: "#3b82f6",
  secondary: "#a78bfa",
  error: "#ef4444",
  success: "#22c55e",
  warning: "#eab308",
};

interface ThemeContextValue {
  mode: ThemeMode;
  palette: ThemePalette;
  toggle: () => void;
}

const STORAGE_KEY = "chronos-theme-mode";

function getInitialMode(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  try {
    if (typeof window.matchMedia === "function") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    }
  } catch {
    // matchMedia unavailable (e.g. jsdom)
  }
  return "dark";
}

const ThemeContext = createContext<ThemeContextValue>({
  mode: "dark",
  palette: darkPalette,
  toggle: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(getInitialMode);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, mode);
  }, [mode]);

  const toggle = useCallback(() => {
    setMode((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const palette = mode === "dark" ? darkPalette : lightPalette;

  return (
    <ThemeContext.Provider value={{ mode, palette, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}

export { lightPalette, darkPalette };
