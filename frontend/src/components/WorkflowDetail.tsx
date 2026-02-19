import { useState } from "react";
import { useTheme } from "../context/ThemeContext";
import { useExecutions } from "../hooks/useExecutions";
import type { Workflow, WorkflowExecution } from "../types";
import ExecutionLog from "./ExecutionLog";
import LoadingSpinner from "./LoadingSpinner";

interface WorkflowDetailProps {
  workflow: Workflow;
  onBack: () => void;
}

export default function WorkflowDetail({ workflow, onBack }: WorkflowDetailProps) {
  const { colors } = useTheme();
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);

  const {
    data: executions,
    loading,
    error,
  } = useExecutions({ workflowId: workflow.id, limit: 20 });

  return (
    <div>
      <button
        onClick={onBack}
        style={{
          background: "transparent",
          border: "none",
          color: colors.accent,
          cursor: "pointer",
          fontSize: "14px",
          padding: "0 0 16px",
        }}
      >
        &larr; Back to workflows
      </button>

      <div
        style={{
          background: colors.bgCard,
          borderRadius: "8px",
          border: `1px solid ${colors.border}`,
          padding: "20px",
          marginBottom: "16px",
        }}
      >
        <h2 style={{ margin: "0 0 8px", fontSize: "18px", color: colors.text }}>
          {workflow.name}
        </h2>
        {workflow.description && (
          <p style={{ margin: "0 0 12px", color: colors.textMuted, fontSize: "14px" }}>
            {workflow.description}
          </p>
        )}
        <div style={{ display: "flex", gap: "16px", fontSize: "13px", color: colors.textMuted }}>
          <span>{workflow.tasks.length} tasks</span>
          {workflow.schedule && <span>Schedule: {workflow.schedule}</span>}
          {workflow.tags.length > 0 && (
            <span>
              Tags:{" "}
              {workflow.tags.map((tag) => (
                <span
                  key={tag}
                  style={{
                    padding: "1px 6px",
                    borderRadius: "3px",
                    background: `${colors.accent}22`,
                    color: colors.accent,
                    fontSize: "11px",
                    marginLeft: "4px",
                  }}
                >
                  {tag}
                </span>
              ))}
            </span>
          )}
        </div>
      </div>

      <h3 style={{ fontSize: "15px", color: colors.text, margin: "0 0 12px" }}>
        Recent Executions
      </h3>

      {loading && <LoadingSpinner size={24} />}
      {error && (
        <div style={{ color: colors.error, fontSize: "13px" }}>{error}</div>
      )}

      {!loading && executions && executions.length === 0 && (
        <div style={{ color: colors.textMuted, fontSize: "13px" }}>
          No executions yet
        </div>
      )}

      {!loading && executions && executions.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "16px" }}>
          {executions.map((exec) => (
            <button
              key={exec.id}
              onClick={() => setSelectedExecution(exec)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "10px 14px",
                borderRadius: "6px",
                border: `1px solid ${
                  selectedExecution?.id === exec.id ? colors.accent : colors.border
                }`,
                background:
                  selectedExecution?.id === exec.id ? colors.bgHover : colors.bgCard,
                cursor: "pointer",
                textAlign: "left",
                fontSize: "13px",
                color: colors.text,
              }}
            >
              <span style={{ fontFamily: "monospace", fontSize: "11px", color: colors.textMuted }}>
                {exec.id.slice(0, 8)}
              </span>
              <span
                style={{
                  fontWeight: 600,
                  color:
                    exec.status === "completed"
                      ? colors.success
                      : exec.status === "failed"
                        ? colors.error
                        : colors.textMuted,
                }}
              >
                {exec.status}
              </span>
              <span style={{ color: colors.textMuted, marginLeft: "auto" }}>
                {exec.trigger}
              </span>
              {exec.started_at && (
                <span style={{ color: colors.textMuted, fontSize: "11px" }}>
                  {new Date(exec.started_at).toLocaleString()}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {selectedExecution && (
        <ExecutionLog execution={selectedExecution} />
      )}
    </div>
  );
}
