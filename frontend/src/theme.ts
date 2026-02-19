/**
 * Shared theme tokens for dark and light modes.
 * All components should reference these tokens instead of hard-coding colors.
 */

export interface ThemeTokens {
  bg: string;
  bgCard: string;
  bgInput: string;
  border: string;
  borderSubtle: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  accent: string;
  accentHover: string;
  success: string;
  error: string;
  warning: string;
  info: string;
  statusCompleted: string;
  statusFailed: string;
  statusRunning: string;
  statusPending: string;
  statusCancelled: string;
}

export const darkTheme: ThemeTokens = {
  bg: "#0f172a",
  bgCard: "#1e293b",
  bgInput: "#1e293b",
  border: "#1e293b",
  borderSubtle: "#334155",
  textPrimary: "#e2e8f0",
  textSecondary: "#94a3b8",
  textMuted: "#64748b",
  accent: "#38bdf8",
  accentHover: "#1e40af",
  success: "#22c55e",
  error: "#ef4444",
  warning: "#eab308",
  info: "#3b82f6",
  statusCompleted: "#22c55e",
  statusFailed: "#ef4444",
  statusRunning: "#eab308",
  statusPending: "#64748b",
  statusCancelled: "#6b7280",
};

export const lightTheme: ThemeTokens = {
  bg: "#f8fafc",
  bgCard: "#ffffff",
  bgInput: "#ffffff",
  border: "#e2e8f0",
  borderSubtle: "#cbd5e1",
  textPrimary: "#0f172a",
  textSecondary: "#475569",
  textMuted: "#94a3b8",
  accent: "#0284c7",
  accentHover: "#1d4ed8",
  success: "#16a34a",
  error: "#dc2626",
  warning: "#ca8a04",
  info: "#2563eb",
  statusCompleted: "#16a34a",
  statusFailed: "#dc2626",
  statusRunning: "#ca8a04",
  statusPending: "#94a3b8",
  statusCancelled: "#6b7280",
};

export function statusColor(theme: ThemeTokens, status: string): string {
  const map: Record<string, string> = {
    completed: theme.statusCompleted,
    failed: theme.statusFailed,
    running: theme.statusRunning,
    pending: theme.statusPending,
    cancelled: theme.statusCancelled,
  };
  return map[status] ?? theme.textMuted;
}
