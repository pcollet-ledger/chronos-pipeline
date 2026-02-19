import { useTheme } from "../ThemeContext";

export default function ThemeToggle() {
  const { mode, theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      data-testid="theme-toggle"
      aria-label={`Switch to ${mode === "dark" ? "light" : "dark"} mode`}
      style={{
        padding: "6px 14px",
        borderRadius: "6px",
        border: `1px solid ${theme.borderSubtle}`,
        background: "transparent",
        color: theme.textSecondary,
        cursor: "pointer",
        fontSize: "13px",
      }}
    >
      {mode === "dark" ? "Light" : "Dark"}
    </button>
  );
}
