import { useCallback, useEffect, useState } from "react";
import type { Workflow, WorkflowExecution } from "../types";
import {
  getWorkflow,
  listWorkflowExecutions,
  executeWorkflow,
  cloneWorkflow,
  dryRunWorkflow,
  addWorkflowTags,
  removeWorkflowTag,
  getWorkflowHistory,
} from "../services/api";
import { useTheme } from "../context/ThemeContext";
import TaskCard from "./TaskCard";
import ExecutionLog from "./ExecutionLog";
import LoadingSpinner from "./LoadingSpinner";
import ErrorBanner from "./ErrorBanner";

interface Props {
  workflowId: string;
  onBack: () => void;
}

export default function WorkflowDetail({ workflowId, onBack }: Props) {
  const { palette } = useTheme();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [history, setHistory] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tagInput, setTagInput] = useState("");
  const [activeTab, setActiveTab] = useState<"tasks" | "executions" | "history">("tasks");

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [wf, execs, hist] = await Promise.all([
        getWorkflow(workflowId),
        listWorkflowExecutions(workflowId),
        getWorkflowHistory(workflowId),
      ]);
      setWorkflow(wf);
      setExecutions(execs);
      setHistory(hist);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workflow");
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleExecute = async () => {
    try {
      setError(null);
      await executeWorkflow(workflowId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
    }
  };

  const handleClone = async () => {
    try {
      setError(null);
      await cloneWorkflow(workflowId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clone failed");
    }
  };

  const handleDryRun = async () => {
    try {
      setError(null);
      const result = await dryRunWorkflow(workflowId);
      setExecutions((prev) => [result, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dry run failed");
    }
  };

  const handleAddTag = async () => {
    if (!tagInput.trim()) return;
    try {
      setError(null);
      const updated = await addWorkflowTags(workflowId, [tagInput.trim()]);
      setWorkflow(updated);
      setTagInput("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add tag");
    }
  };

  const handleRemoveTag = async (tag: string) => {
    try {
      setError(null);
      const updated = await removeWorkflowTag(workflowId, tag);
      setWorkflow(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove tag");
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading workflow..." />;
  }

  if (!workflow) {
    return (
      <div>
        {error && <ErrorBanner message={error} onRetry={load} />}
        <button onClick={onBack} style={linkStyle(palette.textSecondary)}>
          Back to list
        </button>
      </div>
    );
  }

  const tabs = ["tasks", "executions", "history"] as const;

  return (
    <div data-testid="workflow-detail">
      <button
        onClick={onBack}
        data-testid="back-button"
        style={linkStyle(palette.textSecondary)}
      >
        Back to list
      </button>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} onRetry={load} />}

      <div
        style={{
          background: palette.surface,
          borderRadius: "12px",
          padding: "20px",
          marginTop: "12px",
          marginBottom: "16px",
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
                fontWeight: 700,
                color: palette.textPrimary,
                marginBottom: "4px",
              }}
            >
              {workflow.name}
            </h2>
            {workflow.description && (
              <p style={{ fontSize: "14px", color: palette.textSecondary }}>
                {workflow.description}
              </p>
            )}
            <div
              style={{
                fontSize: "12px",
                color: palette.textMuted,
                marginTop: "8px",
              }}
            >
              Created: {new Date(workflow.created_at).toLocaleString()} | Updated:{" "}
              {new Date(workflow.updated_at).toLocaleString()}
            </div>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={handleExecute}
              data-testid="execute-button"
              style={actionBtn("#059669")}
            >
              Run
            </button>
            <button
              onClick={handleDryRun}
              data-testid="dry-run-button"
              style={actionBtn("#7c3aed")}
            >
              Dry Run
            </button>
            <button
              onClick={handleClone}
              data-testid="clone-button"
              style={actionBtn("#2563eb")}
            >
              Clone
            </button>
          </div>
        </div>

        {/* Tags */}
        <div style={{ marginTop: "12px" }}>
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", alignItems: "center" }}>
            {workflow.tags.map((tag) => (
              <span
                key={tag}
                style={{
                  padding: "2px 8px",
                  borderRadius: "4px",
                  background: palette.surfaceHover,
                  color: palette.textSecondary,
                  fontSize: "12px",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  data-testid={`remove-tag-${tag}`}
                  style={{
                    border: "none",
                    background: "transparent",
                    color: palette.textMuted,
                    cursor: "pointer",
                    fontSize: "14px",
                    padding: 0,
                    lineHeight: 1,
                  }}
                >
                  x
                </button>
              </span>
            ))}
            <div style={{ display: "flex", gap: "4px" }}>
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    void handleAddTag();
                  }
                }}
                placeholder="Add tag..."
                data-testid="tag-input"
                style={{
                  padding: "2px 8px",
                  borderRadius: "4px",
                  border: `1px solid ${palette.border}`,
                  background: "transparent",
                  color: palette.textPrimary,
                  fontSize: "12px",
                  width: "100px",
                  outline: "none",
                }}
              />
              <button
                onClick={() => void handleAddTag()}
                data-testid="add-tag-button"
                style={{
                  padding: "2px 8px",
                  borderRadius: "4px",
                  border: "none",
                  background: palette.primary,
                  color: "#fff",
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                +
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            data-testid={`tab-${tab}`}
            style={{
              padding: "6px 16px",
              borderRadius: "6px",
              border: "none",
              cursor: "pointer",
              background: activeTab === tab ? palette.primary : "transparent",
              color: activeTab === tab ? "#fff" : palette.textSecondary,
              fontWeight: activeTab === tab ? 600 : 400,
              fontSize: "14px",
              textTransform: "capitalize",
            }}
          >
            {tab}
            {tab === "executions" && ` (${executions.length})`}
            {tab === "tasks" && ` (${workflow.tasks.length})`}
            {tab === "history" && ` (${history.length})`}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "tasks" && (
        <div
          style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}
          data-testid="tasks-panel"
        >
          {workflow.tasks.length === 0 ? (
            <div style={{ color: palette.textMuted, fontSize: "14px" }}>
              No tasks defined.
            </div>
          ) : (
            workflow.tasks.map((task) => <TaskCard key={task.id} task={task} />)
          )}
        </div>
      )}

      {activeTab === "executions" && (
        <ExecutionLog executions={executions} />
      )}

      {activeTab === "history" && (
        <div data-testid="history-panel">
          {history.length === 0 ? (
            <div style={{ color: palette.textMuted, fontSize: "14px" }}>
              No version history.
            </div>
          ) : (
            history.map((entry, idx) => (
              <div
                key={idx}
                style={{
                  background: palette.surface,
                  borderRadius: "8px",
                  padding: "12px 16px",
                  marginBottom: "8px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span
                    style={{
                      fontSize: "14px",
                      fontWeight: 600,
                      color: palette.textPrimary,
                    }}
                  >
                    Version {String(entry.version ?? idx + 1)}
                  </span>
                  <span
                    style={{ fontSize: "12px", color: palette.textMuted }}
                  >
                    {entry.snapshot_at
                      ? new Date(String(entry.snapshot_at)).toLocaleString()
                      : "—"}
                  </span>
                </div>
                {"name" in entry && entry.name != null && (
                  <div
                    style={{
                      fontSize: "13px",
                      color: palette.textSecondary,
                      marginTop: "4px",
                    }}
                  >
                    {String(entry.name)}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function linkStyle(color: string): React.CSSProperties {
  return {
    background: "transparent",
    border: "none",
    color,
    cursor: "pointer",
    fontSize: "14px",
    padding: 0,
  };
}

function actionBtn(bg: string): React.CSSProperties {
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
