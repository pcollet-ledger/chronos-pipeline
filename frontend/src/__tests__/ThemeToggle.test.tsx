import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ThemeToggle from "../components/ThemeToggle";
import { ThemeProvider } from "../context/ThemeContext";

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock });

function renderWithTheme() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>,
  );
}

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  it("renders toggle button", () => {
    renderWithTheme();
    const btn = screen.getByRole("button");
    expect(btn).toBeDefined();
  });

  it("shows Light text in dark mode by default", () => {
    renderWithTheme();
    expect(screen.getByText("Light")).toBeDefined();
  });

  it("toggles to dark text after click", () => {
    renderWithTheme();
    const btn = screen.getByRole("button");
    fireEvent.click(btn);
    expect(screen.getByText("Dark")).toBeDefined();
  });

  it("toggles back to light text after two clicks", () => {
    renderWithTheme();
    const btn = screen.getByRole("button");
    fireEvent.click(btn);
    fireEvent.click(btn);
    expect(screen.getByText("Light")).toBeDefined();
  });

  it("has accessible label", () => {
    renderWithTheme();
    const btn = screen.getByLabelText(/switch to light mode/i);
    expect(btn).toBeDefined();
  });
});
