import type { ThemePalette } from "../types";

export const lightPalette: ThemePalette = {
  background: "#f8fafc",
  surface: "#ffffff",
  text: "#0f172a",
  textSecondary: "#64748b",
  primary: "#2563eb",
  primaryLight: "#3b82f6",
  primaryDark: "#1e40af",
  secondary: "#a78bfa",
  error: "#ef4444",
  errorLight: "#fca5a5",
  success: "#22c55e",
  successLight: "#86efac",
  warning: "#eab308",
  warningLight: "#fde047",
  info: "#38bdf8",
  border: "#e2e8f0",
};

export const darkPalette: ThemePalette = {
  background: "#0f172a",
  surface: "#1e293b",
  text: "#e2e8f0",
  textSecondary: "#94a3b8",
  primary: "#2563eb",
  primaryLight: "#3b82f6",
  primaryDark: "#1e40af",
  secondary: "#a78bfa",
  error: "#ef4444",
  errorLight: "#fca5a5",
  success: "#22c55e",
  successLight: "#86efac",
  warning: "#eab308",
  warningLight: "#fde047",
  info: "#38bdf8",
  border: "#334155",
};

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "16px",
  lg: "24px",
  xl: "32px",
  xxl: "48px",
} as const;

export const borderRadius = {
  sm: "4px",
  md: "8px",
  lg: "12px",
  full: "9999px",
} as const;

export const fontSize = {
  xs: "11px",
  sm: "12px",
  md: "13px",
  base: "14px",
  lg: "16px",
  xl: "18px",
  xxl: "20px",
  heading: "28px",
} as const;

export const fontWeight = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

export const shadow = {
  sm: "0 1px 2px rgba(0,0,0,0.05)",
  md: "0 4px 6px rgba(0,0,0,0.1)",
  lg: "0 4px 20px rgba(0,0,0,0.3)",
} as const;

export const transition = {
  fast: "150ms ease",
  normal: "200ms ease",
  slow: "300ms ease",
} as const;

export const theme = {
  light: lightPalette,
  dark: darkPalette,
  spacing,
  borderRadius,
  fontSize,
  fontWeight,
  shadow,
  transition,
} as const;

export type Theme = typeof theme;
