import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider } from "../ThemeContext";
import ThemeToggle from "../components/ThemeToggle";

function renderWithTheme() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>,
  );
}

describe("ThemeToggle", () => {
  it("renders the toggle button", () => {
    renderWithTheme();
    expect(screen.getByTestId("theme-toggle")).toBeDefined();
  });

  it("shows 'Light' label in dark mode by default", () => {
    renderWithTheme();
    expect(screen.getByText("Light")).toBeDefined();
  });

  it("has correct aria-label in dark mode", () => {
    renderWithTheme();
    expect(screen.getByLabelText("Switch to light mode")).toBeDefined();
  });

  it("toggles to light mode on click", () => {
    renderWithTheme();
    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(screen.getByText("Dark")).toBeDefined();
  });

  it("has correct aria-label after toggling to light mode", () => {
    renderWithTheme();
    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(screen.getByLabelText("Switch to dark mode")).toBeDefined();
  });

  it("toggles back to dark mode on double click", () => {
    renderWithTheme();
    fireEvent.click(screen.getByTestId("theme-toggle"));
    fireEvent.click(screen.getByTestId("theme-toggle"));
    expect(screen.getByText("Light")).toBeDefined();
  });

  it("renders as a button element", () => {
    renderWithTheme();
    const btn = screen.getByTestId("theme-toggle");
    expect(btn.tagName).toBe("BUTTON");
  });

  it("is clickable", () => {
    renderWithTheme();
    const btn = screen.getByTestId("theme-toggle");
    expect(btn.style.cursor).toBe("pointer");
  });

  it("has transparent background", () => {
    renderWithTheme();
    const btn = screen.getByTestId("theme-toggle");
    expect(btn.style.background).toBe("transparent");
  });

  it("has border styling", () => {
    renderWithTheme();
    const btn = screen.getByTestId("theme-toggle");
    expect(btn.style.borderRadius).toBe("6px");
  });
});
