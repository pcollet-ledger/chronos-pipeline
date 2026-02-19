import { useState } from "react";
import type { TaskResult, WorkflowExecution } from "../types";
import { retryExecution } from "../services/api";

interface Props {
  execution: WorkflowExecution;
  onRetryComplete?: (newExecution: WorkflowExecution) => void;
}

function statusIcon(status: string): string {
  if (status === "completed") return "\u2713";
  if (status === "failed") return "\u2717";
  return "\u23F3";
}

function formatDuration(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const sec = ms / 1000;
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const min = sec / 60;
  return `${min.toFixed(1)}m`;
}

function TaskStep({ result, defaultExpanded }: { result: TaskResult; defaultExpanded: boolean }) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const isFailed = result.status === "failed";

  return (
    <div
      data-testid={`task-step-${result.task_id}`}
      style={{
        borderLeft: `3px solid ${isFailed ? "#ef4444" : result.status === "completed" ? "#22c55e" : "#eab308"}`,
        paddingLeft: "16px",
        marginBottom: "12px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          cursor: "pointer",
        }}
        onClick={() => setExpanded(!expanded)}
        data-testid={`toggle-${result.task_id}`}
      >
        <span
          data-testid={`icon-${result.task_id}`}
          style={{
            fontSize: "16px",
            color: isFailed ? "#ef4444" : result.status === "completed" ? "#22c55e" : "#eab308",
          }}
        >
          {statusIcon(result.status)}
        </span>
        <span style={{ fontWeight: 600, color: "#e2e8f0", fontSize: "14px" }}>
          {result.task_id}
        </span>
        <span style={{ color: "#64748b", fontSize: "12px", marginLeft: "auto" }}>
          {formatDuration(result.duration_ms)}
        </span>
      </div>

      {isFailed && result.error && (
        <div
          data-testid={`error-${result.task_id}`}
          style={{
            marginTop: "4px",
            padding: "8px",
            background: "#7f1d1d",
            borderRadius: "4px",
            color: "#fca5a5",
            fontSize: "12px",
          }}
        >
          {result.error}
        </div>
      )}

      {expanded && result.output && (
        <pre
          data-testid={`output-${result.task_id}`}
          style={{
            marginTop: "4px",
            padding: "8px",
            background: "#0f172a",
            borderRadius: "4px",
            color: "#94a3b8",
            fontSize: "11px",
            overflow: "auto",
            maxHeight: "200px",
          }}
        >
          {JSON.stringify(result.output, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function ExecutionLog({ execution, onRetryComplete }: Props) {
  const [retrying, setRetrying] = useState(false);

  const handleRetry = async () => {
    setRetrying(true);
    try {
      const result = await retryExecution(execution.id);
      onRetryComplete?.(result);
    } finally {
      setRetrying(false);
    }
  };

  if (execution.task_results.length === 0) {
    return (
      <div data-testid="empty-log" style={{ color: "#64748b", padding: "16px" }}>
        No task results to display.
      </div>
    );
  }

  return (
    <div data-testid="execution-log">
      {execution.task_results.map((result) => (
        <TaskStep
          key={result.task_id}
          result={result}
          defaultExpanded={result.status === "failed"}
        />
      ))}

      {execution.status === "failed" && (
        <button
          onClick={() => void handleRetry()}
          disabled={retrying}
          data-testid="retry-button"
          style={{
            marginTop: "12px",
            padding: "8px 20px",
            borderRadius: "6px",
            border: "none",
            background: "#2563eb",
            color: "#fff",
            cursor: retrying ? "not-allowed" : "pointer",
            fontWeight: 600,
            fontSize: "14px",
            opacity: retrying ? 0.6 : 1,
          }}
        >
          {retrying ? "Retrying..." : "Retry Failed Tasks"}
        </button>
      )}
    </div>
  );
}
