export interface ThemeTokens {
  bg: string;
  surface: string;
  surfaceHover: string;
  border: string;
  text: string;
  textSecondary: string;
  primary: string;
  primaryHover: string;
  success: string;
  warning: string;
  danger: string;
  dangerHover: string;
  info: string;
  shadow: string;
  radius: string;
  radiusLg: string;
  fontMono: string;
}

export const lightTheme: ThemeTokens = {
  bg: "#f5f5f5",
  surface: "#ffffff",
  surfaceHover: "#f9fafb",
  border: "#e5e7eb",
  text: "#111827",
  textSecondary: "#6b7280",
  primary: "#2563eb",
  primaryHover: "#1d4ed8",
  success: "#16a34a",
  warning: "#d97706",
  danger: "#dc2626",
  dangerHover: "#b91c1c",
  info: "#0891b2",
  shadow: "0 1px 3px rgba(0,0,0,0.1)",
  radius: "8px",
  radiusLg: "12px",
  fontMono: "'Fira Code', 'Cascadia Code', monospace",
};

export const darkTheme: ThemeTokens = {
  bg: "#111827",
  surface: "#1f2937",
  surfaceHover: "#374151",
  border: "#374151",
  text: "#f9fafb",
  textSecondary: "#9ca3af",
  primary: "#3b82f6",
  primaryHover: "#2563eb",
  success: "#22c55e",
  warning: "#f59e0b",
  danger: "#ef4444",
  dangerHover: "#dc2626",
  info: "#06b6d4",
  shadow: "0 1px 3px rgba(0,0,0,0.4)",
  radius: "8px",
  radiusLg: "12px",
  fontMono: "'Fira Code', 'Cascadia Code', monospace",
};

export type ThemeMode = "light" | "dark";

export function getTheme(mode: ThemeMode): ThemeTokens {
  return mode === "dark" ? darkTheme : lightTheme;
}

export const statusColor: Record<string, string> = {
  completed: "#16a34a",
  running: "#2563eb",
  pending: "#d97706",
  failed: "#dc2626",
  cancelled: "#6b7280",
  skipped: "#9ca3af",
};

export function getStatusColor(status: string): string {
  return statusColor[status.toLowerCase()] ?? "#6b7280";
}
