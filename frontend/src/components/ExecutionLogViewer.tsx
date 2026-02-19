import { useCallback, useEffect, useState } from "react";
import type { WorkflowExecution } from "../types";
import { cancelExecution, getExecution, retryExecution } from "../services/api";
import { useTheme } from "../context/ThemeContext";
import ErrorBanner from "./ErrorBanner";
import LoadingSpinner from "./LoadingSpinner";

interface Props {
  executionId: string;
  onBack: () => void;
}

export default function ExecutionLogViewer({ executionId, onBack }: Props) {
  const { theme } = useTheme();
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const ex = await getExecution(executionId);
      setExecution(ex);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load execution");
    } finally {
      setLoading(false);
    }
  }, [executionId]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleRetry = async () => {
    try {
      setError(null);
      const result = await retryExecution(executionId);
      setExecution(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Retry failed");
    }
  };

  const handleCancel = async () => {
    try {
      setError(null);
      const result = await cancelExecution(executionId);
      setExecution(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cancel failed");
    }
  };

  if (loading) return <LoadingSpinner label="Loading execution..." />;

  const p = theme.palette;

  const statusColors: Record<string, string> = {
    completed: theme.colors.success,
    failed: theme.colors.error,
    running: theme.colors.warning,
    pending: p.textMuted,
    cancelled: p.textMuted,
  };

  const btnBase: React.CSSProperties = {
    padding: "6px 14px",
    borderRadius: theme.borderRadius.md,
    border: "none",
    cursor: "pointer",
    fontSize: theme.fontSize.md,
    fontWeight: theme.fontWeight.medium,
    color: "#fff",
  };

  if (!execution) {
    return (
      <div>
        <button onClick={onBack} style={{ ...btnBase, background: p.surfaceHover, color: p.textSecondary, marginBottom: theme.spacing.md }}>
          Back
        </button>
        <ErrorBanner message="Execution not found" />
      </div>
    );
  }

  const duration = execution.started_at && execution.completed_at
    ? new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()
    : null;

  return (
    <div>
      <button
        onClick={onBack}
        data-testid="back-button"
        style={{
          ...btnBase,
          background: "transparent",
          color: p.textSecondary,
          border: `1px solid ${p.border}`,
          marginBottom: theme.spacing.md,
        }}
      >
        Back
      </button>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Header */}
      <div
        style={{
          background: p.surface,
          borderRadius: theme.borderRadius.lg,
          padding: theme.spacing.lg,
          marginBottom: theme.spacing.md,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ fontSize: theme.fontSize.xxl, color: p.text }}>
              Execution{" "}
              <span style={{ color: p.textMuted, fontWeight: theme.fontWeight.normal }}>
                {execution.id.slice(0, 8)}...
              </span>
            </h2>
            <div style={{ display: "flex", gap: theme.spacing.lg, marginTop: theme.spacing.sm }}>
              <InfoItem label="Status" value={execution.status} color={statusColors[execution.status]} />
              <InfoItem label="Trigger" value={execution.trigger} color={p.textSecondary} />
              {duration !== null && (
                <InfoItem label="Duration" value={formatMs(duration)} color={p.textSecondary} />
              )}
              <InfoItem
                label="Started"
                value={execution.started_at ? new Date(execution.started_at).toLocaleString() : "—"}
                color={p.textSecondary}
              />
            </div>
          </div>
          <div style={{ display: "flex", gap: theme.spacing.sm }}>
            {execution.status === "failed" && (
              <button onClick={handleRetry} style={{ ...btnBase, background: theme.colors.warning }}>
                Retry
              </button>
            )}
            {execution.status === "running" && (
              <button onClick={handleCancel} style={{ ...btnBase, background: theme.colors.error }}>
                Cancel
              </button>
            )}
            <button onClick={() => void load()} style={{ ...btnBase, background: p.surfaceHover, color: p.textSecondary }}>
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Task Results */}
      <div
        style={{
          background: p.surface,
          borderRadius: theme.borderRadius.lg,
          padding: theme.spacing.lg,
        }}
      >
        <h3 style={{ fontSize: theme.fontSize.lg, color: p.text, marginBottom: theme.spacing.md }}>
          Task Results ({execution.task_results.length})
        </h3>
        {execution.task_results.length === 0 ? (
          <div style={{ color: p.textMuted, fontSize: theme.fontSize.base }}>No task results</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.sm }}>
            {execution.task_results.map((tr) => (
              <div
                key={tr.task_id}
                data-testid={`task-result-${tr.task_id}`}
                style={{
                  padding: theme.spacing.md,
                  background: p.background,
                  borderRadius: theme.borderRadius.md,
                  borderLeft: `3px solid ${statusColors[tr.status] ?? p.textMuted}`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <span style={{ color: p.text, fontWeight: theme.fontWeight.semibold, fontSize: theme.fontSize.base }}>
                      {tr.task_id.slice(0, 8)}...
                    </span>
                    <span
                      style={{
                        marginLeft: theme.spacing.sm,
                        color: statusColors[tr.status] ?? p.textMuted,
                        fontWeight: theme.fontWeight.semibold,
                        textTransform: "capitalize",
                        fontSize: theme.fontSize.md,
                      }}
                    >
                      {tr.status}
                    </span>
                  </div>
                  {tr.duration_ms !== null && (
                    <span style={{ color: p.textMuted, fontSize: theme.fontSize.sm }}>
                      {formatMs(tr.duration_ms)}
                    </span>
                  )}
                </div>
                {tr.error && (
                  <div
                    style={{
                      marginTop: theme.spacing.sm,
                      padding: theme.spacing.sm,
                      background: "rgba(239, 68, 68, 0.1)",
                      borderRadius: theme.borderRadius.sm,
                      color: theme.colors.errorLight,
                      fontSize: theme.fontSize.md,
                      fontFamily: "monospace",
                    }}
                  >
                    {tr.error}
                  </div>
                )}
                {tr.output && Object.keys(tr.output).length > 0 && (
                  <div
                    style={{
                      marginTop: theme.spacing.sm,
                      padding: theme.spacing.sm,
                      background: p.surfaceHover,
                      borderRadius: theme.borderRadius.sm,
                      fontSize: theme.fontSize.sm,
                      fontFamily: "monospace",
                      color: p.textSecondary,
                      whiteSpace: "pre-wrap",
                      overflowX: "auto",
                    }}
                  >
                    {JSON.stringify(tr.output, null, 2)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Metadata */}
      {Object.keys(execution.metadata).length > 0 && (
        <div
          style={{
            background: p.surface,
            borderRadius: theme.borderRadius.lg,
            padding: theme.spacing.lg,
            marginTop: theme.spacing.md,
          }}
        >
          <h3 style={{ fontSize: theme.fontSize.lg, color: p.text, marginBottom: theme.spacing.md }}>
            Metadata
          </h3>
          <pre
            style={{
              padding: theme.spacing.md,
              background: p.background,
              borderRadius: theme.borderRadius.md,
              color: p.textSecondary,
              fontSize: theme.fontSize.sm,
              fontFamily: "monospace",
              whiteSpace: "pre-wrap",
              overflowX: "auto",
              margin: 0,
            }}
          >
            {JSON.stringify(execution.metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function InfoItem({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontSize: "14px", color: color ?? "#e2e8f0", fontWeight: 600, textTransform: "capitalize" }}>
        {value}
      </div>
    </div>
  );
}

function formatMs(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  const sec = ms / 1000;
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const min = sec / 60;
  return `${min.toFixed(1)}m`;
}
