import type { AnalyticsSummary } from "../types";
import { useTheme } from "../contexts/ThemeContext";
import {
  spacing,
  fontSize,
  fontWeight,
  radii,
  getStatusColor,
  formatDuration,
} from "../theme";
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
  textMuted,
}: {
  label: string;
  value: string | number;
  color: string;
  surface: string;
  textMuted: string;
}) {
  return (
    <div
      style={{
        background: surface,
        borderRadius: radii.xl,
        padding: spacing.xl,
        minWidth: "200px",
        flex: 1,
      }}
    >
      <div style={{ fontSize: fontSize.md, color: textMuted, marginBottom: spacing.sm }}>
        {label}
      </div>
      <div style={{ fontSize: fontSize.h2, fontWeight: fontWeight.bold, color }}>{value}</div>
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

  return (
    <div>
      <h2
        style={{ fontSize: fontSize.xxl, marginBottom: spacing.xl, color: theme.text }}
      >
        Dashboard
      </h2>

      <div
        style={{
          display: "flex",
          gap: spacing.lg,
          flexWrap: "wrap",
          marginBottom: spacing.xxl,
        }}
      >
        <StatCard
          label="Pipelines"
          value={analytics.total_workflows}
          color={theme.info}
          surface={theme.surface}
          textMuted={theme.textMuted}
        />
        <StatCard
          label="Executions"
          value={analytics.total_executions}
          color={theme.accent}
          surface={theme.surface}
          textMuted={theme.textMuted}
        />
        <StatCard
          label="Success Rate"
          value={`${analytics.success_rate}%`}
          color={analytics.success_rate >= 90 ? theme.success : theme.warning}
          surface={theme.surface}
          textMuted={theme.textMuted}
        />
        <StatCard
          label="Avg Duration"
          value={formatDuration(analytics.avg_duration_ms)}
          color={theme.highlight}
          surface={theme.surface}
          textMuted={theme.textMuted}
        />
      </div>

      <div
        style={{
          background: theme.surface,
          borderRadius: radii.xl,
          padding: spacing.xl,
          marginBottom: spacing.xl,
        }}
      >
        <h3
          style={{
            fontSize: fontSize.lg,
            color: theme.textMuted,
            marginBottom: spacing.lg,
          }}
        >
          Executions by Status
        </h3>
        <div style={{ display: "flex", gap: spacing.xl, flexWrap: "wrap" }}>
          {Object.entries(analytics.executions_by_status).map(
            ([status, count]) => (
              <div
                key={status}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: spacing.sm,
                }}
              >
                <div
                  style={{
                    width: "10px",
                    height: "10px",
                    borderRadius: radii.full,
                    background: getStatusColor(status),
                  }}
                />
                <span
                  style={{
                    fontSize: fontSize.lg,
                    color: theme.textSecondary,
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
          borderRadius: radii.xl,
          padding: spacing.xl,
        }}
      >
        <h3
          style={{
            fontSize: fontSize.lg,
            color: theme.textMuted,
            marginBottom: spacing.lg,
          }}
        >
          Recent Executions
        </h3>
        {analytics.recent_executions.length === 0 ? (
          <div style={{ color: theme.textMuted, fontSize: fontSize.lg }}>
            No executions yet
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${theme.tableBorder}` }}>
                <th style={thStyle(theme.textMuted)}>ID</th>
                <th style={thStyle(theme.textMuted)}>Status</th>
                <th style={thStyle(theme.textMuted)}>Trigger</th>
                <th style={thStyle(theme.textMuted)}>Started</th>
              </tr>
            </thead>
            <tbody>
              {analytics.recent_executions.map((ex) => (
                <tr
                  key={ex.id}
                  style={{ borderBottom: `1px solid ${theme.borderSubtle}` }}
                >
                  <td style={tdStyle(theme.textSecondary)}>{ex.id.slice(0, 8)}...</td>
                  <td style={tdStyle(theme.textSecondary)}>
                    <span
                      style={{
                        color: getStatusColor(ex.status),
                        fontWeight: fontWeight.semibold,
                        textTransform: "capitalize",
                      }}
                    >
                      {ex.status}
                    </span>
                  </td>
                  <td style={tdStyle(theme.textSecondary)}>{ex.trigger}</td>
                  <td style={tdStyle(theme.textSecondary)}>
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

function thStyle(color: string): React.CSSProperties {
  return {
    textAlign: "left",
    padding: `${spacing.sm} ${spacing.md}`,
    fontSize: fontSize.sm,
    color,
    fontWeight: fontWeight.semibold,
    textTransform: "uppercase",
  };
}

function tdStyle(color: string): React.CSSProperties {
  return {
    padding: `10px ${spacing.md}`,
    fontSize: fontSize.lg,
    color,
  };
}
