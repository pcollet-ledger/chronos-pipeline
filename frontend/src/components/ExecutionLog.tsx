import { useTheme } from "../ThemeContext";
import { statusColor } from "../theme";
import type { WorkflowExecution } from "../types";
import ProgressBar from "./ProgressBar";

interface Props {
  execution: WorkflowExecution;
  onClose?: () => void;
}

export default function ExecutionLog({ execution, onClose }: Props) {
  const { theme } = useTheme();

  const total = execution.task_results.length;
  const completed = execution.task_results.filter(
    (t) => t.status === "completed",
  ).length;
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div
      data-testid="execution-log"
      style={{
        background: theme.bgCard,
        borderRadius: "12px",
        padding: "20px",
        border: `1px solid ${theme.border}`,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
        }}
      >
        <div>
          <h3 style={{ fontSize: "16px", color: theme.textPrimary, margin: 0 }}>
            Execution{" "}
            <span style={{ fontFamily: "monospace", fontSize: "14px" }}>
              {execution.id.slice(0, 8)}
            </span>
          </h3>
          <div style={{ fontSize: "12px", color: theme.textMuted, marginTop: "4px" }}>
            Trigger: {execution.trigger} &middot; Status:{" "}
            <span
              style={{
                color: statusColor(theme, execution.status),
                fontWeight: 600,
                textTransform: "capitalize",
              }}
            >
              {execution.status}
            </span>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            aria-label="Close execution log"
            style={{
              padding: "4px 10px",
              borderRadius: "4px",
              border: `1px solid ${theme.borderSubtle}`,
              background: "transparent",
              color: theme.textSecondary,
              cursor: "pointer",
              fontSize: "14px",
            }}
          >
            Close
          </button>
        )}
      </div>

      <ProgressBar percent={percent} label={`${completed}/${total} tasks completed`} />

      <div style={{ marginTop: "16px" }}>
        {execution.task_results.length === 0 ? (
          <div style={{ color: theme.textMuted, fontSize: "14px" }}>
            No task results
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${theme.borderSubtle}` }}>
                <th style={thStyle(theme.textMuted)}>Task</th>
                <th style={thStyle(theme.textMuted)}>Status</th>
                <th style={thStyle(theme.textMuted)}>Duration</th>
                <th style={thStyle(theme.textMuted)}>Error</th>
              </tr>
            </thead>
            <tbody>
              {execution.task_results.map((tr) => (
                <tr
                  key={tr.task_id}
                  style={{ borderBottom: `1px solid ${theme.border}` }}
                >
                  <td style={tdStyle(theme.textPrimary)}>
                    <span style={{ fontFamily: "monospace", fontSize: "13px" }}>
                      {tr.task_id.slice(0, 8)}
                    </span>
                  </td>
                  <td style={tdStyle(statusColor(theme, tr.status))}>
                    <span style={{ fontWeight: 600, textTransform: "capitalize" }}>
                      {tr.status}
                    </span>
                  </td>
                  <td style={tdStyle(theme.textSecondary)}>
                    {tr.duration_ms !== null ? `${tr.duration_ms}ms` : "—"}
                  </td>
                  <td style={tdStyle(theme.error)}>
                    {tr.error ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function thStyle(color: string): React.CSSProperties {
  return {
    textAlign: "left",
    padding: "8px 12px",
    fontSize: "11px",
    color,
    fontWeight: 600,
    textTransform: "uppercase",
  };
}

function tdStyle(color: string): React.CSSProperties {
  return {
    padding: "8px 12px",
    fontSize: "13px",
    color,
  };
}
