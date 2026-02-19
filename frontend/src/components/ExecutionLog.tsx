import { useTheme } from "../context/ThemeContext";
import type { WorkflowExecution, TaskResult } from "../types";
import LoadingSpinner from "./LoadingSpinner";

interface ExecutionLogProps {
  execution: WorkflowExecution | null;
  loading?: boolean;
}

const statusColors: Record<string, string> = {
  completed: "#22c55e",
  failed: "#ef4444",
  running: "#3b82f6",
  pending: "#94a3b8",
  cancelled: "#f59e0b",
};

function TaskResultRow({ task }: { task: TaskResult }) {
  const { colors } = useTheme();
  const statusColor = statusColors[task.status] ?? colors.textMuted;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "8px 12px",
        borderBottom: `1px solid ${colors.border}`,
        fontSize: "13px",
      }}
    >
      <span
        style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          background: statusColor,
          flexShrink: 0,
        }}
      />
      <span style={{ flex: 1, fontFamily: "monospace", color: colors.text }}>
        {task.task_id}
      </span>
      <span style={{ color: statusColor, fontWeight: 600, minWidth: "80px" }}>
        {task.status}
      </span>
      <span style={{ color: colors.textMuted, minWidth: "80px", textAlign: "right" }}>
        {task.duration_ms != null ? `${task.duration_ms}ms` : "—"}
      </span>
      {task.error && (
        <span
          style={{
            color: colors.error,
            fontSize: "12px",
            maxWidth: "200px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
          title={task.error}
        >
          {task.error}
        </span>
      )}
    </div>
  );
}

export default function ExecutionLog({ execution, loading }: ExecutionLogProps) {
  const { colors } = useTheme();

  if (loading) {
    return <LoadingSpinner size={32} />;
  }

  if (!execution) {
    return (
      <div style={{ color: colors.textMuted, padding: "16px", textAlign: "center" }}>
        No execution selected
      </div>
    );
  }

  const statusColor = statusColors[execution.status] ?? colors.textMuted;

  return (
    <div
      style={{
        background: colors.bgCard,
        borderRadius: "8px",
        border: `1px solid ${colors.border}`,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          padding: "12px 16px",
          borderBottom: `1px solid ${colors.border}`,
          display: "flex",
          alignItems: "center",
          gap: "16px",
        }}
      >
        <span style={{ fontWeight: 600, color: colors.text }}>
          Execution
        </span>
        <code style={{ fontSize: "12px", color: colors.textMuted }}>
          {execution.id}
        </code>
        <span
          style={{
            padding: "2px 8px",
            borderRadius: "4px",
            background: `${statusColor}22`,
            color: statusColor,
            fontSize: "12px",
            fontWeight: 600,
          }}
        >
          {execution.status}
        </span>
        <span style={{ color: colors.textMuted, fontSize: "12px", marginLeft: "auto" }}>
          {execution.trigger}
        </span>
      </div>

      <div style={{ padding: "4px 0" }}>
        {execution.task_results.length === 0 ? (
          <div style={{ padding: "16px", textAlign: "center", color: colors.textMuted }}>
            No task results
          </div>
        ) : (
          execution.task_results.map((task) => (
            <TaskResultRow key={task.task_id} task={task} />
          ))
        )}
      </div>

      <div
        style={{
          padding: "8px 16px",
          borderTop: `1px solid ${colors.border}`,
          display: "flex",
          gap: "16px",
          fontSize: "12px",
          color: colors.textMuted,
        }}
      >
        {execution.started_at && (
          <span>Started: {new Date(execution.started_at).toLocaleString()}</span>
        )}
        {execution.completed_at && (
          <span>Completed: {new Date(execution.completed_at).toLocaleString()}</span>
        )}
      </div>
    </div>
  );
}
