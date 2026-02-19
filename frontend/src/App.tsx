import { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import WorkflowList from "./components/WorkflowList";
import ErrorBanner from "./components/ErrorBanner";
import type { AnalyticsSummary, Workflow } from "./types";
import { getAnalyticsSummary, listWorkflows } from "./services/api";

type View = "dashboard" | "workflows";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
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
          {(["dashboard", "workflows"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              style={{
                padding: "6px 16px",
                borderRadius: "6px",
                border: "none",
                cursor: "pointer",
                background: view === v ? "#1e40af" : "transparent",
                color: view === v ? "#fff" : "#94a3b8",
                fontWeight: view === v ? 600 : 400,
                fontSize: "14px",
                textTransform: "capitalize",
              }}
            >
              {v}
            </button>
          ))}
        </nav>
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
          />
        )}
      </main>
    </div>
  );
}
