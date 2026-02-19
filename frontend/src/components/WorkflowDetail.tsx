import { useCallback, useEffect, useState } from "react";
import type { Workflow, WorkflowExecution } from "../types";
import {
  addWorkflowTags,
  cloneWorkflow,
  deleteWorkflow,
  dryRunWorkflow,
  executeWorkflow,
  getWorkflow,
  getWorkflowHistory,
  listWorkflowExecutions,
  removeWorkflowTag,
  updateWorkflow,
} from "../services/api";
import { useTheme } from "../context/ThemeContext";
import TaskCard from "./TaskCard";
import ErrorBanner from "./ErrorBanner";
import LoadingSpinner from "./LoadingSpinner";

interface Props {
  workflowId: string;
  onBack: () => void;
  onRefresh: () => void;
}

export default function WorkflowDetail({ workflowId, onBack, onRefresh }: Props) {
  const { theme } = useTheme();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [history, setHistory] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tagInput, setTagInput] = useState("");
  const [showHistory, setShowHistory] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [wf, execs] = await Promise.all([
        getWorkflow(workflowId),
        listWorkflowExecutions(workflowId, 10),
      ]);
      setWorkflow(wf);
      setExecutions(execs);
      setEditName(wf.name);
      setEditDescription(wf.description);
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
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
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

  const handleClone = async () => {
    try {
      setError(null);
      await cloneWorkflow(workflowId);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clone failed");
    }
  };

  const handleDelete = async () => {
    try {
      setError(null);
      await deleteWorkflow(workflowId);
      onRefresh();
      onBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
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

  const handleLoadHistory = async () => {
    try {
      setError(null);
      const hist = await getWorkflowHistory(workflowId);
      setHistory(hist);
      setShowHistory(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    }
  };

  const handleSaveEdit = async () => {
    try {
      setError(null);
      const updated = await updateWorkflow(workflowId, {
        name: editName.trim(),
        description: editDescription.trim(),
      });
      setWorkflow(updated);
      setEditing(false);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update");
    }
  };

  if (loading) return <LoadingSpinner label="Loading workflow..." />;
  if (!workflow) return <ErrorBanner message="Workflow not found" />;

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

  const inputStyle: React.CSSProperties = {
    padding: "8px 12px",
    borderRadius: theme.borderRadius.md,
    border: `1px solid ${p.border}`,
    background: p.surface,
    color: p.text,
    fontSize: theme.fontSize.base,
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
  };

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
        Back to list
      </button>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      <div
        style={{
          background: p.surface,
          borderRadius: theme.borderRadius.lg,
          padding: theme.spacing.lg,
          marginBottom: theme.spacing.md,
        }}
      >
        {editing ? (
          <div style={{ marginBottom: theme.spacing.md }}>
            <input
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              style={{ ...inputStyle, marginBottom: theme.spacing.sm }}
              data-testid="edit-name-input"
            />
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              rows={3}
              style={{ ...inputStyle, resize: "vertical" }}
              data-testid="edit-description-input"
            />
            <div style={{ display: "flex", gap: theme.spacing.sm, marginTop: theme.spacing.sm }}>
              <button onClick={handleSaveEdit} style={{ ...btnBase, background: theme.colors.primary }}>
                Save
              </button>
              <button
                onClick={() => {
                  setEditing(false);
                  setEditName(workflow.name);
                  setEditDescription(workflow.description);
                }}
                style={{ ...btnBase, background: p.surfaceHover, color: p.textSecondary }}
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h2 style={{ fontSize: theme.fontSize.xxl, color: p.text, fontWeight: theme.fontWeight.bold }}>
                {workflow.name}
              </h2>
              {workflow.description && (
                <p style={{ fontSize: theme.fontSize.base, color: p.textSecondary, marginTop: theme.spacing.xs }}>
                  {workflow.description}
                </p>
              )}
              <div style={{ fontSize: theme.fontSize.sm, color: p.textMuted, marginTop: theme.spacing.sm }}>
                Version {workflow.version} · Created {new Date(workflow.created_at).toLocaleDateString()}
              </div>
            </div>
            <div style={{ display: "flex", gap: theme.spacing.sm, flexShrink: 0 }}>
              <button onClick={() => setEditing(true)} style={{ ...btnBase, background: theme.colors.primary }}>
                Edit
              </button>
              <button onClick={handleExecute} style={{ ...btnBase, background: theme.colors.success }}>
                Run
              </button>
              <button onClick={handleDryRun} style={{ ...btnBase, background: theme.colors.info }}>
                Dry Run
              </button>
              <button onClick={handleClone} style={{ ...btnBase, background: theme.colors.secondary }}>
                Clone
              </button>
              <button onClick={handleDelete} style={{ ...btnBase, background: theme.colors.error }}>
                Delete
              </button>
            </div>
          </div>
        )}

        {/* Tags */}
        <div style={{ marginTop: theme.spacing.md }}>
          <div style={{ display: "flex", gap: theme.spacing.sm, flexWrap: "wrap", alignItems: "center" }}>
            {workflow.tags.map((tag) => (
              <span
                key={tag}
                style={{
                  padding: "2px 8px",
                  borderRadius: theme.borderRadius.sm,
                  background: p.surfaceHover,
                  color: p.textSecondary,
                  fontSize: theme.fontSize.sm,
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                {tag}
                <button
                  onClick={() => void handleRemoveTag(tag)}
                  style={{
                    border: "none",
                    background: "transparent",
                    color: theme.colors.error,
                    cursor: "pointer",
                    fontSize: "14px",
                    padding: 0,
                    lineHeight: 1,
                  }}
                  aria-label={`Remove tag ${tag}`}
                >
                  ×
                </button>
              </span>
            ))}
            <div style={{ display: "flex", gap: "4px" }}>
              <input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") void handleAddTag(); }}
                placeholder="Add tag..."
                style={{ ...inputStyle, width: "120px" }}
                data-testid="tag-input"
              />
              <button
                onClick={() => void handleAddTag()}
                style={{ ...btnBase, background: p.surfaceHover, color: p.textSecondary, fontSize: theme.fontSize.sm }}
              >
                Add
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tasks */}
      {workflow.tasks.length > 0 && (
        <div
          style={{
            background: p.surface,
            borderRadius: theme.borderRadius.lg,
            padding: theme.spacing.lg,
            marginBottom: theme.spacing.md,
          }}
        >
          <h3 style={{ fontSize: theme.fontSize.lg, color: p.text, marginBottom: theme.spacing.md }}>
            Tasks ({workflow.tasks.length})
          </h3>
          <div style={{ display: "flex", gap: theme.spacing.sm, flexWrap: "wrap" }}>
            {workflow.tasks.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        </div>
      )}

      {/* Recent Executions */}
      <div
        style={{
          background: p.surface,
          borderRadius: theme.borderRadius.lg,
          padding: theme.spacing.lg,
          marginBottom: theme.spacing.md,
        }}
      >
        <h3 style={{ fontSize: theme.fontSize.lg, color: p.text, marginBottom: theme.spacing.md }}>
          Recent Executions
        </h3>
        {executions.length === 0 ? (
          <div style={{ color: p.textMuted, fontSize: theme.fontSize.base }}>No executions yet</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${p.border}` }}>
                <th style={thStyle(p)}>ID</th>
                <th style={thStyle(p)}>Status</th>
                <th style={thStyle(p)}>Trigger</th>
                <th style={thStyle(p)}>Started</th>
                <th style={thStyle(p)}>Tasks</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((ex) => (
                <tr key={ex.id} style={{ borderBottom: `1px solid ${p.borderLight}` }}>
                  <td style={tdStyle(p)}>{ex.id.slice(0, 8)}...</td>
                  <td style={tdStyle(p)}>
                    <span style={{ color: statusColors[ex.status] ?? p.textMuted, fontWeight: 600, textTransform: "capitalize" }}>
                      {ex.status}
                    </span>
                  </td>
                  <td style={tdStyle(p)}>{ex.trigger}</td>
                  <td style={tdStyle(p)}>
                    {ex.started_at ? new Date(ex.started_at).toLocaleString() : "—"}
                  </td>
                  <td style={tdStyle(p)}>{ex.task_results.length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Version History */}
      <div
        style={{
          background: p.surface,
          borderRadius: theme.borderRadius.lg,
          padding: theme.spacing.lg,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: theme.spacing.md }}>
          <h3 style={{ fontSize: theme.fontSize.lg, color: p.text }}>Version History</h3>
          <button
            onClick={() => { showHistory ? setShowHistory(false) : void handleLoadHistory(); }}
            data-testid="toggle-history"
            style={{ ...btnBase, background: p.surfaceHover, color: p.textSecondary, fontSize: theme.fontSize.sm }}
          >
            {showHistory ? "Hide" : "Show History"}
          </button>
        </div>
        {showHistory && (
          history.length === 0 ? (
            <div style={{ color: p.textMuted, fontSize: theme.fontSize.base }}>No previous versions</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.sm }}>
              {history.map((ver) => (
                <div
                  key={`v${ver.version}`}
                  style={{
                    padding: theme.spacing.md,
                    background: p.background,
                    borderRadius: theme.borderRadius.md,
                    border: `1px solid ${p.borderLight}`,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: p.text, fontWeight: theme.fontWeight.semibold }}>
                      v{ver.version} — {ver.name}
                    </span>
                    <span style={{ color: p.textMuted, fontSize: theme.fontSize.sm }}>
                      {new Date(ver.updated_at).toLocaleString()}
                    </span>
                  </div>
                  {ver.description && (
                    <p style={{ color: p.textSecondary, fontSize: theme.fontSize.md, marginTop: theme.spacing.xs }}>
                      {ver.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}

function thStyle(p: { textMuted: string }): React.CSSProperties {
  return {
    textAlign: "left",
    padding: "8px 12px",
    fontSize: "12px",
    color: p.textMuted,
    fontWeight: 600,
    textTransform: "uppercase",
  };
}

function tdStyle(p: { text: string }): React.CSSProperties {
  return {
    padding: "10px 12px",
    fontSize: "14px",
    color: p.text,
  };
}
