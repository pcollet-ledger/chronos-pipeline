import { useCallback, useState } from "react";
import Dashboard from "./components/Dashboard";
import WorkflowList from "./components/WorkflowList";
import ErrorBanner from "./components/ErrorBanner";
import ThemeToggle from "./components/ThemeToggle";
import { ThemeProvider, useTheme } from "./context/ThemeContext";
import { useWorkflows } from "./hooks/useWorkflows";
import { useAnalytics } from "./hooks/useAnalytics";

type View = "dashboard" | "workflows";

function AppContent() {
  const [view, setView] = useState<View>("dashboard");
  const { colors } = useTheme();

  const {
    data: workflows,
    loading: wfLoading,
    error: wfError,
    refetch: refetchWorkflows,
  } = useWorkflows();

  const {
    data: analytics,
    loading: analyticsLoading,
    error: analyticsError,
    refetch: refetchAnalytics,
  } = useAnalytics();

  const error = wfError || analyticsError;
  const loading = wfLoading || analyticsLoading;

  const refresh = useCallback(() => {
    refetchWorkflows();
    refetchAnalytics();
  }, [refetchWorkflows, refetchAnalytics]);

  return (
    <div style={{ minHeight: "100vh", background: colors.bg, color: colors.text }}>
      <header
        style={{
          padding: "16px 32px",
          borderBottom: `1px solid ${colors.border}`,
          display: "flex",
          alignItems: "center",
          gap: "24px",
        }}
      >
        <h1 style={{ fontSize: "20px", fontWeight: 700, color: colors.accent }}>
          Chronos Pipeline
        </h1>
        <nav style={{ display: "flex", gap: "12px" }}>
          {(["dashboard", "workflows"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              style={{
                padding: "6px 16px",
                borderRadius: "6px",
                border: "none",
                cursor: "pointer",
                background: view === v ? colors.navActiveBg : "transparent",
                color: view === v ? colors.navActive : colors.textMuted,
                fontWeight: view === v ? 600 : 400,
                fontSize: "14px",
                textTransform: "capitalize",
              }}
            >
              {v}
            </button>
          ))}
        </nav>
        <div style={{ marginLeft: "auto", display: "flex", gap: "8px", alignItems: "center" }}>
          <ThemeToggle />
          <button
            onClick={refresh}
            style={{
              padding: "6px 16px",
              borderRadius: "6px",
              border: `1px solid ${colors.border}`,
              background: "transparent",
              color: colors.textMuted,
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            Refresh
          </button>
        </div>
      </header>

      <main
        style={{
          padding: "24px 32px",
          maxWidth: "1200px",
          margin: "0 auto",
        }}
      >
        {error && (
          <ErrorBanner
            message={error}
            onDismiss={() => {}}
            onRetry={refresh}
          />
        )}

        {view === "dashboard" && (
          <Dashboard analytics={analytics} loading={loading} />
        )}
        {view === "workflows" && (
          <WorkflowList
            workflows={workflows ?? []}
            onRefresh={refresh}
            loading={loading}
          />
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}
