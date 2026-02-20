import type { AnalyticsSummary } from "../types";
import { useTheme } from "../contexts/ThemeContext";
import { statusColor } from "../theme";
import LoadingSpinner from "./LoadingSpinner";
import EmptyState from "./EmptyState";

interface Props {
  analytics: AnalyticsSummary | null;
  loading?: boolean;
}

function StatCard({
  label,
  value,
  color,
  surface,
  textSecondary,
}: {
  label: string;
  value: string | number;
  color: string;
  surface: string;
  textSecondary: string;
}) {
  return (
    <div
      style={{
        background: surface,
        borderRadius: "12px",
        padding: "20px",
        minWidth: "200px",
        flex: 1,
      }}
    >
      <div style={{ fontSize: "13px", color: textSecondary, marginBottom: "8px" }}>
        {label}
      </div>
      <div style={{ fontSize: "28px", fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

export default function Dashboard({ analytics, loading }: Props) {
  const { theme } = useTheme();

  if (loading) {
    return <LoadingSpinner label="Loading analytics..." />;
  }

  if (!analytics) {
    return <EmptyState message="No analytics data available yet." />;
  }

  const thStyle: React.CSSProperties = {
    textAlign: "left",
    padding: "8px 12px",
    fontSize: "12px",
    color: theme.textSecondary,
    fontWeight: 600,
    textTransform: "uppercase",
  };

  const tdStyle: React.CSSProperties = {
    padding: "10px 12px",
    fontSize: "14px",
    color: theme.text,
  };

  return (
    <div>
      <h2
        style={{ fontSize: "18px", marginBottom: "20px", color: theme.text }}
      >
        Dashboard
      </h2>

      <div
        style={{
          display: "flex",
          gap: "16px",
          flexWrap: "wrap",
          marginBottom: "32px",
        }}
      >
        <StatCard
          label="Pipelines"
          value={analytics.total_workflows}
          color={theme.info}
          surface={theme.surface}
          textSecondary={theme.textSecondary}
        />
        <StatCard
          label="Executions"
          value={analytics.total_executions}
          color={theme.primary}
          surface={theme.surface}
          textSecondary={theme.textSecondary}
        />
        <StatCard
          label="Success Rate"
          value={`${analytics.success_rate}%`}
          color={analytics.success_rate >= 90 ? theme.success : theme.warning}
          surface={theme.surface}
          textSecondary={theme.textSecondary}
        />
        <StatCard
          label="Avg Duration"
          value={formatDuration(analytics.avg_duration_ms)}
          color={theme.danger}
          surface={theme.surface}
          textSecondary={theme.textSecondary}
        />
      </div>

      <div
        style={{
          background: theme.surface,
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "24px",
        }}
      >
        <h3
          style={{
            fontSize: "14px",
            color: theme.textSecondary,
            marginBottom: "16px",
          }}
        >
          Executions by Status
        </h3>
        <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
          {Object.entries(analytics.executions_by_status).map(
            ([status, count]) => (
              <div
                key={status}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <div
                  style={{
                    width: "10px",
                    height: "10px",
                    borderRadius: "50%",
                    background: statusColor[status] ?? theme.textSecondary,
                  }}
                />
                <span
                  style={{
                    fontSize: "14px",
                    color: theme.text,
                    textTransform: "capitalize",
                  }}
                >
                  {status}: <strong>{count}</strong>
                </span>
              </div>
            ),
          )}
        </div>
      </div>

      <div
        style={{
          background: theme.surface,
          borderRadius: "12px",
          padding: "20px",
        }}
      >
        <h3
          style={{
            fontSize: "14px",
            color: theme.textSecondary,
            marginBottom: "16px",
          }}
        >
          Recent Executions
        </h3>
        {analytics.recent_executions.length === 0 ? (
          <div style={{ color: theme.textSecondary, fontSize: "14px" }}>
            No executions yet
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${theme.border}` }}>
                <th style={thStyle}>ID</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Trigger</th>
                <th style={thStyle}>Started</th>
              </tr>
            </thead>
            <tbody>
              {analytics.recent_executions.map((ex) => (
                <tr
                  key={ex.id}
                  style={{ borderBottom: `1px solid ${theme.surface}` }}
                >
                  <td style={tdStyle}>{ex.id.slice(0, 8)}...</td>
                  <td style={tdStyle}>
                    <span
                      style={{
                        color: statusColor[ex.status] ?? theme.textSecondary,
                        fontWeight: 600,
                        textTransform: "capitalize",
                      }}
                    >
                      {ex.status}
                    </span>
                  </td>
                  <td style={tdStyle}>{ex.trigger}</td>
                  <td style={tdStyle}>
                    {ex.started_at
                      ? new Date(ex.started_at).toLocaleString()
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const sec = ms / 1000;
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const min = sec / 60;
  return `${min.toFixed(1)}m`;
}
