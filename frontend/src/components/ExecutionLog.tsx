import { useEffect, useState, useCallback } from "react";
import type { WorkflowExecution, TaskResult } from "../types";
import * as api from "../services/api";
import { getStatusColor } from "../theme";
import LoadingSpinner from "./LoadingSpinner";
import ErrorBanner from "./ErrorBanner";
import EmptyState from "./EmptyState";

interface ExecutionLogProps {
  executionId: string;
}

function getStatusIcon(status: string): string {
  switch (status) {
    case "completed":
      return "\u2713";
    case "failed":
      return "\u2717";
    case "running":
    case "pending":
      return "\u23F3";
    case "cancelled":
      return "\u2014";
    default:
      return "\u2022";
  }
}

function formatDuration(ms: number | null): string {
  if (ms === null || ms === undefined) return "\u2014";
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60_000);
  const seconds = ((ms % 60_000) / 1000).toFixed(0);
  return `${minutes}m ${seconds}s`;
}

function TimelineStep({ result, isLast, defaultExpanded }: {
  result: TaskResult;
  isLast: boolean;
  defaultExpanded: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const isFailed = result.status === "failed";
  const hasDetails = result.output !== null || result.error !== null;
  const statusIcon = getStatusIcon(result.status);

  return (
    <div
      data-testid="task-result-row"
      style={{ display: "flex", gap: 12, minHeight: 48 }}
    >
      {/* Timeline gutter */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 32, flexShrink: 0 }}>
        <div
          data-testid="status-icon"
          style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            backgroundColor: getStatusColor(result.status),
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 14,
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {statusIcon}
        </div>
        {!isLast && (
          <div
            style={{
              width: 2,
              flex: 1,
              backgroundColor: "#e5e7eb",
              marginTop: 4,
              marginBottom: 4,
            }}
          />
        )}
      </div>

      {/* Step content */}
      <div
        style={{
          flex: 1,
          paddingBottom: isLast ? 0 : 16,
          borderRadius: 8,
          padding: "8px 12px",
          backgroundColor: isFailed ? "#fef2f2" : "transparent",
          border: isFailed ? "1px solid #fecaca" : "1px solid transparent",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <span style={{ fontFamily: "monospace", fontSize: 14, fontWeight: 600 }}>
            {result.task_id}
          </span>
          <span
            style={{
              fontSize: 12,
              padding: "1px 6px",
              borderRadius: 4,
              backgroundColor: getStatusColor(result.status),
              color: "#fff",
              fontWeight: 500,
            }}
          >
            {result.status}
          </span>
          <span style={{ fontSize: 12, color: "#6b7280", marginLeft: "auto" }}>
            {formatDuration(result.duration_ms)}
          </span>
          {hasDetails && (
            <button
              data-testid="toggle-details"
              onClick={() => setExpanded(!expanded)}
              style={{
                background: "none",
                border: "1px solid #d1d5db",
                borderRadius: 4,
                padding: "2px 8px",
                fontSize: 12,
                cursor: "pointer",
                color: "#374151",
              }}
            >
              {expanded ? "Hide details" : "Show details"}
            </button>
          )}
        </div>

        {isFailed && result.error && (
          <div
            data-testid="error-message"
            style={{
              marginTop: 6,
              fontSize: 13,
              color: "#dc2626",
              fontWeight: 500,
            }}
          >
            {result.error}
          </div>
        )}

        {expanded && hasDetails && (
          <div data-testid="task-details" style={{ marginTop: 8 }}>
            {result.output && (
              <pre
                style={{
                  fontSize: 12,
                  backgroundColor: "#f3f4f6",
                  padding: 8,
                  borderRadius: 4,
                  overflow: "auto",
                  margin: 0,
                }}
              >
                {JSON.stringify(result.output, null, 2)}
              </pre>
            )}
            {result.error && !isFailed && (
              <div style={{ fontSize: 13, color: "#dc2626" }}>{result.error}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ExecutionLog({ executionId }: ExecutionLogProps) {
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  const fetchExecution = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .getExecution(executionId)
      .then(setExecution)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [executionId]);

  useEffect(() => {
    fetchExecution();
  }, [fetchExecution]);

  const handleRetry = useCallback(async () => {
    if (!execution) return;
    setRetrying(true);
    try {
      const retried = await api.retryExecution(execution.id);
      setExecution(retried);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry failed");
    } finally {
      setRetrying(false);
    }
  }, [execution]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={error} />;
  if (!execution) return <EmptyState message="Execution not found" />;

  const canRetry = execution.status === "failed";

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
        {canRetry && (
          <button
            data-testid="retry-button"
            onClick={handleRetry}
            disabled={retrying}
            style={{
              marginLeft: "auto",
              padding: "6px 16px",
              borderRadius: 6,
              border: "none",
              backgroundColor: "#2563eb",
              color: "#fff",
              fontSize: 13,
              fontWeight: 600,
              cursor: retrying ? "not-allowed" : "pointer",
              opacity: retrying ? 0.6 : 1,
            }}
          >
            {retrying ? "Retrying\u2026" : "Retry"}
          </button>
        )}
      </div>

      <div style={{ fontSize: 14, color: "#6b7280", marginBottom: 16 }}>
        <div>Execution ID: <code>{execution.id}</code></div>
        <div>Workflow: <code>{execution.workflow_id}</code></div>
        <div>Trigger: {execution.trigger}</div>
        <div>Started: {execution.started_at ? new Date(execution.started_at).toLocaleString() : "\u2014"}</div>
        {execution.completed_at && (
          <div>Completed: {new Date(execution.completed_at).toLocaleString()}</div>
        )}
      </div>

      {execution.task_results.length === 0 ? (
        <EmptyState message="No task results recorded" />
      ) : (
        <div data-testid="timeline" style={{ display: "flex", flexDirection: "column" }}>
          {execution.task_results.map((result, idx) => (
            <TimelineStep
              key={result.task_id}
              result={result}
              isLast={idx === execution.task_results.length - 1}
              defaultExpanded={result.status === "failed"}
            />
          ))}
        </div>
      )}
    </div>
  );
}
