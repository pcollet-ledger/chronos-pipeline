import { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import WorkflowList from "./components/WorkflowList";
import WorkflowDetail from "./components/WorkflowDetail";
import ExecutionComparisonView from "./components/ExecutionComparisonView";
import ErrorBanner from "./components/ErrorBanner";
import type { AnalyticsSummary, Workflow } from "./types";
import { getAnalyticsSummary, listWorkflows } from "./services/api";

type View = "dashboard" | "workflows" | "workflow-detail" | "compare";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const refresh = async () => {
    try {
      setError(null);
      setLoading(true);
      const [wfs, stats] = await Promise.all([
        listWorkflows(searchQuery ? { search: searchQuery } : undefined),
        getAnalyticsSummary(),
      ]);
      setWorkflows(wfs);
      setAnalytics(stats);
      if (selectedWorkflow) {
        const updated = wfs.find((w) => w.id === selectedWorkflow.id);
        if (updated) setSelectedWorkflow(updated);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  const handleSelectWorkflow = (wf: Workflow) => {
    setSelectedWorkflow(wf);
    setView("workflow-detail");
  };

  const navItems: Array<{ key: View; label: string }> = [
    { key: "dashboard", label: "dashboard" },
    { key: "workflows", label: "workflows" },
    { key: "compare", label: "compare" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#0f172a" }}>
      <header
        style={{
          padding: "16px 32px",
          borderBottom: "1px solid #1e293b",
          display: "flex",
          alignItems: "center",
          gap: "24px",
        }}
      >
        <h1 style={{ fontSize: "20px", fontWeight: 700, color: "#38bdf8" }}>
          Chronos Pipeline
        </h1>
        <nav style={{ display: "flex", gap: "12px" }}>
          {navItems.map((item) => (
            <button
              key={item.key}
              onClick={() => setView(item.key)}
              style={{
                padding: "6px 16px",
                borderRadius: "6px",
                border: "none",
                cursor: "pointer",
                background: view === item.key ? "#1e40af" : "transparent",
                color: view === item.key ? "#fff" : "#94a3b8",
                fontWeight: view === item.key ? 600 : 400,
                fontSize: "14px",
                textTransform: "capitalize",
              }}
            >
              {item.label}
            </button>
          ))}
        </nav>

        {view === "workflows" && (
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search workflows..."
            data-testid="search-input"
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              border: "1px solid #334155",
              background: "#1e293b",
              color: "#e2e8f0",
              fontSize: "13px",
              outline: "none",
              width: "200px",
            }}
          />
        )}

        <button
          onClick={() => void refresh()}
          style={{
            marginLeft: "auto",
            padding: "6px 16px",
            borderRadius: "6px",
            border: "1px solid #334155",
            background: "transparent",
            color: "#94a3b8",
            cursor: "pointer",
            fontSize: "13px",
          }}
        >
          Refresh
        </button>
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
            onSelect={handleSelectWorkflow}
          />
        )}
        {view === "workflow-detail" && selectedWorkflow && (
          <WorkflowDetail
            workflow={selectedWorkflow}
            onBack={() => setView("workflows")}
            onRefresh={() => void refresh()}
          />
        )}
        {view === "compare" && (
          <ExecutionComparisonView onBack={() => setView("dashboard")} />
        )}
      </main>
    </div>
  );
}
