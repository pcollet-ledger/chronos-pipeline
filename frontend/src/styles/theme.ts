/**
 * Shared theme tokens for Chronos Pipeline UI.
 *
 * Provides colour palette, spacing, typography, shadows, and transitions
 * used across all components.
 */

export const colors = {
  primary: "#2563eb",
  primaryLight: "#3b82f6",
  primaryDark: "#1e40af",
  secondary: "#a78bfa",
  secondaryLight: "#c4b5fd",
  secondaryDark: "#7c3aed",
  error: "#ef4444",
  errorLight: "#fca5a5",
  errorDark: "#7f1d1d",
  warning: "#eab308",
  warningLight: "#fde68a",
  warningDark: "#854d0e",
  success: "#22c55e",
  successLight: "#86efac",
  successDark: "#064e3b",
  info: "#38bdf8",
  infoLight: "#7dd3fc",
  infoDark: "#0369a1",
  background: "#0f172a",
  surface: "#1e293b",
  surfaceHover: "#334155",
  textPrimary: "#e2e8f0",
  textSecondary: "#94a3b8",
  textMuted: "#64748b",
  textDisabled: "#475569",
  border: "#334155",
  borderLight: "#1e293b",
} as const;

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "24px",
  xxl: "32px",
} as const;

export const borderRadius = {
  sm: "4px",
  md: "6px",
  lg: "8px",
  xl: "12px",
  full: "50%",
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

export const shadows = {
  sm: "0 1px 2px rgba(0,0,0,0.1)",
  md: "0 4px 6px rgba(0,0,0,0.15)",
  lg: "0 4px 20px rgba(0,0,0,0.3)",
} as const;

export const transitions = {
  fast: "150ms ease",
  normal: "200ms ease",
  slow: "300ms ease",
} as const;

export const statusColors: Record<string, string> = {
  completed: colors.success,
  failed: colors.error,
  running: colors.warning,
  pending: colors.textMuted,
  cancelled: "#6b7280",
};

export const priorityColors: Record<string, string> = {
  low: colors.textMuted,
  medium: colors.primaryLight,
  high: colors.warning,
  critical: colors.error,
};

export const theme = {
  colors,
  spacing,
  borderRadius,
  fontSize,
  fontWeight,
  shadows,
  transitions,
  statusColors,
  priorityColors,
} as const;

export type Theme = typeof theme;
export default theme;
