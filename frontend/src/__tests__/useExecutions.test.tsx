import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { useExecutions } from "../hooks/useExecutions";
import type { WorkflowExecution } from "../types";

const mockExecution: WorkflowExecution = {
  id: "exec-1",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:01:00Z",
  cancelled_at: null,
  task_results: [],
  trigger: "manual",
  metadata: {},
};

const mockListExecutions = vi.fn();

vi.mock("../services/api", () => ({
  listExecutions: (...args: unknown[]) => mockListExecutions(...args),
}));

function TestComponent({
  workflowId,
  status,
}: {
  workflowId?: string;
  status?: string;
}) {
  const { data, loading, error, refetch } = useExecutions({
    workflowId,
    status,
  });
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="error">{error ?? "none"}</span>
      <span data-testid="count">{data.length}</span>
      <span data-testid="ids">{data.map((e) => e.id).join(",")}</span>
      <button data-testid="refetch" onClick={refetch}>
        Refetch
      </button>
    </div>
  );
}

describe("useExecutions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListExecutions.mockResolvedValue([mockExecution]);
  });

  it("starts in loading state", () => {
    render(<TestComponent />);
    expect(screen.getByTestId("loading").textContent).toBe("true");
  });

  it("loads executions on mount", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(screen.getByTestId("count").textContent).toBe("1");
  });

  it("returns execution IDs", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("ids").textContent).toBe("exec-1"),
    );
  });

  it("passes params to API", async () => {
    render(<TestComponent workflowId="wf-1" status="completed" />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(mockListExecutions).toHaveBeenCalledWith({
      workflowId: "wf-1",
      status: "completed",
    });
  });

  it("handles API error", async () => {
    mockListExecutions.mockRejectedValue(new Error("Timeout"));
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe("Timeout"),
    );
  });

  it("handles non-Error rejection", async () => {
    mockListExecutions.mockRejectedValue(null);
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe(
        "Failed to load executions",
      ),
    );
  });

  it("returns empty array initially", () => {
    mockListExecutions.mockImplementation(() => new Promise(() => {}));
    render(<TestComponent />);
    expect(screen.getByTestId("count").textContent).toBe("0");
  });

  it("refetch reloads data", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    await act(async () => {
      screen.getByTestId("refetch").click();
    });
    await waitFor(() =>
      expect(mockListExecutions).toHaveBeenCalledTimes(2),
    );
  });

  it("clears error on successful refetch", async () => {
    mockListExecutions.mockRejectedValueOnce(new Error("fail"));
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe("fail"),
    );
    mockListExecutions.mockResolvedValueOnce([mockExecution]);
    await act(async () => {
      screen.getByTestId("refetch").click();
    });
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe("none"),
    );
  });

  it("passes empty params when none provided", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(mockListExecutions).toHaveBeenCalledWith({
      workflowId: undefined,
      status: undefined,
    });
  });
});
