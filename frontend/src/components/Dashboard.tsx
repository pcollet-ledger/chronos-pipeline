import type { AnalyticsSummary } from "../types";
import {
  colors,
  fontSizes,
  fontWeights,
  radii,
  spacing,
  statusColors,
} from "../styles/theme";

interface Props {
  analytics: AnalyticsSummary | null;
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div
      style={{
        background: colors.neutral[800],
        borderRadius: radii.xl,
        padding: spacing.xl,
        minWidth: "200px",
        flex: 1,
      }}
    >
      <div
        style={{
          fontSize: fontSizes.md,
          color: colors.neutral[500],
          marginBottom: spacing.sm,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: fontSizes.xxxl, fontWeight: fontWeights.bold, color }}>
        {value}
      </div>
    </div>
  );
}

export default function Dashboard({ analytics }: Props) {
  if (!analytics) {
    return (
      <div
        style={{
          color: colors.neutral[500],
          padding: spacing.xxxxl,
          textAlign: "center",
        }}
      >
        Loading analytics...
      </div>
    );
  }

  return (
    <div>
      <h2
        style={{
          fontSize: fontSizes.xl,
          marginBottom: spacing.xl,
          color: colors.neutral[200],
        }}
      >
        Dashboard
      </h2>

      {/* Stat cards */}
      <div
        style={{
          display: "flex",
          gap: spacing.lg,
          flexWrap: "wrap",
          marginBottom: spacing.xxxl,
        }}
      >
        <StatCard
          label="Pipelines"
          value={analytics.total_workflows}
          color={colors.info.main}
        />
        <StatCard
          label="Executions"
          value={analytics.total_executions}
          color={colors.secondary.main}
        />
        <StatCard
          label="Success Rate"
          value={`${analytics.success_rate}%`}
          color={analytics.success_rate >= 90 ? colors.success.main : colors.warning.main}
        />
        <StatCard
          label="Avg Duration"
          value={formatDuration(analytics.avg_duration_ms)}
          color={colors.pink}
        />
      </div>

      {/* Status breakdown */}
      <div
        style={{
          background: colors.neutral[800],
          borderRadius: radii.xl,
          padding: spacing.xl,
          marginBottom: spacing.xxl,
        }}
      >
        <h3
          style={{
            fontSize: fontSizes.base,
            color: colors.neutral[400],
            marginBottom: spacing.lg,
          }}
        >
          Executions by Status
        </h3>
        <div style={{ display: "flex", gap: spacing.xxl, flexWrap: "wrap" }}>
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
                    background: statusColors[status] || colors.neutral[500],
                  }}
                />
                <span
                  style={{
                    fontSize: fontSizes.base,
                    color: colors.neutral[300],
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

      {/* Recent executions */}
      <div
        style={{
          background: colors.neutral[800],
          borderRadius: radii.xl,
          padding: spacing.xl,
        }}
      >
        <h3
          style={{
            fontSize: fontSizes.base,
            color: colors.neutral[400],
            marginBottom: spacing.lg,
          }}
        >
          Recent Executions
        </h3>
        {analytics.recent_executions.length === 0 ? (
          <div style={{ color: colors.neutral[600], fontSize: fontSizes.base }}>
            No executions yet
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${colors.neutral[700]}` }}>
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
                  style={{ borderBottom: `1px solid ${colors.neutral[800]}` }}
                >
                  <td style={tdStyle}>{ex.id.slice(0, 8)}...</td>
                  <td style={tdStyle}>
                    <span
                      style={{
                        color: statusColors[ex.status] || colors.neutral[500],
                        fontWeight: fontWeights.semibold,
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
                      : "\u2014"}
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

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: `${spacing.sm} ${spacing.md}`,
  fontSize: fontSizes.sm,
  color: colors.neutral[500],
  fontWeight: fontWeights.semibold,
  textTransform: "uppercase",
};

const tdStyle: React.CSSProperties = {
  padding: `10px ${spacing.md}`,
  fontSize: fontSizes.base,
  color: colors.neutral[300],
};

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const sec = ms / 1000;
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const min = sec / 60;
  return `${min.toFixed(1)}m`;
}
