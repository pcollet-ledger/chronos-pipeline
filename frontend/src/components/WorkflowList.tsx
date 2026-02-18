import { useState } from "react";
import type { Workflow, WorkflowExecution } from "../types";
import { createWorkflow, deleteWorkflow, executeWorkflow } from "../services/api";
import TaskCard from "./TaskCard";

interface Props {
  workflows: Workflow[];
  onRefresh: () => void;
}

export default function WorkflowList({ workflows, onRefresh }: Props) {
  const [newName, setNewName] = useState("");
  const [executionResult, setExecutionResult] = useState<WorkflowExecution | null>(null);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    await createWorkflow({ name: newName.trim(), description: "Auto-created pipeline" });
    setNewName("");
    onRefresh();
  };

  const handleExecute = async (id: string) => {
    const result = await executeWorkflow(id);
    setExecutionResult(result);
    onRefresh();
  };

  const handleDelete = async (id: string) => {
    await deleteWorkflow(id);
    onRefresh();
  };

  return (
    <div>
      <h2 style={{ fontSize: "18px", marginBottom: "20px", color: "#e2e8f0" }}>
        Pipelines
      </h2>

      {/* Create form */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "24px" }}>
        <input
          type="text"
          placeholder="New pipeline name..."
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: "8px",
            border: "1px solid #334155",
            background: "#1e293b",
            color: "#e2e8f0",
            fontSize: "14px",
            outline: "none",
          }}
        />
        <button
          onClick={handleCreate}
          style={{
            padding: "10px 20px",
            borderRadius: "8px",
            border: "none",
            background: "#2563eb",
            color: "#fff",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "14px",
          }}
        >
          Create
        </button>
      </div>

      {/* Pipeline list */}
      {workflows.length === 0 ? (
        <div style={{ color: "#475569", textAlign: "center", padding: "40px" }}>
          No pipelines yet. Create one above.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {workflows.map((wf) => (
            <div
              key={wf.id}
              style={{
                background: "#1e293b",
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
                  <h3 style={{ fontSize: "16px", color: "#e2e8f0", fontWeight: 600 }}>
                    {wf.name}
                  </h3>
                  {wf.description && (
                    <p style={{ fontSize: "13px", color: "#64748b", marginTop: "4px" }}>
                      {wf.description}
                    </p>
                  )}
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button onClick={() => handleExecute(wf.id)} style={btnStyle("#059669")}>
                    Run
                  </button>
                  <button onClick={() => handleDelete(wf.id)} style={btnStyle("#dc2626")}>
                    Delete
                  </button>
                </div>
              </div>

              {/* Tags */}
              {wf.tags.length > 0 && (
                <div style={{ display: "flex", gap: "6px", marginBottom: "8px" }}>
                  {wf.tags.map((tag) => (
                    <span
                      key={tag}
                      style={{
                        padding: "2px 8px",
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

              {/* Tasks */}
              {wf.tasks.length > 0 && (
                <div style={{ marginTop: "12px" }}>
                  <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "8px" }}>
                    {wf.tasks.length} task{wf.tasks.length !== 1 ? "s" : ""}
                  </div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
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
            bottom: "20px",
            right: "20px",
            background: executionResult.status === "completed" ? "#064e3b" : "#7f1d1d",
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
          <div style={{ fontSize: "12px", marginTop: "4px", opacity: 0.8 }}>
            {executionResult.task_results.length} tasks completed · Click to dismiss
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
