import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ThemeToggle from "../components/ThemeToggle";
import { ThemeProvider } from "../context/ThemeContext";

function renderWithTheme() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>,
  );
}

describe("ThemeToggle", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("renders the toggle button", () => {
    renderWithTheme();
    expect(screen.getByTestId("theme-toggle")).toBeDefined();
  });

  it("shows 'Light' in dark mode (default)", () => {
    renderWithTheme();
    expect(screen.getByText("Light")).toBeDefined();
  });

  it("toggles to light mode on click", () => {
    renderWithTheme();
    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(screen.getByText("Dark")).toBeDefined();
  });

  it("has correct aria-label", () => {
    renderWithTheme();
    const btn = screen.getByTestId("theme-toggle");
    expect(btn.getAttribute("aria-label")).toBe("Switch to light mode");
  });

  it("updates aria-label after toggle", () => {
    renderWithTheme();
    const btn = screen.getByTestId("theme-toggle");
    fireEvent.click(btn);
    expect(btn.getAttribute("aria-label")).toBe("Switch to dark mode");
  });

  it("persists theme choice in localStorage", () => {
    renderWithTheme();
    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(localStorage.getItem("chronos-theme")).toBe("light");
  });
});
