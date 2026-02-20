import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import App from "../App";
import { ThemeProvider } from "../contexts/ThemeContext";
import * as api from "../services/api";

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
  getWorkflow: vi.fn(),
  listWorkflowExecutions: vi.fn(),
  executeWorkflow: vi.fn(),
  cloneWorkflow: vi.fn(),
  dryRunWorkflow: vi.fn(),
  createWorkflow: vi.fn(),
  deleteWorkflow: vi.fn(),
}));

const mockedApi = vi.mocked(api);

async function renderApp() {
  const result = render(
    <ThemeProvider>
      <App />
    </ThemeProvider>,
  );
  await waitFor(() => {
    expect(screen.getByText("Chronos Pipeline")).toBeDefined();
  });
  return result;
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedApi.listWorkflows.mockResolvedValue([]);
    mockedApi.getAnalyticsSummary.mockResolvedValue({
      total_workflows: 0,
      total_executions: 0,
      success_rate: 0,
      avg_duration_ms: 0,
      executions_by_status: {},
      recent_executions: [],
      top_failing_workflows: [],
    });
  });

  it("renders the header with Chronos Pipeline title", async () => {
    await renderApp();
    expect(screen.getByText("Chronos Pipeline")).toBeDefined();
  });

  it("renders navigation buttons", async () => {
    await renderApp();
    expect(screen.getByText("dashboard")).toBeDefined();
    expect(screen.getByText("workflows")).toBeDefined();
  });

  it("renders refresh button", async () => {
    await renderApp();
    expect(screen.getByText("Refresh")).toBeDefined();
  });

  it("renders theme toggle button", async () => {
    await renderApp();
    expect(screen.getByTestId("theme-toggle")).toBeDefined();
  });

  it("toggles theme when clicking the theme button", async () => {
    await renderApp();
    const btn = screen.getByTestId("theme-toggle");
    const initialText = btn.textContent;
    fireEvent.click(btn);
    expect(btn.textContent).not.toBe(initialText);
  });

  it("shows dashboard view by default", async () => {
    await renderApp();
    expect(screen.getByText("Dashboard")).toBeDefined();
  });

  it("switches to workflows view when clicking workflows nav", async () => {
    await renderApp();
    fireEvent.click(screen.getByText("workflows"));
    await waitFor(() => {
      expect(screen.getByText("Pipelines")).toBeDefined();
    });
  });

  it("switches back to dashboard from workflows", async () => {
    await renderApp();
    fireEvent.click(screen.getByText("workflows"));
    await waitFor(() => {
      expect(screen.getByText("Pipelines")).toBeDefined();
    });
    fireEvent.click(screen.getByText("dashboard"));
    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeDefined();
    });
  });

  it("calls listWorkflows and getAnalyticsSummary on mount", async () => {
    await renderApp();
    expect(mockedApi.listWorkflows).toHaveBeenCalledTimes(1);
    expect(mockedApi.getAnalyticsSummary).toHaveBeenCalledTimes(1);
  });

  it("calls refresh when clicking Refresh button", async () => {
    await renderApp();
    mockedApi.listWorkflows.mockResolvedValue([]);
    mockedApi.getAnalyticsSummary.mockResolvedValue({
      total_workflows: 1,
      total_executions: 5,
      success_rate: 80,
      avg_duration_ms: 100,
      executions_by_status: { completed: 4, failed: 1 },
      recent_executions: [],
      top_failing_workflows: [],
    });
    await act(async () => {
      fireEvent.click(screen.getByText("Refresh"));
    });
    await waitFor(() => {
      expect(mockedApi.listWorkflows).toHaveBeenCalledTimes(2);
    });
  });

  it("shows error banner when API call fails", async () => {
    mockedApi.listWorkflows.mockRejectedValueOnce(new Error("Network failure"));
    const { container } = render(
      <ThemeProvider>
        <App />
      </ThemeProvider>,
    );
    await waitFor(() => {
      expect(container.textContent).toContain("Network failure");
    });
  });

  it("dismisses error banner when clicking dismiss", async () => {
    mockedApi.listWorkflows.mockRejectedValueOnce(new Error("Temporary error"));
    render(
      <ThemeProvider>
        <App />
      </ThemeProvider>,
    );
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeDefined();
    });
    const dismissBtn = screen.getByLabelText("Dismiss error");
    fireEvent.click(dismissBtn);
    await waitFor(() => {
      expect(screen.queryByRole("alert")).toBeNull();
    });
  });
});
