import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { Theme } from "../styles/theme";
import { darkTheme, lightTheme } from "../styles/theme";

type ThemeMode = "dark" | "light";

interface ThemeContextValue {
  theme: Theme;
  mode: ThemeMode;
  toggleTheme: () => void;
}

const STORAGE_KEY = "chronos-theme";

function getInitialMode(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  if (typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "dark";
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: darkTheme,
  mode: "dark",
  toggleTheme: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(getInitialMode);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, mode);
  }, [mode]);

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
