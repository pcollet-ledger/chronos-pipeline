/**
 * Shared design tokens for Chronos Pipeline UI.
 *
 * Every visual constant (colour, spacing, typography, shadow, etc.) lives here
 * so that components stay consistent and style changes propagate from a single
 * source of truth.
 */

// ---------------------------------------------------------------------------
// Colour palette
// ---------------------------------------------------------------------------

export const colors = {
  primary: {
    light: "#60a5fa",
    main: "#2563eb",
    dark: "#1e40af",
  },
  secondary: {
    light: "#c4b5fd",
    main: "#a78bfa",
    dark: "#7c3aed",
  },
  error: {
    light: "#fca5a5",
    main: "#ef4444",
    dark: "#dc2626",
    bg: "#7f1d1d",
  },
  warning: {
    light: "#fde68a",
    main: "#eab308",
    dark: "#ca8a04",
  },
  success: {
    light: "#86efac",
    main: "#22c55e",
    dark: "#059669",
  },
  info: {
    light: "#67e8f9",
    main: "#38bdf8",
    dark: "#0ea5e9",
  },
  neutral: {
    50: "#f8fafc",
    100: "#f1f5f9",
    200: "#e2e8f0",
    300: "#cbd5e1",
    400: "#94a3b8",
    500: "#64748b",
    600: "#475569",
    700: "#334155",
    800: "#1e293b",
    900: "#0f172a",
  },
  pink: "#f472b6",
  muted: "#6b7280",
} as const;

/** Semantic status colours used across dashboard and execution displays. */
export const statusColors: Record<string, string> = {
  completed: colors.success.main,
  failed: colors.error.main,
  running: colors.warning.main,
  pending: colors.neutral[500],
  cancelled: colors.muted,
};

/** Priority-level colours for task cards. */
export const priorityColors: Record<string, string> = {
  low: colors.neutral[500],
  medium: colors.primary.light,
  high: colors.warning.main,
  critical: colors.error.main,
};

// ---------------------------------------------------------------------------
// Spacing scale
// ---------------------------------------------------------------------------

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "12px",
  lg: "16px",
  xl: "20px",
  xxl: "24px",
  xxxl: "32px",
  xxxxl: "40px",
} as const;

// ---------------------------------------------------------------------------
// Border radius
// ---------------------------------------------------------------------------

export const radii = {
  sm: "4px",
  md: "6px",
  lg: "8px",
  xl: "12px",
  full: "50%",
} as const;

// ---------------------------------------------------------------------------
// Typography
// ---------------------------------------------------------------------------

export const fontSizes = {
  xs: "11px",
  sm: "12px",
  md: "13px",
  base: "14px",
  lg: "16px",
  xl: "18px",
  xxl: "20px",
  xxxl: "28px",
} as const;

export const fontWeights = {
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
} as const;

// ---------------------------------------------------------------------------
// Shadows
// ---------------------------------------------------------------------------

export const shadows = {
  sm: "0 1px 2px rgba(0,0,0,0.2)",
  md: "0 4px 6px rgba(0,0,0,0.25)",
  lg: "0 4px 20px rgba(0,0,0,0.3)",
  xl: "0 10px 40px rgba(0,0,0,0.4)",
} as const;

// ---------------------------------------------------------------------------
// Transitions
// ---------------------------------------------------------------------------

export const transitions = {
  fast: "150ms ease",
  normal: "250ms ease",
  slow: "400ms ease",
} as const;

// ---------------------------------------------------------------------------
// Composite theme object
// ---------------------------------------------------------------------------

export const theme = {
  colors,
  statusColors,
  priorityColors,
  spacing,
  radii,
  fontSizes,
  fontWeights,
  shadows,
  transitions,
} as const;

/** Inferred type of the full theme object. */
export type Theme = typeof theme;

export default theme;
