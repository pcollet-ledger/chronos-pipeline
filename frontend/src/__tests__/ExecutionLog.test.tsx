import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import ExecutionLog from "../components/ExecutionLog";
import type { WorkflowExecution } from "../types";

const mockExecution: WorkflowExecution = {
  id: "exec-abc",
  workflow_id: "wf-1",
  status: "failed",
  started_at: "2025-01-01T00:00:00Z",
  completed_at: "2025-01-01T00:01:00Z",
  cancelled_at: null,
  task_results: [
    {
      task_id: "t1",
      status: "completed",
      started_at: "2025-01-01T00:00:00Z",
      completed_at: "2025-01-01T00:00:30Z",
      output: { rows: 42 },
      error: null,
      duration_ms: 500,
    },
    {
      task_id: "t2",
      status: "failed",
      started_at: "2025-01-01T00:00:30Z",
      completed_at: "2025-01-01T00:01:00Z",
      output: null,
      error: "Timeout exceeded",
      duration_ms: 30000,
    },
    {
      task_id: "t3",
      status: "running",
      started_at: "2025-01-01T00:01:00Z",
      completed_at: null,
      output: null,
      error: null,
      duration_ms: null,
    },
  ],
  trigger: "manual",
  metadata: {},
};

vi.mock("../services/api", () => ({
  getExecution: vi.fn(),
  retryExecution: vi.fn(),
}));

import * as api from "../services/api";

describe("ExecutionLog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue(mockExecution);
  });

  it("renders execution log container", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByTestId("execution-log")).toBeDefined();
    });
  });

  it("renders all task result rows", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      const rows = screen.getAllByTestId("task-result-row");
      expect(rows.length).toBe(3);
    });
  });

  it("displays task IDs for each step", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("t1")).toBeDefined();
      expect(screen.getByText("t2")).toBeDefined();
      expect(screen.getByText("t3")).toBeDefined();
    });
  });

  it("shows correct status icons", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      const icons = screen.getAllByTestId("status-icon");
      expect(icons.length).toBe(3);
      expect(icons[0]!.textContent).toBe("\u2713");
      expect(icons[1]!.textContent).toBe("\u2717");
      expect(icons[2]!.textContent).toBe("\u23F3");
    });
  });

  it("shows human-readable duration", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("500ms")).toBeDefined();
      expect(screen.getByText("30.0s")).toBeDefined();
      expect(screen.getByText("\u2014")).toBeDefined();
    });
  });

  it("shows error message visible by default for failed tasks", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByTestId("error-message")).toBeDefined();
      expect(screen.getByText("Timeout exceeded")).toBeDefined();
    });
  });

  it("expands and collapses task details", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getAllByTestId("toggle-details").length).toBeGreaterThan(0);
    });

    const toggleButtons = screen.getAllByTestId("toggle-details");
    const completedToggle = toggleButtons[0]!;

    expect(completedToggle.textContent).toBe("Show details");

    const detailsBefore = screen.queryAllByTestId("task-details");
    const countBefore = detailsBefore.length;

    fireEvent.click(completedToggle);
    const detailsAfter = screen.getAllByTestId("task-details");
    expect(detailsAfter.length).toBe(countBefore + 1);
    expect(screen.getByText(/42/)).toBeDefined();
    expect(completedToggle.textContent).toBe("Hide details");

    fireEvent.click(completedToggle);
    const detailsFinal = screen.queryAllByTestId("task-details");
    expect(detailsFinal.length).toBe(countBefore);
  });

  it("failed task details are expanded by default", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      const toggleButtons = screen.getAllByTestId("toggle-details");
      const failedToggle = toggleButtons[1]!;
      expect(failedToggle.textContent).toBe("Hide details");
    });
  });

  it("shows retry button for failed executions", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByTestId("retry-button")).toBeDefined();
      expect(screen.getByText("Retry")).toBeDefined();
    });
  });

  it("retry button calls the retry API", async () => {
    const retriedExecution: WorkflowExecution = {
      ...mockExecution,
      id: "exec-retry",
      status: "running",
      task_results: [],
    };
    (api.retryExecution as ReturnType<typeof vi.fn>).mockResolvedValue(retriedExecution);

    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByTestId("retry-button")).toBeDefined();
    });

    fireEvent.click(screen.getByTestId("retry-button"));
    await waitFor(() => {
      expect(api.retryExecution).toHaveBeenCalledWith("exec-abc");
    });
  });

  it("does not show retry button for completed executions", async () => {
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue({
      ...mockExecution,
      status: "completed",
    });
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByTestId("execution-log")).toBeDefined();
    });
    expect(screen.queryByTestId("retry-button")).toBeNull();
  });

  it("handles empty task list", async () => {
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue({
      ...mockExecution,
      task_results: [],
    });
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("No task results recorded")).toBeDefined();
    });
    expect(screen.queryByTestId("task-result-row")).toBeNull();
  });

  it("displays execution metadata", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("Execution Log")).toBeDefined();
      expect(screen.getByText("exec-abc")).toBeDefined();
      expect(screen.getByText("wf-1")).toBeDefined();
      expect(screen.getByText(/manual/)).toBeDefined();
    });
  });

  it("displays execution status badge", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      const badges = screen.getAllByText("failed");
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows error banner when API fails", async () => {
    (api.getExecution as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Not found"),
    );
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("Not found")).toBeDefined();
    });
  });

  it("calls getExecution with the correct ID", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(api.getExecution).toHaveBeenCalledWith("exec-abc");
    });
  });

  it("shows loading spinner initially", () => {
    (api.getExecution as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}));
    render(<ExecutionLog executionId="exec-abc" />);
    expect(screen.getByTestId("spinner")).toBeDefined();
  });

  it("shows retrying state on retry button", async () => {
    (api.retryExecution as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}));
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByTestId("retry-button")).toBeDefined();
    });

    fireEvent.click(screen.getByTestId("retry-button"));
    await waitFor(() => {
      expect(screen.getByText("Retrying\u2026")).toBeDefined();
    });
  });

  it("shows error when retry fails", async () => {
    (api.retryExecution as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Retry failed"),
    );
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByTestId("retry-button")).toBeDefined();
    });

    fireEvent.click(screen.getByTestId("retry-button"));
    await waitFor(() => {
      expect(screen.getByText("Retry failed")).toBeDefined();
    });
  });

  it("renders vertical timeline connector between steps", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByTestId("timeline")).toBeDefined();
    });
  });
});
