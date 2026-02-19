/** Centralised design tokens for Chronos Pipeline UI. */

export const colors = {
  bg: "#0f172a",
  surface: "#1e293b",
  surfaceHover: "#334155",
  border: "#334155",
  text: "#e2e8f0",
  textSecondary: "#94a3b8",
  textMuted: "#64748b",
  textDim: "#475569",
  primary: "#2563eb",
  primaryHover: "#1e40af",
  accent: "#38bdf8",
  success: "#22c55e",
  error: "#ef4444",
  warning: "#eab308",
  purple: "#a78bfa",
  pink: "#f472b6",
  teal: "#0891b2",
  violet: "#7c3aed",
  cancelled: "#6b7280",
} as const;

export const statusColors: Record<string, string> = {
  completed: colors.success,
  failed: colors.error,
  running: colors.warning,
  pending: colors.textMuted,
  cancelled: colors.cancelled,
};

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "20px",
  xxl: "24px",
  xxxl: "32px",
} as const;

export const radii = {
  sm: "4px",
  md: "6px",
  lg: "8px",
  xl: "12px",
} as const;

export const fontSizes = {
  xs: "11px",
  sm: "12px",
  md: "13px",
  base: "14px",
  lg: "16px",
  xl: "18px",
  xxl: "20px",
  heading: "28px",
} as const;

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const sec = ms / 1000;
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const min = sec / 60;
  if (min < 60) return `${min.toFixed(1)}m`;
  const hrs = min / 60;
  return `${hrs.toFixed(1)}h`;
}
