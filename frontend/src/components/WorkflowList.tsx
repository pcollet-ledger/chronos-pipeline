import { useState } from "react";
import type { Workflow, WorkflowCreatePayload, WorkflowExecution } from "../types";
import { createWorkflow, deleteWorkflow, executeWorkflow } from "../services/api";
import { useTheme } from "../contexts/ThemeContext";
import TaskCard from "./TaskCard";
import WorkflowForm from "./WorkflowForm";
import EmptyState from "./EmptyState";
import ErrorBanner from "./ErrorBanner";

interface Props {
  workflows: Workflow[];
  onRefresh: () => void;
  loading?: boolean;
  onSelectWorkflow?: (id: string) => void;
}

export default function WorkflowList({ workflows, onRefresh, loading, onSelectWorkflow }: Props) {
  const { theme } = useTheme();
  const [showForm, setShowForm] = useState(false);
  const [executionResult, setExecutionResult] =
    useState<WorkflowExecution | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async (data: WorkflowCreatePayload) => {
    try {
      setError(null);
      await createWorkflow(data);
      setShowForm(false);
      onRefresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create workflow",
      );
    }
  };

  const handleExecute = async (id: string) => {
    try {
      setError(null);
      const result = await executeWorkflow(id);
      setExecutionResult(result);
      onRefresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to execute workflow",
      );
    }
  };

  const handleDelete = async (id: string) => {
    try {
      setError(null);
      await deleteWorkflow(id);
      onRefresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete workflow",
      );
    }
  };

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <h2 style={{ fontSize: "18px", color: theme.text }}>Pipelines</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          data-testid="toggle-form-button"
          style={{
            padding: "8px 20px",
            borderRadius: "8px",
            border: "none",
            background: showForm ? theme.surfaceHover : theme.primary,
            color: "#fff",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "14px",
          }}
        >
          {showForm ? "Cancel" : "New Pipeline"}
        </button>
      </div>

      {error && (
        <ErrorBanner
          message={error}
          onDismiss={() => setError(null)}
          onRetry={onRefresh}
        />
      )}

      {showForm && (
          <div
            style={{
              background: theme.surface,
              borderRadius: "12px",
              padding: "20px",
              marginBottom: "24px",
            }}
          >
            <WorkflowForm
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {!loading && workflows.length === 0 && !showForm ? (
        <EmptyState
          message="No pipelines yet. Create one to get started."
          actionLabel="Create Pipeline"
          onAction={() => setShowForm(true)}
        />
      ) : (
        <div
          style={{ display: "flex", flexDirection: "column", gap: "12px" }}
        >
          {workflows.map((wf) => (
            <div
              key={wf.id}
              style={{
                background: theme.surface,
                borderRadius: "12px",
                padding: "16px 20px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "8px",
                }}
              >
                <div>
                  <h3
                    style={{
                      fontSize: "16px",
                      color: theme.text,
                      fontWeight: 600,
                    }}
                  >
                    {wf.name}
                  </h3>
                  {wf.description && (
                    <p
                      style={{
                        fontSize: "13px",
                        color: theme.textSecondary,
                        marginTop: "4px",
                      }}
                    >
                      {wf.description}
                    </p>
                  )}
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  {onSelectWorkflow && (
                    <button
                      onClick={() => onSelectWorkflow(wf.id)}
                      data-testid="view-workflow-btn"
                      style={btnStyle(theme.primary)}
                    >
                      View
                    </button>
                  )}
                  <button
                    onClick={() => handleExecute(wf.id)}
                    style={btnStyle(theme.success)}
                  >
                    Run
                  </button>
                  <button
                    onClick={() => handleDelete(wf.id)}
                    style={btnStyle(theme.danger)}
                  >
                    Delete
                  </button>
                </div>
              </div>

              {wf.tags.length > 0 && (
                <div
                  style={{
                    display: "flex",
                    gap: "6px",
                    marginBottom: "8px",
                  }}
                >
                  {wf.tags.map((tag, idx) => (
                    <span
                      key={`${tag}-${idx}`}
                      style={{
                        padding: "2px 8px",
                        borderRadius: "4px",
                        background: theme.surfaceHover,
                        color: theme.textSecondary,
                        fontSize: "12px",
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {wf.tasks.length > 0 && (
                <div style={{ marginTop: "12px" }}>
                  <div
                    style={{
                      fontSize: "12px",
                      color: theme.textSecondary,
                      marginBottom: "8px",
                    }}
                  >
                    {wf.tasks.length} task{wf.tasks.length !== 1 ? "s" : ""}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      gap: "8px",
                      flexWrap: "wrap",
                    }}
                  >
                    {wf.tasks.map((task) => (
                      <TaskCard key={task.id} task={task} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {executionResult && (
        <div
          style={{
            position: "fixed",
            bottom: "20px",
            right: "20px",
            background:
              executionResult.status === "completed" ? "#064e3b" : "#7f1d1d",
            color: "#fff",
            padding: "16px 20px",
            borderRadius: "12px",
            fontSize: "14px",
            boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
            cursor: "pointer",
            maxWidth: "400px",
          }}
          onClick={() => setExecutionResult(null)}
        >
          <strong>Execution {executionResult.status}</strong>
          <div
            style={{ fontSize: "12px", marginTop: "4px", opacity: 0.8 }}
          >
            {executionResult.task_results.length} tasks completed · Click to
            dismiss
          </div>
        </div>
      )}
    </div>
  );
}

function btnStyle(bg: string): React.CSSProperties {
  return {
    padding: "6px 14px",
    borderRadius: "6px",
    border: "none",
    background: bg,
    color: "#fff",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: 500,
  };
}
