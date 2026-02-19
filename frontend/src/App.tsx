import { useEffect, useState } from "react";
import Dashboard from "./components/Dashboard";
import WorkflowList from "./components/WorkflowList";
import type { AnalyticsSummary, Workflow } from "./types";
import { getAnalyticsSummary, listWorkflows } from "./services/api";
import {
  colors,
  fontSizes,
  fontWeights,
  radii,
  spacing,
} from "./styles/theme";

type View = "dashboard" | "workflows";

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setError(null);
      const [wfs, stats] = await Promise.all([
        listWorkflows(),
        getAnalyticsSummary(),
      ]);
      setWorkflows(wfs);
      setAnalytics(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: colors.neutral[900] }}>
      {/* Header */}
      <header
        style={{
          padding: `${spacing.lg} ${spacing.xxxl}`,
          borderBottom: `1px solid ${colors.neutral[800]}`,
          display: "flex",
          alignItems: "center",
          gap: spacing.xxl,
        }}
      >
        <h1
          style={{
            fontSize: fontSizes.xxl,
            fontWeight: fontWeights.bold,
            color: colors.info.main,
          }}
        >
          Chronos Pipeline
        </h1>
        <nav style={{ display: "flex", gap: spacing.md }}>
          {(["dashboard", "workflows"] as View[]).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              style={{
                padding: `6px ${spacing.lg}`,
                borderRadius: radii.md,
                border: "none",
                cursor: "pointer",
                background: view === v ? colors.primary.dark : "transparent",
                color: view === v ? "#fff" : colors.neutral[400],
                fontWeight: view === v ? fontWeights.semibold : fontWeights.normal,
                fontSize: fontSizes.base,
                textTransform: "capitalize",
              }}
            >
              {v}
            </button>
          ))}
        </nav>
        <button
          onClick={refresh}
          style={{
            marginLeft: "auto",
            padding: `6px ${spacing.lg}`,
            borderRadius: radii.md,
            border: `1px solid ${colors.neutral[700]}`,
            background: "transparent",
            color: colors.neutral[400],
            cursor: "pointer",
            fontSize: fontSizes.md,
          }}
        >
          Refresh
        </button>
      </header>

      {/* Content */}
      <main
        style={{
          padding: `${spacing.xxl} ${spacing.xxxl}`,
          maxWidth: "1200px",
          margin: "0 auto",
        }}
      >
        {error && (
          <div
            style={{
              padding: `${spacing.md} ${spacing.lg}`,
              background: colors.error.bg,
              borderRadius: radii.lg,
              marginBottom: spacing.lg,
              color: colors.error.light,
              fontSize: fontSizes.base,
            }}
          >
            {error}
          </div>
        )}

        {view === "dashboard" && <Dashboard analytics={analytics} />}
        {view === "workflows" && (
          <WorkflowList workflows={workflows} onRefresh={refresh} />
        )}
      </main>
    </div>
  );
}
