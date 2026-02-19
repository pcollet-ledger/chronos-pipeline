import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import App from "../App";
import { ThemeProvider } from "../contexts/ThemeContext";

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

vi.mock("../services/api", () => ({
  listWorkflows: vi.fn().mockResolvedValue([]),
  getAnalyticsSummary: vi.fn().mockResolvedValue({
    total_workflows: 0,
    total_executions: 0,
    success_rate: 0,
    avg_duration_ms: 0,
    executions_by_status: {},
    recent_executions: [],
    top_failing_workflows: [],
  }),
}));

function renderApp() {
  return render(
    <ThemeProvider>
      <App />
    </ThemeProvider>,
  );
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the header with Chronos Pipeline title", () => {
    renderApp();
    expect(screen.getByText("Chronos Pipeline")).toBeDefined();
  });

  it("renders navigation buttons", () => {
    renderApp();
    expect(screen.getByText("dashboard")).toBeDefined();
    expect(screen.getByText("workflows")).toBeDefined();
  });

  it("renders refresh button", () => {
    renderApp();
    expect(screen.getByText("Refresh")).toBeDefined();
  });

  it("renders theme toggle button", () => {
    renderApp();
    expect(screen.getByTestId("theme-toggle")).toBeDefined();
  });

  it("toggles theme when clicking the theme button", () => {
    renderApp();
    const btn = screen.getByTestId("theme-toggle");
    const initialText = btn.textContent;
    fireEvent.click(btn);
    expect(btn.textContent).not.toBe(initialText);
  });
});
