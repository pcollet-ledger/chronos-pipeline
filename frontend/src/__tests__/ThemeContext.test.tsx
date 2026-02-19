import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider, useTheme, darkTheme, lightTheme } from "../contexts/ThemeContext";

function ThemeConsumer() {
  const { theme, mode, toggleTheme } = useTheme();
  return (
    <div>
      <span data-testid="mode">{mode}</span>
      <span data-testid="bg">{theme.bg}</span>
      <span data-testid="text">{theme.text}</span>
      <span data-testid="accent">{theme.accent}</span>
      <button data-testid="toggle" onClick={toggleTheme}>Toggle</button>
    </div>
  );
}

describe("ThemeContext", () => {
  it("provides dark theme by default", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("provides dark theme bg color", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("bg").textContent).toBe(darkTheme.bg);
  });

  it("provides dark theme text color", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("text").textContent).toBe(darkTheme.text);
  });

  it("provides dark theme accent color", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("accent").textContent).toBe(darkTheme.accent);
  });

  it("toggles to light theme", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("mode").textContent).toBe("light");
  });

  it("provides light theme bg after toggle", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("bg").textContent).toBe(lightTheme.bg);
  });

  it("provides light theme text after toggle", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("text").textContent).toBe(lightTheme.text);
  });

  it("toggles back to dark theme on double toggle", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("dark theme has expected bg value", () => {
    expect(darkTheme.bg).toBe("#0f172a");
  });

  it("light theme has expected bg value", () => {
    expect(lightTheme.bg).toBe("#f8fafc");
  });

  it("dark theme has all required keys", () => {
    const keys = ["bg", "bgCard", "bgInput", "border", "text", "textMuted", "textDim", "accent", "success", "error", "warning", "info"];
    for (const key of keys) {
      expect(darkTheme).toHaveProperty(key);
    }
  });

  it("light theme has all required keys", () => {
    const keys = ["bg", "bgCard", "bgInput", "border", "text", "textMuted", "textDim", "accent", "success", "error", "warning", "info"];
    for (const key of keys) {
      expect(lightTheme).toHaveProperty(key);
    }
  });

  it("useTheme outside provider returns defaults", () => {
    render(<ThemeConsumer />);
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });
});
