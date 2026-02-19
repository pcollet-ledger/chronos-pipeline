import { useEffect, useState } from "react";
import type { WorkflowExecution } from "../types";
import * as api from "../services/api";
import { getStatusColor } from "../theme";
import LoadingSpinner from "./LoadingSpinner";
import ErrorBanner from "./ErrorBanner";
import EmptyState from "./EmptyState";

interface ExecutionLogProps {
  executionId: string;
}

export default function ExecutionLog({ executionId }: ExecutionLogProps) {
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getExecution(executionId)
      .then(setExecution)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [executionId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} />;
  if (!execution) return <EmptyState message="Execution not found" />;

  return (
    <div data-testid="execution-log">
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <h3 style={{ margin: 0 }}>Execution Log</h3>
        <span
          style={{
            padding: "2px 8px",
            borderRadius: 4,
            backgroundColor: getStatusColor(execution.status),
            color: "#fff",
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          {execution.status}
        </span>
      </div>

      <div style={{ fontSize: 14, color: "#6b7280", marginBottom: 16 }}>
        <div>Execution ID: <code>{execution.id}</code></div>
        <div>Workflow: <code>{execution.workflow_id}</code></div>
        <div>Trigger: {execution.trigger}</div>
        <div>Started: {execution.started_at ? new Date(execution.started_at).toLocaleString() : "—"}</div>
        {execution.completed_at && (
          <div>Completed: {new Date(execution.completed_at).toLocaleString()}</div>
        )}
      </div>

      {execution.task_results.length === 0 ? (
        <EmptyState message="No task results recorded" />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {execution.task_results.map((result, idx) => (
            <div
              key={result.task_id}
              data-testid="task-result-row"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "8px 12px",
                borderRadius: 6,
                backgroundColor: idx % 2 === 0 ? "#f9fafb" : "#ffffff",
                border: "1px solid #e5e7eb",
              }}
            >
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  backgroundColor: getStatusColor(result.status),
                  flexShrink: 0,
                }}
              />
              <span style={{ flex: 1, fontFamily: "monospace", fontSize: 13 }}>
                {result.task_id}
              </span>
              <span style={{ fontSize: 13 }}>{result.status}</span>
              {result.duration_ms !== null && result.duration_ms !== undefined && (
                <span style={{ fontSize: 12, color: "#6b7280" }}>
                  {result.duration_ms}ms
                </span>
              )}
              {result.error && (
                <span style={{ fontSize: 12, color: "#dc2626" }} title={result.error}>
                  Error
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
