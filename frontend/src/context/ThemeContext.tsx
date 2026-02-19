import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { ThemeMode, ThemePalette } from "../types";
import { darkPalette, lightPalette } from "../styles/theme";

interface ThemeContextValue {
  mode: ThemeMode;
  palette: ThemePalette;
  toggle: () => void;
}

const STORAGE_KEY = "chronos-theme";

function getInitialMode(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // localStorage may not be available in tests
  }
  try {
    if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) return "dark";
  } catch {
    // matchMedia may not be available in tests
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
  const palette = mode === "dark" ? darkPalette : lightPalette;

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, mode);
  }, [mode]);

  const toggle = () => setMode((m) => (m === "dark" ? "light" : "dark"));

  return (
    <ThemeContext.Provider value={{ mode, palette, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}
