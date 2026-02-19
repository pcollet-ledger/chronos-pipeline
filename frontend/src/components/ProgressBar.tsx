interface Props {
  value: number;
  max?: number;
  height?: number;
  color?: string;
  bgColor?: string;
  label?: string;
  showPercent?: boolean;
}

export default function ProgressBar({
  value,
  max = 100,
  height = 8,
  color = "#22c55e",
  bgColor = "#334155",
  label,
  showPercent = false,
}: Props) {
  const clamped = Math.min(Math.max(value, 0), max);
  const pct = max > 0 ? Math.round((clamped / max) * 100) : 0;

  return (
    <div data-testid="progress-bar-container">
      {(label || showPercent) && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "12px",
            color: "#94a3b8",
            marginBottom: "4px",
          }}
        >
          {label && <span data-testid="progress-label">{label}</span>}
          {showPercent && <span data-testid="progress-percent">{pct}%</span>}
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={max}
        style={{
          width: "100%",
          height,
          background: bgColor,
          borderRadius: height / 2,
          overflow: "hidden",
        }}
      >
        <div
          data-testid="progress-fill"
          style={{
            width: `${pct}%`,
            height: "100%",
            background: color,
            borderRadius: height / 2,
            transition: "width 0.3s ease",
          }}
        />
      </div>
    </div>
  );
}
