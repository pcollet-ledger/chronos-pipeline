import { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import WorkflowList from "./components/WorkflowList";
import WorkflowDetail from "./components/WorkflowDetail";
import ExecutionLogViewer from "./components/ExecutionLogViewer";
import ErrorBanner from "./components/ErrorBanner";
import ThemeToggle from "./components/ThemeToggle";
import { ThemeProvider, useTheme } from "./context/ThemeContext";
import type { AnalyticsSummary, Workflow } from "./types";
import { getAnalyticsSummary, listWorkflows } from "./services/api";

type View =
  | { kind: "dashboard" }
  | { kind: "workflows" }
  | { kind: "workflow-detail"; workflowId: string }
  | { kind: "execution-log"; executionId: string };

function AppContent() {
  const { theme } = useTheme();
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

  const p = theme.palette;

  const navItems: Array<{ kind: View["kind"]; label: string }> = [
    { kind: "dashboard", label: "dashboard" },
    { kind: "workflows", label: "workflows" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: p.background }}>
      <header
        style={{
          padding: `${theme.spacing.md} ${theme.spacing.xl}`,
          borderBottom: `1px solid ${p.border}`,
          display: "flex",
          alignItems: "center",
          gap: theme.spacing.lg,
        }}
      >
        <h1 style={{ fontSize: theme.fontSize.xxl, fontWeight: theme.fontWeight.bold, color: theme.colors.info }}>
          Chronos Pipeline
        </h1>
        <nav style={{ display: "flex", gap: theme.spacing.sm }}>
          {navItems.map((item) => (
            <button
              key={item.kind}
              onClick={() => setView({ kind: item.kind } as View)}
              style={{
                padding: `6px ${theme.spacing.md}`,
                borderRadius: theme.borderRadius.md,
                border: "none",
                cursor: "pointer",
                background: view.kind === item.kind ? theme.colors.primaryDark : "transparent",
                color: view.kind === item.kind ? "#fff" : p.textSecondary,
                fontWeight: view.kind === item.kind ? theme.fontWeight.semibold : theme.fontWeight.normal,
                fontSize: theme.fontSize.base,
                textTransform: "capitalize",
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div style={{ marginLeft: "auto", display: "flex", gap: theme.spacing.sm, alignItems: "center" }}>
          <ThemeToggle />
          <button
            onClick={() => void refresh()}
            style={{
              padding: `6px ${theme.spacing.md}`,
              borderRadius: theme.borderRadius.md,
              border: `1px solid ${p.border}`,
              background: "transparent",
              color: p.textSecondary,
              cursor: "pointer",
              fontSize: theme.fontSize.md,
            }}
          >
            Refresh
          </button>
        </div>
      </header>

      <main
        style={{
          padding: `${theme.spacing.lg} ${theme.spacing.xl}`,
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
            onSelectWorkflow={(id) => setView({ kind: "workflow-detail", workflowId: id })}
          />
        )}
        {view.kind === "workflow-detail" && (
          <WorkflowDetail
            workflowId={view.workflowId}
            onBack={() => setView({ kind: "workflows" })}
            onRefresh={() => void refresh()}
          />
        )}
        {view.kind === "execution-log" && (
          <ExecutionLogViewer
            executionId={view.executionId}
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
