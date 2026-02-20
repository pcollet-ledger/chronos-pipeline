import { useState } from "react";
import type { Workflow, WorkflowCreatePayload, WorkflowExecution } from "../types";
import { createWorkflow, deleteWorkflow, executeWorkflow } from "../services/api";
import { useTheme } from "../contexts/ThemeContext";
import {
  spacing,
  fontSize,
  fontWeight,
  radii,
  shadows,
} from "../theme";
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

  function btnStyle(bg: string): React.CSSProperties {
    return {
      padding: `${spacing.sm} ${spacing.lg}`,
      borderRadius: radii.md,
      border: "none",
      background: bg,
      color: "#fff",
      cursor: "pointer",
      fontSize: fontSize.md,
      fontWeight: fontWeight.medium,
    };
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: spacing.xl,
        }}
      >
        <h2 style={{ fontSize: fontSize.xxl, color: theme.text }}>Pipelines</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          data-testid="toggle-form-button"
          style={{
            padding: `${spacing.sm} ${spacing.xl}`,
            borderRadius: radii.lg,
            border: "none",
            background: showForm ? theme.surfaceHover : theme.primary,
            color: "#fff",
            cursor: "pointer",
            fontWeight: fontWeight.semibold,
            fontSize: fontSize.lg,
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
            borderRadius: radii.xl,
            padding: spacing.xl,
            marginBottom: spacing.xl,
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
          style={{ display: "flex", flexDirection: "column", gap: spacing.md }}
        >
          {workflows.map((wf) => (
            <div
              key={wf.id}
              style={{
                background: theme.surface,
                borderRadius: radii.xl,
                padding: `${spacing.lg} ${spacing.xl}`,
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: spacing.sm,
                }}
              >
                <div>
                  <h3
                    style={{
                      fontSize: fontSize.xl,
                      color: theme.text,
                      fontWeight: fontWeight.semibold,
                    }}
                  >
                    {wf.name}
                  </h3>
                  {wf.description && (
                    <p
                      style={{
                        fontSize: fontSize.md,
                        color: theme.textMuted,
                        marginTop: spacing.xs,
                      }}
                    >
                      {wf.description}
                    </p>
                  )}
                </div>
                <div style={{ display: "flex", gap: spacing.sm }}>
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
                    gap: spacing.sm,
                    marginBottom: spacing.sm,
                  }}
                >
                  {wf.tags.map((tag, idx) => (
                    <span
                      key={`${tag}-${idx}`}
                      style={{
                        padding: `2px ${spacing.sm}`,
                        borderRadius: radii.sm,
                        background: theme.tagBg,
                        color: theme.tagText,
                        fontSize: fontSize.sm,
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {wf.tasks.length > 0 && (
                <div style={{ marginTop: spacing.md }}>
                  <div
                    style={{
                      fontSize: fontSize.sm,
                      color: theme.textMuted,
                      marginBottom: spacing.sm,
                    }}
                  >
                    {wf.tasks.length} task{wf.tasks.length !== 1 ? "s" : ""}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      gap: spacing.sm,
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
            bottom: spacing.xl,
            right: spacing.xl,
            background:
              executionResult.status === "completed" ? "#064e3b" : "#7f1d1d",
            color: "#fff",
            padding: `${spacing.lg} ${spacing.xl}`,
            borderRadius: radii.xl,
            fontSize: fontSize.lg,
            boxShadow: shadows.lg,
            cursor: "pointer",
            maxWidth: "400px",
          }}
          onClick={() => setExecutionResult(null)}
        >
          <strong>Execution {executionResult.status}</strong>
          <div
            style={{ fontSize: fontSize.sm, marginTop: spacing.xs, opacity: 0.8 }}
          >
            {executionResult.task_results.length} tasks completed · Click to
            dismiss
          </div>
        </div>
      )}
    </div>
  );
}
