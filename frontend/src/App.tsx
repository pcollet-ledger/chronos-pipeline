import { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import WorkflowList from "./components/WorkflowList";
import WorkflowDetail from "./components/WorkflowDetail";
import ErrorBanner from "./components/ErrorBanner";
import { useTheme } from "./contexts/ThemeContext";
import type { AnalyticsSummary, Workflow } from "./types";
import { getAnalyticsSummary, listWorkflows } from "./services/api";

type View = "dashboard" | "workflows" | "workflow-detail";

export default function App() {
  const { mode, theme, toggleTheme } = useTheme();
  const [view, setView] = useState<View>("dashboard");
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
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

  const openWorkflow = (id: string) => {
    setSelectedWorkflowId(id);
    setView("workflow-detail");
  };

  const goBack = () => {
    setSelectedWorkflowId(null);
    setView("workflows");
    void refresh();
  };

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: theme.bg, color: theme.text }}>
      <header
        style={{
          padding: "16px 32px",
          borderBottom: `1px solid ${theme.border}`,
          display: "flex",
          alignItems: "center",
          gap: "24px",
        }}
      >
        <h1 style={{ fontSize: "20px", fontWeight: 700, color: theme.primary }}>
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
                background: view === v || (v === "workflows" && view === "workflow-detail")
                  ? theme.primary
                  : "transparent",
                color: view === v || (v === "workflows" && view === "workflow-detail")
                  ? "#fff"
                  : theme.textSecondary,
                fontWeight: view === v ? 600 : 400,
                fontSize: "14px",
                textTransform: "capitalize",
              }}
            >
              {v}
            </button>
          ))}
        </nav>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <button
            onClick={toggleTheme}
            data-testid="theme-toggle"
            style={{
              padding: "6px 16px",
              borderRadius: "6px",
              border: `1px solid ${theme.border}`,
              background: "transparent",
              color: theme.textSecondary,
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
              border: `1px solid ${theme.border}`,
              background: "transparent",
              color: theme.textSecondary,
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

        {view === "dashboard" && (
          <Dashboard analytics={analytics} loading={loading} />
        )}
        {view === "workflows" && (
          <WorkflowList
            workflows={workflows}
            onRefresh={() => void refresh()}
            loading={loading}
            onSelectWorkflow={openWorkflow}
          />
        )}
        {view === "workflow-detail" && selectedWorkflowId && (
          <WorkflowDetail workflowId={selectedWorkflowId} onBack={goBack} />
        )}
      </main>
    </div>
  );
}
