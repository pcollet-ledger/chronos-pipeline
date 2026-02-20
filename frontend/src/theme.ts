// ---------------------------------------------------------------------------
// Spacing scale – xs through xxl
// ---------------------------------------------------------------------------
export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "24px",
  xxl: "32px",
} as const;

export type SpacingScale = typeof spacing;

// ---------------------------------------------------------------------------
// Border-radius values
// ---------------------------------------------------------------------------
export const radii = {
  sm: "4px",
  md: "6px",
  lg: "8px",
  xl: "12px",
  full: "9999px",
} as const;

export type Radii = typeof radii;

// ---------------------------------------------------------------------------
// Font sizes
// ---------------------------------------------------------------------------
export const fontSize = {
  xs: "11px",
  sm: "12px",
  md: "13px",
  lg: "14px",
  xl: "16px",
  xxl: "18px",
  h1: "20px",
  h2: "28px",
} as const;

export type FontSize = typeof fontSize;

// ---------------------------------------------------------------------------
// Font weights
// ---------------------------------------------------------------------------
export const fontWeight = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

export type FontWeight = typeof fontWeight;

// ---------------------------------------------------------------------------
// Shadow definitions
// ---------------------------------------------------------------------------
export const shadows = {
  sm: "0 1px 2px rgba(0,0,0,0.05)",
  md: "0 1px 3px rgba(0,0,0,0.1)",
  lg: "0 4px 20px rgba(0,0,0,0.15)",
  dark: {
    sm: "0 1px 2px rgba(0,0,0,0.2)",
    md: "0 1px 3px rgba(0,0,0,0.4)",
    lg: "0 4px 20px rgba(0,0,0,0.3)",
  },
} as const;

export type Shadows = typeof shadows;

// ---------------------------------------------------------------------------
// Transition durations
// ---------------------------------------------------------------------------
export const transition = {
  fast: "100ms ease",
  normal: "200ms ease",
  slow: "300ms ease",
} as const;

export type Transition = typeof transition;

// ---------------------------------------------------------------------------
// Colour palette – primary, secondary, error, warning, success, info
// Each has a base, light, and dark variant.
// ---------------------------------------------------------------------------
export const palette = {
  primary: { base: "#2563eb", light: "#3b82f6", dark: "#1d4ed8" },
  secondary: { base: "#6b7280", light: "#9ca3af", dark: "#4b5563" },
  error: { base: "#dc2626", light: "#ef4444", dark: "#b91c1c" },
  warning: { base: "#d97706", light: "#f59e0b", dark: "#b45309" },
  success: { base: "#16a34a", light: "#22c55e", dark: "#15803d" },
  info: { base: "#0891b2", light: "#06b6d4", dark: "#0e7490" },
} as const;

export type Palette = typeof palette;

// ---------------------------------------------------------------------------
// Theme tokens – colour tokens that change between light and dark modes
// ---------------------------------------------------------------------------
export interface ThemeTokens {
  bg: string;
  surface: string;
  surfaceHover: string;
  surfaceAlt: string;
  border: string;
  borderSubtle: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  primary: string;
  primaryHover: string;
  success: string;
  warning: string;
  danger: string;
  dangerHover: string;
  info: string;
  accent: string;
  shadow: string;
  shadowLg: string;
  radius: string;
  radiusLg: string;
  fontMono: string;
  tagBg: string;
  tagText: string;
  inputBg: string;
  inputBorder: string;
  tableBorder: string;
  highlight: string;
}

export const lightTheme: ThemeTokens = {
  bg: "#f5f5f5",
  surface: "#ffffff",
  surfaceHover: "#f9fafb",
  surfaceAlt: "#f1f5f9",
  border: "#e5e7eb",
  borderSubtle: "#f3f4f6",
  text: "#111827",
  textSecondary: "#6b7280",
  textMuted: "#94a3b8",
  primary: palette.primary.base,
  primaryHover: palette.primary.dark,
  success: palette.success.base,
  warning: palette.warning.base,
  danger: palette.error.base,
  dangerHover: palette.error.dark,
  info: palette.info.base,
  accent: "#a78bfa",
  shadow: shadows.md,
  shadowLg: shadows.lg,
  radius: radii.lg,
  radiusLg: radii.xl,
  fontMono: "'Fira Code', 'Cascadia Code', monospace",
  tagBg: "#e0e7ff",
  tagText: "#3730a3",
  inputBg: "#ffffff",
  inputBorder: "#d1d5db",
  tableBorder: "#e5e7eb",
  highlight: "#f472b6",
};

export const darkTheme: ThemeTokens = {
  bg: "#111827",
  surface: "#1f2937",
  surfaceHover: "#374151",
  surfaceAlt: "#0f172a",
  border: "#374151",
  borderSubtle: "#1e293b",
  text: "#f9fafb",
  textSecondary: "#9ca3af",
  textMuted: "#64748b",
  primary: palette.primary.light,
  primaryHover: palette.primary.base,
  success: palette.success.light,
  warning: palette.warning.light,
  danger: palette.error.light,
  dangerHover: palette.error.base,
  info: palette.info.light,
  accent: "#a78bfa",
  shadow: shadows.dark.md,
  shadowLg: shadows.dark.lg,
  radius: radii.lg,
  radiusLg: radii.xl,
  fontMono: "'Fira Code', 'Cascadia Code', monospace",
  tagBg: "#334155",
  tagText: "#94a3b8",
  inputBg: "#1e293b",
  inputBorder: "#334155",
  tableBorder: "#334155",
  highlight: "#f472b6",
};

export type ThemeMode = "light" | "dark";

export function getTheme(mode: ThemeMode): ThemeTokens {
  return mode === "dark" ? darkTheme : lightTheme;
}

// ---------------------------------------------------------------------------
// Status colours – shared across all themes
// ---------------------------------------------------------------------------
export const statusColor: Record<string, string> = {
  completed: palette.success.base,
  running: palette.primary.base,
  pending: palette.warning.base,
  failed: palette.error.base,
  cancelled: palette.secondary.base,
  skipped: palette.secondary.light,
};

export function getStatusColor(status: string): string {
  return statusColor[status.toLowerCase()] ?? palette.secondary.base;
}

// ---------------------------------------------------------------------------
// Priority colours
// ---------------------------------------------------------------------------
export const priorityColor: Record<string, string> = {
  low: palette.secondary.base,
  medium: palette.primary.light,
  high: palette.warning.light,
  critical: palette.error.light,
};

export function getPriorityColor(priority: string): string {
  return priorityColor[priority.toLowerCase()] ?? palette.secondary.base;
}

// ---------------------------------------------------------------------------
// Shared style helpers
// ---------------------------------------------------------------------------
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const sec = ms / 1000;
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const min = sec / 60;
  return `${min.toFixed(1)}m`;
}
