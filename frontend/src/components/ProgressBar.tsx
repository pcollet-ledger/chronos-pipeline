import { useMemo } from "react";
import { getStatusColor } from "../theme";

interface ProgressBarProps {
  completed: number;
  total: number;
  status?: string;
  height?: number;
}

export default function ProgressBar({
  completed,
  total,
  status = "running",
  height = 8,
}: ProgressBarProps) {
  const pct = useMemo(
    () => (total > 0 ? Math.round((completed / total) * 100) : 0),
    [completed, total],
  );
  const color = getStatusColor(status);

  return (
    <div
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`${pct}% complete`}
      style={{
        width: "100%",
        height,
        backgroundColor: "#e5e7eb",
        borderRadius: height / 2,
        overflow: "hidden",
      }}
    >
      <div
        data-testid="progress-fill"
        style={{
          width: `${pct}%`,
          height: "100%",
          backgroundColor: color,
          borderRadius: height / 2,
          transition: "width 0.3s ease",
        }}
      />
    </div>
  );
}
