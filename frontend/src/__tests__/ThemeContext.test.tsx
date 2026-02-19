import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider, useTheme } from "../context/ThemeContext";

function ThemeDisplay() {
  const { mode, palette, toggle } = useTheme();
  return (
    <div>
      <span data-testid="mode">{mode}</span>
      <span data-testid="bg">{palette.background}</span>
      <button data-testid="toggle" onClick={toggle}>
        Toggle
      </button>
    </div>
  );
}

describe("ThemeContext", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("provides dark mode by default", () => {
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("provides dark palette background by default", () => {
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("bg").textContent).toBe("#0f172a");
  });

  it("toggles to light mode", () => {
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("mode").textContent).toBe("light");
  });

  it("toggles back to dark mode", () => {
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("light mode has light background", () => {
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("bg").textContent).toBe("#f8fafc");
  });

  it("persists mode to localStorage", () => {
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(localStorage.getItem("chronos-theme")).toBe("light");
  });

  it("reads stored mode from localStorage", () => {
    localStorage.setItem("chronos-theme", "light");
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("light");
  });

  it("ignores invalid stored mode", () => {
    localStorage.setItem("chronos-theme", "invalid");
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("useTheme outside provider returns defaults", () => {
    function Standalone() {
      const { mode } = useTheme();
      return <span data-testid="standalone">{mode}</span>;
    }
    render(<Standalone />);
    expect(screen.getByTestId("standalone").textContent).toBe("dark");
  });

  it("multiple toggles cycle correctly", () => {
    render(
      <ThemeProvider>
        <ThemeDisplay />
      </ThemeProvider>,
    );
    const btn = screen.getByTestId("toggle");
    for (let i = 0; i < 5; i++) {
      fireEvent.click(btn);
    }
    expect(screen.getByTestId("mode").textContent).toBe("light");
  });
});
