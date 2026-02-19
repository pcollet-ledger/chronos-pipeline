import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useExecutionPolling } from "../hooks/useExecutionPolling";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  getExecution: vi.fn(),
}));

const completedExec = {
  id: "exec-1",
  workflow_id: "wf-1",
  status: "completed" as const,
  started_at: "2026-01-01T00:00:00Z",
  completed_at: "2026-01-01T00:01:00Z",
  cancelled_at: null,
  task_results: [],
  trigger: "manual",
  metadata: {},
};

describe("useExecutionPolling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not poll when executionId is null", () => {
    renderHook(() => useExecutionPolling({ executionId: null }));
    expect(api.getExecution).not.toHaveBeenCalled();
  });

  it("does not poll when enabled is false", () => {
    renderHook(() =>
      useExecutionPolling({ executionId: "exec-1", enabled: false }),
    );
    expect(api.getExecution).not.toHaveBeenCalled();
  });

  it("fetches immediately when given an executionId", async () => {
    vi.mocked(api.getExecution).mockResolvedValue(completedExec);
    renderHook(() => useExecutionPolling({ executionId: "exec-1" }));
    await waitFor(() => {
      expect(api.getExecution).toHaveBeenCalledWith("exec-1");
    });
  });

  it("sets execution data after fetch", async () => {
    vi.mocked(api.getExecution).mockResolvedValue(completedExec);
    const { result } = renderHook(() =>
      useExecutionPolling({ executionId: "exec-1" }),
    );
    await waitFor(() => {
      expect(result.current.execution).toEqual(completedExec);
    });
  });

  it("sets error on fetch failure", async () => {
    vi.mocked(api.getExecution).mockRejectedValue(new Error("Not found"));
    const { result } = renderHook(() =>
      useExecutionPolling({ executionId: "exec-1" }),
    );
    await waitFor(() => {
      expect(result.current.error).toBe("Not found");
    });
  });

  it("starts with null execution", () => {
    vi.mocked(api.getExecution).mockResolvedValue(completedExec);
    const { result } = renderHook(() =>
      useExecutionPolling({ executionId: "exec-1" }),
    );
    expect(result.current.execution).toBeNull();
  });

  it("starts with null error", () => {
    vi.mocked(api.getExecution).mockResolvedValue(completedExec);
    const { result } = renderHook(() =>
      useExecutionPolling({ executionId: "exec-1" }),
    );
    expect(result.current.error).toBeNull();
  });

  it("provides a stop function", () => {
    vi.mocked(api.getExecution).mockResolvedValue(completedExec);
    const { result } = renderHook(() =>
      useExecutionPolling({ executionId: "exec-1" }),
    );
    expect(typeof result.current.stop).toBe("function");
  });

  it("handles non-Error exceptions", async () => {
    vi.mocked(api.getExecution).mockRejectedValue("string error");
    const { result } = renderHook(() =>
      useExecutionPolling({ executionId: "exec-1" }),
    );
    await waitFor(() => {
      expect(result.current.error).toBe("Polling failed");
    });
  });

  it("stops polling after terminal status (only calls once for completed)", async () => {
    vi.mocked(api.getExecution).mockResolvedValue(completedExec);
    renderHook(() =>
      useExecutionPolling({ executionId: "exec-1", intervalMs: 100 }),
    );
    await waitFor(() => {
      expect(api.getExecution).toHaveBeenCalledTimes(1);
    });
    await new Promise((r) => setTimeout(r, 300));
    expect(api.getExecution).toHaveBeenCalledTimes(1);
  });
});
