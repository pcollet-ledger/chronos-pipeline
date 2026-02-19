import { useTheme } from "../ThemeContext";

interface Props {
  /** Value between 0 and 100 */
  percent: number;
  label?: string;
  height?: number;
}

export default function ProgressBar({ percent, label, height = 8 }: Props) {
  const { theme } = useTheme();
  const clamped = Math.max(0, Math.min(100, percent));

  const barColor =
    clamped >= 90
      ? theme.success
      : clamped >= 50
        ? theme.warning
        : theme.error;

  return (
    <div data-testid="progress-bar-container">
      {label && (
        <div
          style={{
            fontSize: "12px",
            color: theme.textSecondary,
            marginBottom: "4px",
          }}
        >
          {label}
        </div>
      )}
      <div
        style={{
          width: "100%",
          height,
          borderRadius: height / 2,
          background: theme.borderSubtle,
          overflow: "hidden",
        }}
      >
        <div
          data-testid="progress-bar-fill"
          role="progressbar"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
          style={{
            width: `${clamped}%`,
            height: "100%",
            borderRadius: height / 2,
            background: barColor,
            transition: "width 0.3s ease",
          }}
        />
      </div>
    </div>
  );
}
