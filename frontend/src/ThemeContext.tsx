import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { darkTheme, lightTheme } from "./theme";
import type { ThemeTokens } from "./theme";

type Mode = "dark" | "light";

interface ThemeContextValue {
  mode: Mode;
  theme: ThemeTokens;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  mode: "dark",
  theme: darkTheme,
  toggleTheme: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>("dark");

  const toggleTheme = useCallback(() => {
    setMode((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const value = useMemo<ThemeContextValue>(
    () => ({
      mode,
      theme: mode === "dark" ? darkTheme : lightTheme,
      toggleTheme,
    }),
    [mode, toggleTheme],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext);
}
