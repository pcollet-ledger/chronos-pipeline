import { useState } from "react";
import type { Workflow, WorkflowExecution } from "../types";
import { deleteWorkflow, executeWorkflow } from "../services/api";
import TaskCard from "./TaskCard";
import WorkflowForm from "./WorkflowForm";
import {
  colors,
  fontSizes,
  fontWeights,
  radii,
  shadows,
  spacing,
} from "../styles/theme";

interface Props {
  workflows: Workflow[];
  onRefresh: () => void;
}

export default function WorkflowList({ workflows, onRefresh }: Props) {
  const [executionResult, setExecutionResult] =
    useState<WorkflowExecution | null>(null);
  const [editingWorkflow, setEditingWorkflow] = useState<Workflow | null>(null);
  const [showForm, setShowForm] = useState(false);

  const handleExecute = async (id: string) => {
    const result = await executeWorkflow(id);
    setExecutionResult(result);
    onRefresh();
  };

  const handleDelete = async (id: string) => {
    await deleteWorkflow(id);
    onRefresh();
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingWorkflow(null);
    onRefresh();
  };

  const handleEdit = (wf: Workflow) => {
    setEditingWorkflow(wf);
    setShowForm(true);
  };

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
        <h2
          style={{
            fontSize: fontSizes.xl,
            color: colors.neutral[200],
          }}
        >
          Pipelines
        </h2>
        <button
          onClick={() => {
            setEditingWorkflow(null);
            setShowForm(!showForm);
          }}
          style={{
            padding: `10px ${spacing.xl}`,
            borderRadius: radii.lg,
            border: "none",
            background: colors.primary.main,
            color: "#fff",
            cursor: "pointer",
            fontWeight: fontWeights.semibold,
            fontSize: fontSizes.base,
          }}
        >
          {showForm ? "Cancel" : "New Pipeline"}
        </button>
      </div>

      {/* Create / Edit form */}
      {showForm && (
        <div style={{ marginBottom: spacing.xxl }}>
          <WorkflowForm
            workflow={editingWorkflow ?? undefined}
            onSuccess={handleFormSuccess}
            onCancel={() => {
              setShowForm(false);
              setEditingWorkflow(null);
            }}
          />
        </div>
      )}

      {/* Pipeline list */}
      {workflows.length === 0 ? (
        <div
          style={{
            color: colors.neutral[600],
            textAlign: "center",
            padding: spacing.xxxxl,
          }}
        >
          No pipelines yet. Create one above.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
          {workflows.map((wf) => (
            <div
              key={wf.id}
              style={{
                background: colors.neutral[800],
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
                      fontSize: fontSizes.lg,
                      color: colors.neutral[200],
                      fontWeight: fontWeights.semibold,
                    }}
                  >
                    {wf.name}
                  </h3>
                  {wf.description && (
                    <p
                      style={{
                        fontSize: fontSizes.md,
                        color: colors.neutral[500],
                        marginTop: spacing.xs,
                      }}
                    >
                      {wf.description}
                    </p>
                  )}
                </div>
                <div style={{ display: "flex", gap: spacing.sm }}>
                  <button
                    onClick={() => handleEdit(wf)}
                    style={btnStyle(colors.primary.main)}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleExecute(wf.id)}
                    style={btnStyle(colors.success.dark)}
                  >
                    Run
                  </button>
                  <button
                    onClick={() => handleDelete(wf.id)}
                    style={btnStyle(colors.error.dark)}
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Tags */}
              {wf.tags.length > 0 && (
                <div
                  style={{
                    display: "flex",
                    gap: spacing.sm,
                    marginBottom: spacing.sm,
                    flexWrap: "wrap",
                  }}
                >
                  {wf.tags.map((tag) => (
                    <span
                      key={tag}
                      style={{
                        padding: `2px ${spacing.sm}`,
                        borderRadius: radii.sm,
                        background: colors.neutral[700],
                        color: colors.neutral[400],
                        fontSize: fontSizes.sm,
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Tasks */}
              {wf.tasks.length > 0 && (
                <div style={{ marginTop: spacing.md }}>
                  <div
                    style={{
                      fontSize: fontSizes.sm,
                      color: colors.neutral[500],
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

      {/* Execution result popup */}
      {executionResult && (
        <div
          style={{
            position: "fixed",
            bottom: spacing.xl,
            right: spacing.xl,
            background:
              executionResult.status === "completed"
                ? colors.success.dark
                : colors.error.bg,
            color: "#fff",
            padding: `${spacing.lg} ${spacing.xl}`,
            borderRadius: radii.xl,
            fontSize: fontSizes.base,
            boxShadow: shadows.lg,
            cursor: "pointer",
            maxWidth: "400px",
          }}
          onClick={() => setExecutionResult(null)}
        >
          <strong>Execution {executionResult.status}</strong>
          <div style={{ fontSize: fontSizes.sm, marginTop: spacing.xs, opacity: 0.8 }}>
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
    padding: `6px ${spacing.lg}`,
    borderRadius: radii.md,
    border: "none",
    background: bg,
    color: "#fff",
    cursor: "pointer",
    fontSize: fontSizes.md,
    fontWeight: fontWeights.medium,
  };
}
