import type { TaskDefinition } from "../types";

interface Props {
  task: TaskDefinition;
}

const priorityColors: Record<string, string> = {
  low: "#64748b",
  medium: "#3b82f6",
  high: "#f59e0b",
  critical: "#ef4444",
};

export default function TaskCard({ task }: Props) {
  return (
    <div
      style={{
        background: "#0f172a",
        borderRadius: "8px",
        padding: "10px 14px",
        borderLeft: `3px solid ${priorityColors[task.priority] || "#64748b"}`,
        minWidth: "180px",
      }}
    >
      <div style={{ fontSize: "13px", fontWeight: 600, color: "#e2e8f0" }}>
        {task.name}
      </div>
      <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
        Action: <span style={{ color: "#94a3b8" }}>{task.action}</span>
      </div>
      <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
        Priority:{" "}
        <span style={{ color: priorityColors[task.priority], textTransform: "capitalize" }}>
          {task.priority}
        </span>
      </div>
      {task.depends_on.length > 0 && (
        <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
          Deps: {task.depends_on.length}
        </div>
      )}
      {task.pre_hook && (
        <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
          Pre-hook: <span style={{ color: "#94a3b8" }}>{task.pre_hook}</span>
        </div>
      )}
      {task.post_hook && (
        <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
          Post-hook: <span style={{ color: "#94a3b8" }}>{task.post_hook}</span>
        </div>
      )}
    </div>
  );
}
