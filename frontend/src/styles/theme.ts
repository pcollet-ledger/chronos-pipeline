export const colors = {
  primary: "#2563eb",
  primaryLight: "#3b82f6",
  primaryDark: "#1e40af",
  secondary: "#a78bfa",
  secondaryLight: "#c4b5fd",
  secondaryDark: "#7c3aed",
  error: "#ef4444",
  errorLight: "#fca5a5",
  errorDark: "#dc2626",
  warning: "#eab308",
  warningLight: "#fde047",
  warningDark: "#ca8a04",
  success: "#22c55e",
  successLight: "#86efac",
  successDark: "#16a34a",
  info: "#38bdf8",
  infoLight: "#7dd3fc",
  infoDark: "#0284c7",
} as const;

export const darkPalette = {
  background: "#0f172a",
  surface: "#1e293b",
  surfaceHover: "#334155",
  text: "#e2e8f0",
  textSecondary: "#94a3b8",
  textMuted: "#64748b",
  border: "#334155",
  borderLight: "#1e293b",
} as const;

export const lightPalette = {
  background: "#f8fafc",
  surface: "#ffffff",
  surfaceHover: "#f1f5f9",
  text: "#0f172a",
  textSecondary: "#475569",
  textMuted: "#94a3b8",
  border: "#e2e8f0",
  borderLight: "#f1f5f9",
} as const;

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

export const shadows = {
  sm: "0 1px 2px rgba(0,0,0,0.05)",
  md: "0 4px 6px rgba(0,0,0,0.1)",
  lg: "0 4px 20px rgba(0,0,0,0.3)",
} as const;

export const transitions = {
  fast: "150ms ease",
  normal: "200ms ease",
  slow: "300ms ease",
} as const;

export interface ThemePalette {
  readonly background: string;
  readonly surface: string;
  readonly surfaceHover: string;
  readonly text: string;
  readonly textSecondary: string;
  readonly textMuted: string;
  readonly border: string;
  readonly borderLight: string;
}

export interface Theme {
  palette: ThemePalette;
  colors: typeof colors;
  spacing: typeof spacing;
  borderRadius: typeof borderRadius;
  fontSize: typeof fontSize;
  fontWeight: typeof fontWeight;
  shadows: typeof shadows;
  transitions: typeof transitions;
}

export const darkTheme: Theme = {
  palette: darkPalette,
  colors,
  spacing,
  borderRadius,
  fontSize,
  fontWeight,
  shadows,
  transitions,
};

export const lightTheme: Theme = {
  palette: lightPalette,
  colors,
  spacing,
  borderRadius,
  fontSize,
  fontWeight,
  shadows,
  transitions,
};
