import { useEffect, useState } from "react";
import { useTheme } from "../ThemeContext";
import type { Workflow, WorkflowExecution } from "../types";
import {
  executeWorkflow,
  dryRunWorkflow,
  cloneWorkflow,
  listWorkflowExecutions,
  getWorkflowHistory,
} from "../services/api";
import TaskCard from "./TaskCard";
import ExecutionLog from "./ExecutionLog";
import LoadingSpinner from "./LoadingSpinner";
import ErrorBanner from "./ErrorBanner";

interface Props {
  workflow: Workflow;
  onBack: () => void;
  onRefresh: () => void;
}

export default function WorkflowDetail({ workflow, onBack, onRefresh }: Props) {
  const { theme } = useTheme();
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [history, setHistory] = useState<Workflow[]>([]);
  const [selectedExecution, setSelectedExecution] =
    useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [execs, hist] = await Promise.all([
          listWorkflowExecutions(workflow.id),
          getWorkflowHistory(workflow.id),
        ]);
        setExecutions(execs);
        setHistory(hist);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load details");
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [workflow.id]);

  const handleExecute = async () => {
    try {
      setError(null);
      const result = await executeWorkflow(workflow.id);
      setSelectedExecution(result);
      setExecutions((prev) => [result, ...prev]);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
    }
  };

  const handleDryRun = async () => {
    try {
      setError(null);
      const result = await dryRunWorkflow(workflow.id);
      setSelectedExecution(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dry run failed");
    }
  };

  const handleClone = async () => {
    try {
      setError(null);
      await cloneWorkflow(workflow.id);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clone failed");
    }
  };

  const btnStyle = (bg: string): React.CSSProperties => ({
    padding: "6px 14px",
    borderRadius: "6px",
    border: "none",
    background: bg,
    color: "#fff",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: 500,
  });

  return (
    <div>
      <button
        onClick={onBack}
        data-testid="back-button"
        style={{
          padding: "6px 14px",
          borderRadius: "6px",
          border: `1px solid ${theme.borderSubtle}`,
          background: "transparent",
          color: theme.textSecondary,
          cursor: "pointer",
          fontSize: "13px",
          marginBottom: "16px",
        }}
      >
        Back to list
      </button>

      {error && (
        <ErrorBanner message={error} onDismiss={() => setError(null)} />
      )}

      <div
        style={{
          background: theme.bgCard,
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "20px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div>
            <h2
              style={{
                fontSize: "20px",
                color: theme.textPrimary,
                margin: 0,
              }}
            >
              {workflow.name}
            </h2>
            {workflow.description && (
              <p
                style={{
                  fontSize: "14px",
                  color: theme.textMuted,
                  marginTop: "4px",
                }}
              >
                {workflow.description}
              </p>
            )}
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button onClick={handleExecute} style={btnStyle(theme.success)}>
              Run
            </button>
            <button onClick={handleDryRun} style={btnStyle(theme.info)}>
              Dry Run
            </button>
            <button onClick={handleClone} style={btnStyle(theme.warning)}>
              Clone
            </button>
          </div>
        </div>

        {workflow.tags.length > 0 && (
          <div
            style={{
              display: "flex",
              gap: "6px",
              marginTop: "12px",
              flexWrap: "wrap",
            }}
          >
            {workflow.tags.map((tag, idx) => (
              <span
                key={`${tag}-${idx}`}
                style={{
                  padding: "2px 8px",
                  borderRadius: "4px",
                  background: theme.borderSubtle,
                  color: theme.textSecondary,
                  fontSize: "12px",
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {workflow.tasks.length > 0 && (
          <div style={{ marginTop: "16px" }}>
            <div
              style={{
                fontSize: "12px",
                color: theme.textMuted,
                marginBottom: "8px",
              }}
            >
              {workflow.tasks.length} task{workflow.tasks.length !== 1 ? "s" : ""}
            </div>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {workflow.tasks.map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          </div>
        )}
      </div>

      {loading && <LoadingSpinner label="Loading details..." />}

      {selectedExecution && (
        <div style={{ marginBottom: "20px" }}>
          <ExecutionLog
            execution={selectedExecution}
            onClose={() => setSelectedExecution(null)}
          />
        </div>
      )}

      {/* Execution history */}
      <div
        style={{
          background: theme.bgCard,
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "20px",
        }}
      >
        <h3
          style={{
            fontSize: "14px",
            color: theme.textSecondary,
            marginBottom: "12px",
          }}
        >
          Execution History ({executions.length})
        </h3>
        {executions.length === 0 ? (
          <div style={{ color: theme.textMuted, fontSize: "14px" }}>
            No executions yet
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {executions.map((ex) => (
              <button
                key={ex.id}
                onClick={() => setSelectedExecution(ex)}
                data-testid={`execution-row-${ex.id}`}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "10px 14px",
                  borderRadius: "8px",
                  border: `1px solid ${theme.border}`,
                  background: "transparent",
                  cursor: "pointer",
                  textAlign: "left",
                  color: theme.textPrimary,
                  fontSize: "13px",
                }}
              >
                <span style={{ fontFamily: "monospace" }}>
                  {ex.id.slice(0, 8)}
                </span>
                <span
                  style={{
                    color:
                      ex.status === "completed"
                        ? theme.success
                        : ex.status === "failed"
                          ? theme.error
                          : theme.textMuted,
                    fontWeight: 600,
                    textTransform: "capitalize",
                  }}
                >
                  {ex.status}
                </span>
                <span style={{ color: theme.textMuted, fontSize: "12px" }}>
                  {ex.started_at
                    ? new Date(ex.started_at).toLocaleString()
                    : "—"}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Version history */}
      {history.length > 0 && (
        <div
          style={{
            background: theme.bgCard,
            borderRadius: "12px",
            padding: "20px",
          }}
        >
          <h3
            style={{
              fontSize: "14px",
              color: theme.textSecondary,
              marginBottom: "12px",
            }}
          >
            Version History ({history.length})
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {history.map((ver, idx) => (
              <div
                key={`${ver.id}-${idx}`}
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: `1px solid ${theme.border}`,
                  fontSize: "13px",
                  color: theme.textPrimary,
                }}
              >
                v{history.length - idx}: {ver.name} &middot;{" "}
                {ver.tasks.length} tasks
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
