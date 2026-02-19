import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  ThemeProvider,
  useTheme,
  lightPalette,
  darkPalette,
} from "../context/ThemeContext";

function TestConsumer() {
  const { mode, palette, toggle } = useTheme();
  return (
    <div>
      <span data-testid="mode">{mode}</span>
      <span data-testid="bg">{palette.background}</span>
      <span data-testid="text">{palette.textPrimary}</span>
      <button data-testid="toggle" onClick={toggle}>
        Toggle
      </button>
    </div>
  );
}

describe("ThemeContext", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("defaults to dark mode when no localStorage value", () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("provides dark palette by default", () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("bg").textContent).toBe(darkPalette.background);
  });

  it("toggles to light mode on click", () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("mode").textContent).toBe("light");
  });

  it("provides light palette after toggle", () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("bg").textContent).toBe(lightPalette.background);
  });

  it("toggles back to dark mode on double click", () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("persists mode to localStorage", () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(localStorage.getItem("chronos-theme-mode")).toBe("light");
  });

  it("reads mode from localStorage on mount", () => {
    localStorage.setItem("chronos-theme-mode", "light");
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("light");
  });

  it("reads dark from localStorage on mount", () => {
    localStorage.setItem("chronos-theme-mode", "dark");
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("ignores invalid localStorage value", () => {
    localStorage.setItem("chronos-theme-mode", "invalid");
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    // Falls back to system preference or dark
    const mode = screen.getByTestId("mode").textContent;
    expect(mode === "dark" || mode === "light").toBe(true);
  });

  it("provides correct textPrimary for dark mode", () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("text").textContent).toBe(darkPalette.textPrimary);
  });

  it("provides correct textPrimary for light mode", () => {
    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("text").textContent).toBe(lightPalette.textPrimary);
  });

  it("light and dark palettes have different backgrounds", () => {
    expect(lightPalette.background).not.toBe(darkPalette.background);
  });

  it("light and dark palettes have different surface colors", () => {
    expect(lightPalette.surface).not.toBe(darkPalette.surface);
  });
});
