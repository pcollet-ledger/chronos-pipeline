import { useTheme } from "../context/ThemeContext";

export default function ThemeToggle() {
  const { mode, toggleTheme, theme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label={`Switch to ${mode === "dark" ? "light" : "dark"} mode`}
      data-testid="theme-toggle"
      style={{
        padding: "6px 12px",
        borderRadius: theme.borderRadius.md,
        border: `1px solid ${theme.palette.border}`,
        background: "transparent",
        color: theme.palette.textSecondary,
        cursor: "pointer",
        fontSize: theme.fontSize.sm,
        display: "flex",
        alignItems: "center",
        gap: "6px",
        transition: `all ${theme.transitions.fast}`,
      }}
    >
      <span aria-hidden="true">{mode === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}
