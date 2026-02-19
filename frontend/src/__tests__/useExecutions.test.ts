import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useExecutions } from "../hooks/useExecutions";
import type { WorkflowExecution } from "../types";

const mockExecution: WorkflowExecution = {
  id: "e1",
  workflow_id: "w1",
  status: "completed",
  trigger: "manual",
  task_results: [],
  started_at: "2025-01-01T00:00:00Z",
  completed_at: "2025-01-01T00:01:00Z",
  cancelled_at: null,
  metadata: {},
};

const mockApi = {
  listExecutions: vi.fn(),
  getExecution: vi.fn(),
  retryExecution: vi.fn(),
  cancelExecution: vi.fn(),
  compareExecutions: vi.fn(),
};

vi.mock("../services/api", () => ({
  listExecutions: (...args: unknown[]) => mockApi.listExecutions(...args),
  getExecution: (...args: unknown[]) => mockApi.getExecution(...args),
  retryExecution: (...args: unknown[]) => mockApi.retryExecution(...args),
  cancelExecution: (...args: unknown[]) => mockApi.cancelExecution(...args),
  compareExecutions: (...args: unknown[]) => mockApi.compareExecutions(...args),
}));

describe("useExecutions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.listExecutions.mockResolvedValue([mockExecution]);
  });

  it("fetches executions on mount", async () => {
    const { result } = renderHook(() => useExecutions());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual([mockExecution]);
    expect(result.current.error).toBeNull();
  });

  it("passes filter options to API", async () => {
    const { result } = renderHook(() =>
      useExecutions({ workflowId: "w1", status: "completed", limit: 10, offset: 0 }),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockApi.listExecutions).toHaveBeenCalledWith("w1", "completed", 10, 0);
  });

  it("handles fetch error", async () => {
    mockApi.listExecutions.mockRejectedValue(new Error("Connection lost"));

    const { result } = renderHook(() => useExecutions());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Connection lost");
  });

  it("getExecution delegates to API", async () => {
    mockApi.getExecution.mockResolvedValue(mockExecution);

    const { result } = renderHook(() => useExecutions());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const exec = await result.current.getExecution("e1");
    expect(exec).toEqual(mockExecution);
    expect(mockApi.getExecution).toHaveBeenCalledWith("e1");
  });

  it("retryExecution calls API and refetches", async () => {
    const retried = { ...mockExecution, status: "running" as const };
    mockApi.retryExecution.mockResolvedValue(retried);

    const { result } = renderHook(() => useExecutions());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    let retryResult: WorkflowExecution | undefined;
    await act(async () => {
      retryResult = await result.current.retryExecution("e1");
    });

    expect(retryResult?.status).toBe("running");
    expect(mockApi.listExecutions).toHaveBeenCalledTimes(2);
  });

  it("cancelExecution calls API and refetches", async () => {
    const cancelled = { ...mockExecution, status: "cancelled" as const };
    mockApi.cancelExecution.mockResolvedValue(cancelled);

    const { result } = renderHook(() => useExecutions());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    let cancelResult: WorkflowExecution | undefined;
    await act(async () => {
      cancelResult = await result.current.cancelExecution("e1");
    });

    expect(cancelResult?.status).toBe("cancelled");
    expect(mockApi.listExecutions).toHaveBeenCalledTimes(2);
  });

  it("compareExecutions delegates to API", async () => {
    const comparison = {
      workflow_id: "w1",
      executions: [mockExecution, mockExecution],
      task_comparison: [],
      summary: { improved_count: 0, regressed_count: 0, unchanged_count: 0 },
    };
    mockApi.compareExecutions.mockResolvedValue(comparison);

    const { result } = renderHook(() => useExecutions());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const cmp = await result.current.compareExecutions("e1", "e2");
    expect(cmp.workflow_id).toBe("w1");
    expect(mockApi.compareExecutions).toHaveBeenCalledWith("e1", "e2");
  });
});
