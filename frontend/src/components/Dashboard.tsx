import type { AnalyticsSummary } from "../types";

interface Props {
  analytics: AnalyticsSummary | null;
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: "12px",
        padding: "20px",
        minWidth: "200px",
        flex: 1,
      }}
    >
      <div style={{ fontSize: "13px", color: "#64748b", marginBottom: "8px" }}>
        {label}
      </div>
      <div style={{ fontSize: "28px", fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

export default function Dashboard({ analytics }: Props) {
  if (!analytics) {
    return (
      <div style={{ color: "#64748b", padding: "40px", textAlign: "center" }}>
        Loading analytics...
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    completed: "#22c55e",
    failed: "#ef4444",
    running: "#eab308",
    pending: "#64748b",
    cancelled: "#6b7280",
  };

  return (
    <div>
      <h2 style={{ fontSize: "18px", marginBottom: "20px", color: "#e2e8f0" }}>
        Dashboard
      </h2>

      {/* Stat cards */}
      <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", marginBottom: "32px" }}>
        <StatCard label="Pipelines" value={analytics.total_workflows} color="#38bdf8" />
        <StatCard label="Executions" value={analytics.total_executions} color="#a78bfa" />
        <StatCard
          label="Success Rate"
          value={`${analytics.success_rate}%`}
          color={analytics.success_rate >= 90 ? "#22c55e" : "#eab308"}
        />
        <StatCard
          label="Avg Duration"
          value={formatDuration(analytics.avg_duration_ms)}
          color="#f472b6"
        />
      </div>

      {/* Status breakdown */}
      <div style={{ background: "#1e293b", borderRadius: "12px", padding: "20px", marginBottom: "24px" }}>
        <h3 style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "16px" }}>
          Executions by Status
        </h3>
        <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
          {Object.entries(analytics.executions_by_status).map(([status, count]) => (
            <div key={status} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div
                style={{
                  width: "10px",
                  height: "10px",
                  borderRadius: "50%",
                  background: statusColors[status] || "#64748b",
                }}
              />
              <span style={{ fontSize: "14px", color: "#cbd5e1", textTransform: "capitalize" }}>
                {status}: <strong>{count}</strong>
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent executions */}
      <div style={{ background: "#1e293b", borderRadius: "12px", padding: "20px" }}>
        <h3 style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "16px" }}>
          Recent Executions
        </h3>
        {analytics.recent_executions.length === 0 ? (
          <div style={{ color: "#475569", fontSize: "14px" }}>No executions yet</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #334155" }}>
                <th style={thStyle}>ID</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Trigger</th>
                <th style={thStyle}>Started</th>
              </tr>
            </thead>
            <tbody>
              {analytics.recent_executions.map((ex) => (
                <tr key={ex.id} style={{ borderBottom: "1px solid #1e293b" }}>
                  <td style={tdStyle}>{ex.id.slice(0, 8)}...</td>
                  <td style={tdStyle}>
                    <span
                      style={{
                        color: statusColors[ex.status] || "#64748b",
                        fontWeight: 600,
                        textTransform: "capitalize",
                      }}
                    >
                      {ex.status}
                    </span>
                  </td>
                  <td style={tdStyle}>{ex.trigger}</td>
                  <td style={tdStyle}>
                    {ex.started_at ? new Date(ex.started_at).toLocaleString() : "—"}
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
  padding: "8px 12px",
  fontSize: "12px",
  color: "#64748b",
  fontWeight: 600,
  textTransform: "uppercase",
};

const tdStyle: React.CSSProperties = {
  padding: "10px 12px",
  fontSize: "14px",
  color: "#cbd5e1",
};

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const sec = ms / 1000;
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const min = sec / 60;
  return `${min.toFixed(1)}m`;
}
