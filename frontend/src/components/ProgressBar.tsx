import { useTheme } from "../context/ThemeContext";

interface Props {
  /** 0 to 100 */
  value: number;
  label?: string;
  color?: string;
  height?: number;
}

export default function ProgressBar({
  value,
  label,
  color,
  height = 8,
}: Props) {
  const { palette } = useTheme();
  const clamped = Math.max(0, Math.min(100, value));
  const barColor = color ?? palette.primary;

  return (
    <div data-testid="progress-bar">
      {label && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "4px",
          }}
        >
          <span style={{ fontSize: "12px", color: palette.textSecondary }}>
            {label}
          </span>
          <span style={{ fontSize: "12px", color: palette.textMuted }}>
            {Math.round(clamped)}%
          </span>
        </div>
      )}
      <div
        style={{
          width: "100%",
          height,
          borderRadius: height / 2,
          background: palette.border,
          overflow: "hidden",
        }}
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          data-testid="progress-fill"
          style={{
            width: `${clamped}%`,
            height: "100%",
            borderRadius: height / 2,
            background: barColor,
            transition: "width 300ms ease",
          }}
        />
      </div>
    </div>
  );
}
