import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import ExecutionLogViewer from "../components/ExecutionLogViewer";
import { ThemeProvider } from "../context/ThemeContext";

const mockExecution = {
  id: "ex-789",
  workflow_id: "wf-123",
  status: "failed",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:01:00Z",
  cancelled_at: null,
  task_results: [
    {
      task_id: "t1",
      status: "completed",
      started_at: "2026-01-15T10:00:00Z",
      completed_at: "2026-01-15T10:00:30Z",
      output: { result: "ok" },
      error: null,
      duration_ms: 30000,
    },
    {
      task_id: "t2",
      status: "failed",
      started_at: "2026-01-15T10:00:30Z",
      completed_at: "2026-01-15T10:01:00Z",
      output: null,
      error: "Connection timeout",
      duration_ms: 30000,
    },
  ],
  trigger: "manual",
  metadata: { run_by: "admin" },
};

vi.mock("../services/api", () => ({
  getExecution: vi.fn(),
  retryExecution: vi.fn(),
  cancelExecution: vi.fn(),
}));

function renderViewer(props?: Partial<React.ComponentProps<typeof ExecutionLogViewer>>) {
  const defaultProps = {
    executionId: "ex-789",
    onBack: vi.fn(),
  };
  return render(
    <ThemeProvider>
      <ExecutionLogViewer {...defaultProps} {...props} />
    </ThemeProvider>,
  );
}

describe("ExecutionLogViewer", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    localStorage.clear();
    const api = await import("../services/api");
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue(mockExecution);
    (api.retryExecution as ReturnType<typeof vi.fn>).mockResolvedValue({ ...mockExecution, status: "completed" });
    (api.cancelExecution as ReturnType<typeof vi.fn>).mockResolvedValue({ ...mockExecution, status: "cancelled" });
  });

  it("renders execution ID after loading", async () => {
    renderViewer();
    await waitFor(() => {
      expect(screen.getByText("ex-789...")).toBeDefined();
    });
  });

  it("renders status", async () => {
    renderViewer();
    await waitFor(() => {
      const failedElements = screen.getAllByText("failed");
      expect(failedElements.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("renders trigger type", async () => {
    renderViewer();
    await waitFor(() => {
      expect(screen.getByText("manual")).toBeDefined();
    });
  });

  it("renders task results count", async () => {
    renderViewer();
    await waitFor(() => {
      expect(screen.getByText("Task Results (2)")).toBeDefined();
    });
  });

  it("renders error message for failed task", async () => {
    renderViewer();
    await waitFor(() => {
      expect(screen.getByText("Connection timeout")).toBeDefined();
    });
  });

  it("renders retry button for failed execution", async () => {
    renderViewer();
    await waitFor(() => {
      expect(screen.getByText("Retry")).toBeDefined();
    });
  });

  it("renders metadata section", async () => {
    renderViewer();
    await waitFor(() => {
      expect(screen.getByText("Metadata")).toBeDefined();
    });
  });

  it("renders back button", async () => {
    renderViewer();
    await waitFor(() => {
      expect(screen.getByTestId("back-button")).toBeDefined();
    });
  });

  it("renders duration", async () => {
    renderViewer();
    await waitFor(() => {
      expect(screen.getByText("1.0m")).toBeDefined();
    });
  });
});
