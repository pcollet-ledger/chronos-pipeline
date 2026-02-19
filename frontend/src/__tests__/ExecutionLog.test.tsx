import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import ExecutionLog from "../components/ExecutionLog";
import type { WorkflowExecution } from "../types";

const mockExecution: WorkflowExecution = {
  id: "exec-abc",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2025-01-01T00:00:00Z",
  completed_at: "2025-01-01T00:01:00Z",
  cancelled_at: null,
  task_results: [
    {
      task_id: "t1",
      status: "completed",
      started_at: "2025-01-01T00:00:00Z",
      completed_at: "2025-01-01T00:00:30Z",
      output: null,
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
  ],
  trigger: "manual",
  metadata: {},
};

vi.mock("../services/api", () => ({
  getExecution: vi.fn(),
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

  it("displays execution status badge", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("Execution Log")).toBeDefined();
      const badges = screen.getAllByText("completed");
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("displays execution ID", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("exec-abc")).toBeDefined();
    });
  });

  it("displays workflow ID", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("wf-1")).toBeDefined();
    });
  });

  it("displays trigger type", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText(/manual/)).toBeDefined();
    });
  });

  it("renders task result rows", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      const rows = screen.getAllByTestId("task-result-row");
      expect(rows.length).toBe(2);
    });
  });

  it("shows task IDs in result rows", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("t1")).toBeDefined();
      expect(screen.getByText("t2")).toBeDefined();
    });
  });

  it("shows duration for tasks", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("500ms")).toBeDefined();
      expect(screen.getByText("30000ms")).toBeDefined();
    });
  });

  it("shows error indicator for failed tasks", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("Error")).toBeDefined();
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

  it("shows empty state when execution has no task results", async () => {
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue({
      ...mockExecution,
      task_results: [],
    });
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(screen.getByText("No task results recorded")).toBeDefined();
    });
  });

  it("calls getExecution with the correct ID", async () => {
    render(<ExecutionLog executionId="exec-abc" />);
    await waitFor(() => {
      expect(api.getExecution).toHaveBeenCalledWith("exec-abc");
    });
  });
});
