import { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import WorkflowList from "./components/WorkflowList";
import WorkflowDetail from "./components/WorkflowDetail";
import ErrorBanner from "./components/ErrorBanner";
import { ThemeProvider, useTheme } from "./context/ThemeContext";
import type { AnalyticsSummary, Workflow } from "./types";
import { getAnalyticsSummary, listWorkflows } from "./services/api";

type View =
  | { kind: "dashboard" }
  | { kind: "workflows" }
  | { kind: "workflow-detail"; id: string };

function AppContent() {
  const { mode, palette, toggle } = useTheme();
  const [view, setView] = useState<View>({ kind: "dashboard" });
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    try {
      setError(null);
      setLoading(true);
      const [wfs, stats] = await Promise.all([
        listWorkflows(),
        getAnalyticsSummary(),
      ]);
      setWorkflows(wfs);
      setAnalytics(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const navItems = [
    { kind: "dashboard" as const, label: "Dashboard" },
    { kind: "workflows" as const, label: "Workflows" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: palette.background, color: palette.text }}>
      <header
        style={{
          padding: "16px 32px",
          borderBottom: `1px solid ${palette.border}`,
          display: "flex",
          alignItems: "center",
          gap: "24px",
        }}
      >
        <h1 style={{ fontSize: "20px", fontWeight: 700, color: palette.info }}>
          Chronos Pipeline
        </h1>
        <nav style={{ display: "flex", gap: "12px" }}>
          {navItems.map((item) => (
            <button
              key={item.kind}
              onClick={() => setView({ kind: item.kind })}
              style={{
                padding: "6px 16px",
                borderRadius: "6px",
                border: "none",
                cursor: "pointer",
                background:
                  view.kind === item.kind ? palette.primaryDark : "transparent",
                color:
                  view.kind === item.kind ? "#fff" : palette.textSecondary,
                fontWeight: view.kind === item.kind ? 600 : 400,
                fontSize: "14px",
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
          <button
            onClick={toggle}
            data-testid="theme-toggle"
            title={`Switch to ${mode === "dark" ? "light" : "dark"} mode`}
            style={{
              padding: "6px 14px",
              borderRadius: "6px",
              border: `1px solid ${palette.border}`,
              background: "transparent",
              color: palette.textSecondary,
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            {mode === "dark" ? "Light" : "Dark"}
          </button>
          <button
            onClick={() => void refresh()}
            style={{
              padding: "6px 16px",
              borderRadius: "6px",
              border: `1px solid ${palette.border}`,
              background: "transparent",
              color: palette.textSecondary,
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
            onDismiss={() => setError(null)}
            onRetry={() => void refresh()}
          />
        )}

        {view.kind === "dashboard" && (
          <Dashboard analytics={analytics} loading={loading} />
        )}
        {view.kind === "workflows" && (
          <WorkflowList
            workflows={workflows}
            onRefresh={() => void refresh()}
            loading={loading}
            onSelectWorkflow={(id: string) =>
              setView({ kind: "workflow-detail", id })
            }
          />
        )}
        {view.kind === "workflow-detail" && (
          <WorkflowDetail
            workflowId={view.id}
            onBack={() => setView({ kind: "workflows" })}
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
