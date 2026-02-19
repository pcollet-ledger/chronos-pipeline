import type { WorkflowExecution, TaskResult } from "../types";
import { useTheme } from "../context/ThemeContext";
import LoadingSpinner from "./LoadingSpinner";
import EmptyState from "./EmptyState";

interface Props {
  executions: WorkflowExecution[];
  loading?: boolean;
}

const statusColors: Record<string, string> = {
  completed: "#22c55e",
  failed: "#ef4444",
  running: "#eab308",
  pending: "#64748b",
  cancelled: "#6b7280",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      data-testid={`status-badge-${status}`}
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: "4px",
        background: `${statusColors[status] ?? "#64748b"}22`,
        color: statusColors[status] ?? "#64748b",
        fontSize: "12px",
        fontWeight: 600,
        textTransform: "capitalize",
      }}
    >
      {status}
    </span>
  );
}

function TaskResultRow({ result }: { result: TaskResult }) {
  const { palette } = useTheme();

  const duration =
    result.duration_ms !== null ? `${result.duration_ms}ms` : "—";

  return (
    <tr style={{ borderBottom: `1px solid ${palette.border}` }}>
      <td style={tdStyle}>{result.task_id.slice(0, 8)}...</td>
      <td style={tdStyle}>
        <StatusBadge status={result.status} />
      </td>
      <td style={tdStyle}>{duration}</td>
      <td style={tdStyle}>
        {result.error ? (
          <span style={{ color: "#ef4444", fontSize: "12px" }}>
            {result.error}
          </span>
        ) : result.output ? (
          <span style={{ color: palette.textSecondary, fontSize: "12px" }}>
            {JSON.stringify(result.output).slice(0, 80)}
          </span>
        ) : (
          "—"
        )}
      </td>
    </tr>
  );
}

function ExecutionEntry({ execution }: { execution: WorkflowExecution }) {
  const { palette } = useTheme();

  const startedAt = execution.started_at
    ? new Date(execution.started_at).toLocaleString()
    : "—";
  const completedAt = execution.completed_at
    ? new Date(execution.completed_at).toLocaleString()
    : "—";

  return (
    <div
      data-testid={`execution-entry-${execution.id}`}
      style={{
        background: palette.surface,
        borderRadius: "12px",
        padding: "16px 20px",
        marginBottom: "12px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "12px",
        }}
      >
        <div>
          <span
            style={{
              fontSize: "14px",
              fontWeight: 600,
              color: palette.textPrimary,
              marginRight: "12px",
            }}
          >
            {execution.id.slice(0, 12)}...
          </span>
          <StatusBadge status={execution.status} />
        </div>
        <div
          style={{
            fontSize: "12px",
            color: palette.textMuted,
            display: "flex",
            gap: "16px",
          }}
        >
          <span>Trigger: {execution.trigger}</span>
          <span>Started: {startedAt}</span>
          <span>Completed: {completedAt}</span>
        </div>
      </div>

      {execution.task_results.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${palette.border}` }}>
              <th style={thStyle}>Task ID</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Duration</th>
              <th style={thStyle}>Output / Error</th>
            </tr>
          </thead>
          <tbody>
            {execution.task_results.map((tr) => (
              <TaskResultRow key={tr.task_id} result={tr} />
            ))}
          </tbody>
        </table>
      )}

      {execution.task_results.length === 0 && (
        <div style={{ color: palette.textMuted, fontSize: "13px" }}>
          No task results recorded.
        </div>
      )}
    </div>
  );
}

export default function ExecutionLog({ executions, loading }: Props) {
  if (loading) {
    return <LoadingSpinner label="Loading executions..." />;
  }

  if (executions.length === 0) {
    return <EmptyState message="No executions to display." />;
  }

  return (
    <div data-testid="execution-log">
      <h3
        style={{
          fontSize: "16px",
          fontWeight: 600,
          color: "#e2e8f0",
          marginBottom: "16px",
        }}
      >
        Execution Log ({executions.length})
      </h3>
      {executions.map((ex) => (
        <ExecutionEntry key={ex.id} execution={ex} />
      ))}
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
  padding: "8px 12px",
  fontSize: "13px",
  color: "#cbd5e1",
};
