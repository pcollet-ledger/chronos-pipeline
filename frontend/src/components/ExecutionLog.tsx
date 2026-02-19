import type { WorkflowExecution } from "../types";
import ProgressBar from "./ProgressBar";

interface Props {
  execution: WorkflowExecution;
  onRetry?: (id: string) => void;
  onCancel?: (id: string) => void;
}

const statusColors: Record<string, string> = {
  completed: "#22c55e",
  failed: "#ef4444",
  running: "#eab308",
  pending: "#64748b",
  cancelled: "#6b7280",
};

export default function ExecutionLog({ execution, onRetry, onCancel }: Props) {
  const total = execution.task_results.length;
  const completed = execution.task_results.filter(
    (t) => t.status === "completed",
  ).length;
  const failed = execution.task_results.filter(
    (t) => t.status === "failed",
  ).length;

  const statusColor = statusColors[execution.status] ?? "#64748b";
  const canRetry = execution.status === "failed" || execution.status === "completed";
  const canCancel =
    execution.status === "running" || execution.status === "pending";

  return (
    <div
      data-testid="execution-log"
      style={{
        background: "#1e293b",
        borderRadius: "12px",
        padding: "16px 20px",
        borderLeft: `4px solid ${statusColor}`,
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
            data-testid="execution-id"
            style={{ fontSize: "13px", color: "#94a3b8", fontFamily: "monospace" }}
          >
            {execution.id.slice(0, 8)}...
          </span>
          <span
            data-testid="execution-status"
            style={{
              marginLeft: "12px",
              color: statusColor,
              fontWeight: 600,
              fontSize: "14px",
              textTransform: "capitalize",
            }}
          >
            {execution.status}
          </span>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          {canRetry && onRetry && (
            <button
              data-testid="retry-button"
              onClick={() => onRetry(execution.id)}
              style={{
                padding: "4px 12px",
                borderRadius: "4px",
                border: "1px solid #334155",
                background: "transparent",
                color: "#94a3b8",
                cursor: "pointer",
                fontSize: "12px",
              }}
            >
              Retry
            </button>
          )}
          {canCancel && onCancel && (
            <button
              data-testid="cancel-button"
              onClick={() => onCancel(execution.id)}
              style={{
                padding: "4px 12px",
                borderRadius: "4px",
                border: "1px solid #7f1d1d",
                background: "transparent",
                color: "#fca5a5",
                cursor: "pointer",
                fontSize: "12px",
              }}
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      <div style={{ marginBottom: "12px" }}>
        <ProgressBar
          value={completed + failed}
          max={total || 1}
          color={failed > 0 ? "#ef4444" : "#22c55e"}
          label={`${completed}/${total} tasks completed${failed > 0 ? `, ${failed} failed` : ""}`}
          showPercent
        />
      </div>

      <div style={{ display: "flex", gap: "16px", fontSize: "12px", color: "#64748b" }}>
        <span data-testid="execution-trigger">
          Trigger: <strong style={{ color: "#94a3b8" }}>{execution.trigger}</strong>
        </span>
        {execution.started_at && (
          <span data-testid="execution-started">
            Started: {new Date(execution.started_at).toLocaleString()}
          </span>
        )}
        {execution.completed_at && (
          <span data-testid="execution-completed">
            Completed: {new Date(execution.completed_at).toLocaleString()}
          </span>
        )}
      </div>

      {execution.task_results.length > 0 && (
        <div style={{ marginTop: "12px" }}>
          <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "8px" }}>
            Task Results
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {execution.task_results.map((tr) => (
              <div
                key={tr.task_id}
                data-testid={`task-result-${tr.task_id}`}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "6px 10px",
                  background: "#0f172a",
                  borderRadius: "6px",
                  fontSize: "12px",
                }}
              >
                <span style={{ color: "#e2e8f0", fontFamily: "monospace" }}>
                  {tr.task_id.slice(0, 8)}
                </span>
                <span
                  style={{
                    color: statusColors[tr.status] ?? "#64748b",
                    fontWeight: 600,
                    textTransform: "capitalize",
                  }}
                >
                  {tr.status}
                </span>
                {tr.duration_ms != null && (
                  <span style={{ color: "#64748b" }}>{tr.duration_ms}ms</span>
                )}
                {tr.error && (
                  <span style={{ color: "#fca5a5", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {tr.error}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
