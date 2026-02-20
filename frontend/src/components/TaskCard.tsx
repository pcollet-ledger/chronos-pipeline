import type { TaskDefinition } from "../types";
import { useTheme } from "../contexts/ThemeContext";
import {
  spacing,
  fontSize,
  fontWeight,
  radii,
  getPriorityColor,
} from "../theme";

interface Props {
  task: TaskDefinition;
}

export default function TaskCard({ task }: Props) {
  const { theme } = useTheme();

  return (
    <div
      style={{
        background: theme.surfaceAlt,
        borderRadius: radii.lg,
        padding: `10px ${spacing.lg}`,
        borderLeft: `3px solid ${getPriorityColor(task.priority)}`,
        minWidth: "180px",
      }}
    >
      <div style={{ fontSize: fontSize.md, fontWeight: fontWeight.semibold, color: theme.text }}>
        {task.name}
      </div>
      <div style={{ fontSize: fontSize.xs, color: theme.textMuted, marginTop: spacing.xs }}>
        Action: <span style={{ color: theme.textSecondary }}>{task.action}</span>
      </div>
      <div style={{ fontSize: fontSize.xs, color: theme.textMuted, marginTop: "2px" }}>
        Priority:{" "}
        <span style={{ color: getPriorityColor(task.priority), textTransform: "capitalize" }}>
          {task.priority}
        </span>
      </div>
      {task.depends_on.length > 0 && (
        <div style={{ fontSize: fontSize.xs, color: theme.textMuted, marginTop: "2px" }}>
          Deps: {task.depends_on.length}
        </div>
      )}
      {task.pre_hook && (
        <div style={{ fontSize: fontSize.xs, color: theme.textMuted, marginTop: "2px" }}>
          Pre-hook: <span style={{ color: theme.textSecondary }}>{task.pre_hook}</span>
        </div>
      )}
      {task.post_hook && (
        <div style={{ fontSize: fontSize.xs, color: theme.textMuted, marginTop: "2px" }}>
          Post-hook: <span style={{ color: theme.textSecondary }}>{task.post_hook}</span>
        </div>
      )}
    </div>
  );
}
