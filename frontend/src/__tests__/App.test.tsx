import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import App from "../App";
import { ThemeProvider } from "../context/ThemeContext";

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
    localStorage.clear();
  });

  it("renders the header with Chronos Pipeline title", async () => {
    renderApp();
    await waitFor(() =>
      expect(screen.getByText("Chronos Pipeline")).toBeDefined(),
    );
  });

  it("renders navigation buttons", async () => {
    renderApp();
    await waitFor(() =>
      expect(screen.getByText("dashboard")).toBeDefined(),
    );
    expect(screen.getByText("workflows")).toBeDefined();
  });

  it("renders refresh button", async () => {
    renderApp();
    await waitFor(() =>
      expect(screen.getByText("Refresh")).toBeDefined(),
    );
  });

  it("renders theme toggle button", async () => {
    renderApp();
    await waitFor(() =>
      expect(screen.getByTestId("theme-toggle")).toBeDefined(),
    );
  });
});
