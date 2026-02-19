import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider, useTheme } from "../contexts/ThemeContext";
import { lightTheme, darkTheme } from "../theme";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

function ThemeConsumer() {
  const { mode, theme, toggleTheme, setMode } = useTheme();
  return (
    <div>
      <span data-testid="mode">{mode}</span>
      <span data-testid="bg">{theme.bg}</span>
      <button data-testid="toggle" onClick={toggleTheme}>toggle</button>
      <button data-testid="set-dark" onClick={() => setMode("dark")}>dark</button>
      <button data-testid="set-light" onClick={() => setMode("light")}>light</button>
    </div>
  );
}

describe("ThemeContext", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("provides light theme by default", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("light");
    expect(screen.getByTestId("bg").textContent).toBe(lightTheme.bg);
  });

  it("toggles from light to dark", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("mode").textContent).toBe("dark");
    expect(screen.getByTestId("bg").textContent).toBe(darkTheme.bg);
  });

  it("toggles back from dark to light", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("toggle"));
    fireEvent.click(screen.getByTestId("toggle"));
    expect(screen.getByTestId("mode").textContent).toBe("light");
  });

  it("setMode sets dark explicitly", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("set-dark"));
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("setMode sets light explicitly", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("set-dark"));
    fireEvent.click(screen.getByTestId("set-light"));
    expect(screen.getByTestId("mode").textContent).toBe("light");
  });

  it("persists mode to localStorage", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("set-dark"));
    expect(localStorage.getItem("chronos-theme")).toBe("dark");
  });

  it("reads stored mode from localStorage", () => {
    localStorage.setItem("chronos-theme", "dark");
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("dark");
  });

  it("sets data-theme attribute on document", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    fireEvent.click(screen.getByTestId("toggle"));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("throws when useTheme is used outside ThemeProvider", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<ThemeConsumer />)).toThrow(
      "useTheme must be used within a ThemeProvider",
    );
    spy.mockRestore();
  });

  it("provides correct dark theme tokens", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByTestId("set-dark"));
    expect(screen.getByTestId("bg").textContent).toBe(darkTheme.bg);
  });

  it("provides correct light theme tokens", () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("bg").textContent).toBe(lightTheme.bg);
  });

  it("ignores invalid localStorage values", () => {
    localStorage.setItem("chronos-theme", "invalid");
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId("mode").textContent).toBe("light");
  });
});
