import type { Workflow, WorkflowExecution } from "../types";
import TaskCard from "./TaskCard";
import ExecutionLog from "./ExecutionLog";
import EmptyState from "./EmptyState";

interface Props {
  workflow: Workflow;
  executions: WorkflowExecution[];
  onExecute?: () => void;
  onDryRun?: () => void;
  onClone?: () => void;
  onDelete?: () => void;
  onRetry?: (id: string) => void;
  onCancel?: (id: string) => void;
  onBack?: () => void;
}

export default function WorkflowDetail({
  workflow,
  executions,
  onExecute,
  onDryRun,
  onClone,
  onDelete,
  onRetry,
  onCancel,
  onBack,
}: Props) {
  return (
    <div data-testid="workflow-detail">
      {onBack && (
        <button
          data-testid="back-button"
          onClick={onBack}
          style={{
            padding: "6px 14px",
            borderRadius: "6px",
            border: "1px solid #334155",
            background: "transparent",
            color: "#94a3b8",
            cursor: "pointer",
            fontSize: "13px",
            marginBottom: "16px",
          }}
        >
          Back
        </button>
      )}

      <div
        style={{
          background: "#1e293b",
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
            marginBottom: "12px",
          }}
        >
          <div>
            <h2
              data-testid="workflow-name"
              style={{ fontSize: "20px", color: "#e2e8f0", fontWeight: 700 }}
            >
              {workflow.name}
            </h2>
            {workflow.description && (
              <p
                data-testid="workflow-description"
                style={{ fontSize: "14px", color: "#64748b", marginTop: "4px" }}
              >
                {workflow.description}
              </p>
            )}
          </div>
          <div style={{ display: "flex", gap: "8px", flexShrink: 0 }}>
            {onDryRun && (
              <ActionButton
                testId="dry-run-button"
                label="Dry Run"
                color="#6366f1"
                onClick={onDryRun}
              />
            )}
            {onExecute && (
              <ActionButton
                testId="execute-button"
                label="Execute"
                color="#059669"
                onClick={onExecute}
              />
            )}
            {onClone && (
              <ActionButton
                testId="clone-button"
                label="Clone"
                color="#0284c7"
                onClick={onClone}
              />
            )}
            {onDelete && (
              <ActionButton
                testId="delete-button"
                label="Delete"
                color="#dc2626"
                onClick={onDelete}
              />
            )}
          </div>
        </div>

        {workflow.tags.length > 0 && (
          <div
            data-testid="workflow-tags"
            style={{ display: "flex", gap: "6px", marginBottom: "12px", flexWrap: "wrap" }}
          >
            {workflow.tags.map((tag, idx) => (
              <span
                key={`${tag}-${idx}`}
                style={{
                  padding: "2px 10px",
                  borderRadius: "4px",
                  background: "#334155",
                  color: "#94a3b8",
                  fontSize: "12px",
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <div
          style={{
            display: "flex",
            gap: "16px",
            fontSize: "12px",
            color: "#64748b",
          }}
        >
          <span data-testid="workflow-id">ID: {workflow.id.slice(0, 8)}...</span>
          {workflow.schedule && (
            <span data-testid="workflow-schedule">
              Schedule: {workflow.schedule}
            </span>
          )}
          <span data-testid="workflow-created">
            Created: {new Date(workflow.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {workflow.tasks.length > 0 && (
        <div style={{ marginBottom: "20px" }}>
          <h3
            style={{
              fontSize: "14px",
              color: "#94a3b8",
              marginBottom: "12px",
            }}
          >
            Tasks ({workflow.tasks.length})
          </h3>
          <div
            data-testid="task-list"
            style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}
          >
            {workflow.tasks.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        </div>
      )}

      <div>
        <h3
          style={{
            fontSize: "14px",
            color: "#94a3b8",
            marginBottom: "12px",
          }}
        >
          Executions ({executions.length})
        </h3>
        {executions.length === 0 ? (
          <EmptyState message="No executions yet. Run this workflow to see results." />
        ) : (
          <div
            data-testid="execution-list"
            style={{ display: "flex", flexDirection: "column", gap: "12px" }}
          >
            {executions.map((ex) => (
              <ExecutionLog
                key={ex.id}
                execution={ex}
                onRetry={onRetry}
                onCancel={onCancel}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ActionButton({
  testId,
  label,
  color,
  onClick,
}: {
  testId: string;
  label: string;
  color: string;
  onClick: () => void;
}) {
  return (
    <button
      data-testid={testId}
      onClick={onClick}
      style={{
        padding: "6px 14px",
        borderRadius: "6px",
        border: "none",
        background: color,
        color: "#fff",
        cursor: "pointer",
        fontSize: "13px",
        fontWeight: 500,
      }}
    >
      {label}
    </button>
  );
}
