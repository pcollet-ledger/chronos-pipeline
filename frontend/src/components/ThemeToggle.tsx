import { useTheme } from "../context/ThemeContext";

export default function ThemeToggle() {
  const { mode, toggle, colors } = useTheme();

  return (
    <button
      onClick={toggle}
      aria-label={`Switch to ${mode === "dark" ? "light" : "dark"} mode`}
      style={{
        padding: "6px 12px",
        borderRadius: "6px",
        border: `1px solid ${colors.border}`,
        background: "transparent",
        color: colors.textMuted,
        cursor: "pointer",
        fontSize: "13px",
        display: "flex",
        alignItems: "center",
        gap: "6px",
      }}
    >
      <span>{mode === "dark" ? "\u2600" : "\u263E"}</span>
      <span>{mode === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}
