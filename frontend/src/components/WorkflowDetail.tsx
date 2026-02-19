import { useEffect, useState } from "react";
import type { Workflow, WorkflowExecution } from "../types";
import {
  executeWorkflow,
  getWorkflow,
  listWorkflowExecutions,
} from "../services/api";
import LoadingSpinner from "./LoadingSpinner";
import ErrorBanner from "./ErrorBanner";
import EmptyState from "./EmptyState";
import ExecutionLog from "./ExecutionLog";

interface Props {
  workflowId: string;
  onBack?: () => void;
}

const statusColors: Record<string, string> = {
  completed: "#22c55e",
  failed: "#ef4444",
  running: "#eab308",
  pending: "#64748b",
  cancelled: "#6b7280",
};

export default function WorkflowDetail({ workflowId, onBack }: Props) {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedExecution, setSelectedExecution] =
    useState<WorkflowExecution | null>(null);

  const load = async () => {
    try {
      setError(null);
      setLoading(true);
      const [wf, execs] = await Promise.all([
        getWorkflow(workflowId),
        listWorkflowExecutions(workflowId),
      ]);
      setWorkflow(wf);
      setExecutions(execs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workflow");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [workflowId]);

  const handleExecute = async () => {
    try {
      setError(null);
      const result = await executeWorkflow(workflowId);
      setSelectedExecution(result);
      void load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to execute workflow",
      );
    }
  };

  if (loading) return <LoadingSpinner label="Loading workflow..." />;

  if (error && !workflow) {
    return (
      <ErrorBanner
        message={error}
        onRetry={() => void load()}
        onDismiss={onBack}
      />
    );
  }

  if (!workflow) {
    return <EmptyState message="Workflow not found." />;
  }

  return (
    <div data-testid="workflow-detail">
      <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "20px" }}>
        {onBack && (
          <button
            onClick={onBack}
            style={{
              padding: "6px 14px",
              borderRadius: "6px",
              border: "1px solid #334155",
              background: "transparent",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "13px",
            }}
          >
            Back
          </button>
        )}
        <h2 data-testid="workflow-name" style={{ fontSize: "20px", color: "#e2e8f0", fontWeight: 700 }}>
          {workflow.name}
        </h2>
        <button
          onClick={() => void handleExecute()}
          data-testid="execute-button"
          style={{
            marginLeft: "auto",
            padding: "8px 24px",
            borderRadius: "8px",
            border: "none",
            background: "#059669",
            color: "#fff",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "14px",
          }}
        >
          Execute
        </button>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {workflow.description && (
        <p style={{ color: "#94a3b8", fontSize: "14px", marginBottom: "16px" }}>
          {workflow.description}
        </p>
      )}

      <div style={{ background: "#1e293b", borderRadius: "12px", padding: "16px", marginBottom: "20px" }}>
        <h3 style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "12px" }}>
          Tasks ({workflow.tasks.length})
        </h3>
        {workflow.tasks.length === 0 ? (
          <div style={{ color: "#475569", fontSize: "13px" }}>No tasks defined.</div>
        ) : (
          <div data-testid="task-list">
            {workflow.tasks.map((task) => {
              const indent = task.depends_on.length > 0 ? 20 : 0;
              return (
                <div
                  key={task.id}
                  style={{
                    marginLeft: `${indent}px`,
                    padding: "8px 12px",
                    borderLeft: "2px solid #334155",
                    marginBottom: "6px",
                  }}
                >
                  <div style={{ fontWeight: 600, color: "#e2e8f0", fontSize: "13px" }}>
                    {task.name}
                  </div>
                  <div style={{ fontSize: "11px", color: "#64748b" }}>
                    Action: {task.action}
                    {task.depends_on.length > 0 && ` | Depends on: ${task.depends_on.join(", ")}`}
                  </div>
                  {Object.keys(task.parameters).length > 0 && (
                    <div style={{ fontSize: "11px", color: "#475569", marginTop: "2px" }}>
                      Params: {JSON.stringify(task.parameters)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div style={{ background: "#1e293b", borderRadius: "12px", padding: "16px" }}>
        <h3 style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "12px" }}>
          Execution History
        </h3>
        {executions.length === 0 ? (
          <div style={{ color: "#475569", fontSize: "13px" }}>No executions yet.</div>
        ) : (
          <div data-testid="execution-history">
            {executions.map((ex) => (
              <div
                key={ex.id}
                onClick={() => setSelectedExecution(ex)}
                style={{
                  padding: "8px 12px",
                  borderBottom: "1px solid #0f172a",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                }}
              >
                <span
                  data-testid={`status-badge-${ex.id}`}
                  style={{
                    padding: "2px 8px",
                    borderRadius: "4px",
                    background: statusColors[ex.status] ?? "#64748b",
                    color: "#fff",
                    fontSize: "11px",
                    fontWeight: 600,
                    textTransform: "capitalize",
                  }}
                >
                  {ex.status}
                </span>
                <span style={{ color: "#94a3b8", fontSize: "12px" }}>
                  {ex.id.slice(0, 8)}...
                </span>
                <span style={{ color: "#64748b", fontSize: "12px", marginLeft: "auto" }}>
                  {ex.trigger}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedExecution && (
        <div style={{ marginTop: "20px", background: "#1e293b", borderRadius: "12px", padding: "16px" }}>
          <h3 style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "12px" }}>
            Execution Details
          </h3>
          <ExecutionLog
            execution={selectedExecution}
            onRetryComplete={(newEx) => {
              setSelectedExecution(newEx);
              void load();
            }}
          />
        </div>
      )}
    </div>
  );
}
