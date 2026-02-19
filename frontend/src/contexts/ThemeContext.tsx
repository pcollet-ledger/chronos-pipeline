import { createContext, useContext, useState, useCallback } from "react";
import type { ReactNode } from "react";
import type { Theme } from "../types";

const darkTheme: Theme = {
  bg: "#0f172a",
  bgCard: "#1e293b",
  bgInput: "#1e293b",
  border: "#334155",
  text: "#e2e8f0",
  textMuted: "#94a3b8",
  textDim: "#64748b",
  accent: "#38bdf8",
  success: "#22c55e",
  error: "#ef4444",
  warning: "#eab308",
  info: "#3b82f6",
};

const lightTheme: Theme = {
  bg: "#f8fafc",
  bgCard: "#ffffff",
  bgInput: "#f1f5f9",
  border: "#e2e8f0",
  text: "#1e293b",
  textMuted: "#475569",
  textDim: "#94a3b8",
  accent: "#0284c7",
  success: "#16a34a",
  error: "#dc2626",
  warning: "#ca8a04",
  info: "#2563eb",
};

type ThemeMode = "dark" | "light";

interface ThemeContextValue {
  theme: Theme;
  mode: ThemeMode;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: darkTheme,
  mode: "dark",
  toggleTheme: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>("dark");

  const toggleTheme = useCallback(() => {
    setMode((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const theme = mode === "dark" ? darkTheme : lightTheme;

  return (
    <ThemeContext.Provider value={{ theme, mode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}

export { darkTheme, lightTheme };
