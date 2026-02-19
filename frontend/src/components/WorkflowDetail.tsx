import { useState } from "react";
import type { Workflow, WorkflowExecution } from "../types";
import {
  addTags,
  cloneWorkflow,
  dryRunWorkflow,
  getWorkflowHistory,
  listWorkflowExecutions,
  removeTag,
} from "../services/api";
import TaskCard from "./TaskCard";
import ErrorBanner from "./ErrorBanner";
import LoadingSpinner from "./LoadingSpinner";

interface Props {
  workflow: Workflow;
  onBack: () => void;
  onRefresh: () => void;
}

export default function WorkflowDetail({ workflow, onBack, onRefresh }: Props) {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [history, setHistory] = useState<Workflow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [tagInput, setTagInput] = useState("");
  const [activeTab, setActiveTab] = useState<"tasks" | "executions" | "history">("tasks");

  const loadExecutions = async () => {
    try {
      setLoading(true);
      const data = await listWorkflowExecutions(workflow.id);
      setExecutions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load executions");
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await getWorkflowHistory(workflow.id);
      setHistory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    if (tab === "executions") void loadExecutions();
    if (tab === "history") void loadHistory();
  };

  const handleAddTag = async () => {
    const tag = tagInput.trim();
    if (!tag) return;
    try {
      setError(null);
      await addTags(workflow.id, [tag]);
      setTagInput("");
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add tag");
    }
  };

  const handleRemoveTag = async (tag: string) => {
    try {
      setError(null);
      await removeTag(workflow.id, tag);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove tag");
    }
  };

  const handleClone = async () => {
    try {
      setError(null);
      await cloneWorkflow(workflow.id);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clone workflow");
    }
  };

  const handleDryRun = async () => {
    try {
      setError(null);
      const result = await dryRunWorkflow(workflow.id);
      setExecutions([result, ...executions]);
      setActiveTab("executions");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dry-run failed");
    }
  };

  const statusColors: Record<string, string> = {
    completed: "#22c55e",
    failed: "#ef4444",
    running: "#eab308",
    pending: "#64748b",
    cancelled: "#6b7280",
  };

  const tabs: Array<{ key: typeof activeTab; label: string }> = [
    { key: "tasks", label: `Tasks (${workflow.tasks.length})` },
    { key: "executions", label: "Executions" },
    { key: "history", label: "Version History" },
  ];

  return (
    <div>
      <button
        onClick={onBack}
        data-testid="back-button"
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

      {error && (
        <ErrorBanner message={error} onDismiss={() => setError(null)} />
      )}

      <div
        style={{
          background: "#1e293b",
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "16px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h2 style={{ fontSize: "20px", color: "#e2e8f0", fontWeight: 700 }}>
              {workflow.name}
            </h2>
            {workflow.description && (
              <p style={{ fontSize: "14px", color: "#64748b", marginTop: "4px" }}>
                {workflow.description}
              </p>
            )}
            <div style={{ fontSize: "12px", color: "#475569", marginTop: "8px" }}>
              Version {workflow.version} · Created{" "}
              {new Date(workflow.created_at).toLocaleDateString()}
            </div>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button onClick={handleDryRun} data-testid="dry-run-button" style={actionBtnStyle("#7c3aed")}>
              Dry Run
            </button>
            <button onClick={handleClone} data-testid="clone-button" style={actionBtnStyle("#0891b2")}>
              Clone
            </button>
          </div>
        </div>

        {/* Tags */}
        <div style={{ marginTop: "12px", display: "flex", gap: "6px", flexWrap: "wrap", alignItems: "center" }}>
          {workflow.tags.map((tag) => (
            <span
              key={tag}
              style={{
                padding: "2px 8px",
                borderRadius: "4px",
                background: "#334155",
                color: "#94a3b8",
                fontSize: "12px",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              {tag}
              <button
                onClick={() => void handleRemoveTag(tag)}
                data-testid={`remove-tag-${tag}`}
                style={{
                  border: "none",
                  background: "transparent",
                  color: "#ef4444",
                  cursor: "pointer",
                  fontSize: "12px",
                  padding: 0,
                  lineHeight: 1,
                }}
              >
                x
              </button>
            </span>
          ))}
          <div style={{ display: "inline-flex", gap: "4px" }}>
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") void handleAddTag(); }}
              placeholder="Add tag..."
              data-testid="tag-input"
              style={{
                padding: "2px 8px",
                borderRadius: "4px",
                border: "1px solid #334155",
                background: "#0f172a",
                color: "#e2e8f0",
                fontSize: "12px",
                width: "100px",
                outline: "none",
              }}
            />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "4px", marginBottom: "16px" }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => handleTabChange(tab.key)}
            data-testid={`tab-${tab.key}`}
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              border: "none",
              cursor: "pointer",
              background: activeTab === tab.key ? "#1e40af" : "#1e293b",
              color: activeTab === tab.key ? "#fff" : "#94a3b8",
              fontWeight: activeTab === tab.key ? 600 : 400,
              fontSize: "13px",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && <LoadingSpinner label="Loading..." />}

      {/* Tasks tab */}
      {activeTab === "tasks" && !loading && (
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {workflow.tasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}

      {/* Executions tab */}
      {activeTab === "executions" && !loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {executions.length === 0 ? (
            <div style={{ color: "#475569", fontSize: "14px", padding: "20px", textAlign: "center" }}>
              No executions yet
            </div>
          ) : (
            executions.map((ex) => (
              <div
                key={ex.id}
                data-testid={`execution-${ex.id}`}
                style={{
                  background: "#1e293b",
                  borderRadius: "8px",
                  padding: "12px 16px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <span style={{ fontSize: "13px", color: "#94a3b8" }}>
                      {ex.id.slice(0, 8)}...
                    </span>
                    <span
                      style={{
                        marginLeft: "12px",
                        color: statusColors[ex.status] ?? "#64748b",
                        fontWeight: 600,
                        fontSize: "13px",
                        textTransform: "capitalize",
                      }}
                    >
                      {ex.status}
                    </span>
                  </div>
                  <span style={{ fontSize: "12px", color: "#475569" }}>
                    {ex.trigger} · {ex.task_results.length} tasks
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* History tab */}
      {activeTab === "history" && !loading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {history.length === 0 ? (
            <div style={{ color: "#475569", fontSize: "14px", padding: "20px", textAlign: "center" }}>
              No version history
            </div>
          ) : (
            history.map((ver, idx) => (
              <div
                key={`v${ver.version}-${idx}`}
                data-testid={`version-${ver.version}`}
                style={{
                  background: "#1e293b",
                  borderRadius: "8px",
                  padding: "12px 16px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: "14px", color: "#e2e8f0", fontWeight: 600 }}>
                    v{ver.version} — {ver.name}
                  </span>
                  <span style={{ fontSize: "12px", color: "#475569" }}>
                    {ver.tasks.length} tasks
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function actionBtnStyle(bg: string): React.CSSProperties {
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
