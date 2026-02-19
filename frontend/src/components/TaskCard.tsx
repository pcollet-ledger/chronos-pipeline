import type { TaskDefinition } from "../types";
import {
  colors,
  fontSizes,
  fontWeights,
  priorityColors,
  radii,
  spacing,
} from "../styles/theme";

interface Props {
  task: TaskDefinition;
}

export default function TaskCard({ task }: Props) {
  return (
    <div
      style={{
        background: colors.neutral[900],
        borderRadius: radii.lg,
        padding: `10px ${spacing.lg}`,
        borderLeft: `3px solid ${priorityColors[task.priority] || colors.neutral[500]}`,
        minWidth: "180px",
      }}
    >
      <div
        style={{
          fontSize: fontSizes.md,
          fontWeight: fontWeights.semibold,
          color: colors.neutral[200],
        }}
      >
        {task.name}
      </div>
      <div
        style={{
          fontSize: fontSizes.xs,
          color: colors.neutral[500],
          marginTop: spacing.xs,
        }}
      >
        Action: <span style={{ color: colors.neutral[400] }}>{task.action}</span>
      </div>
      <div
        style={{
          fontSize: fontSizes.xs,
          color: colors.neutral[500],
          marginTop: "2px",
        }}
      >
        Priority:{" "}
        <span
          style={{
            color: priorityColors[task.priority],
            textTransform: "capitalize",
          }}
        >
          {task.priority}
        </span>
      </div>
      {task.depends_on.length > 0 && (
        <div
          style={{
            fontSize: fontSizes.xs,
            color: colors.neutral[500],
            marginTop: "2px",
          }}
        >
          Deps: {task.depends_on.length}
        </div>
      )}
      {task.pre_hook && (
        <div
          style={{
            fontSize: fontSizes.xs,
            color: colors.neutral[500],
            marginTop: "2px",
          }}
        >
          Pre-hook: <span style={{ color: colors.neutral[400] }}>{task.pre_hook}</span>
        </div>
      )}
      {task.post_hook && (
        <div
          style={{
            fontSize: fontSizes.xs,
            color: colors.neutral[500],
            marginTop: "2px",
          }}
        >
          Post-hook:{" "}
          <span style={{ color: colors.neutral[400] }}>{task.post_hook}</span>
        </div>
      )}
    </div>
  );
}
