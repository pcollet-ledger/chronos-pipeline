import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useExecutionPolling } from "../hooks/useExecutionPolling";
import type { WorkflowExecution, WorkflowStatus } from "../types";

const makeExecution = (
  status: WorkflowStatus,
  overrides: Partial<WorkflowExecution> = {},
): WorkflowExecution => ({
  id: "e1",
  workflow_id: "w1",
  status,
  trigger: "manual",
  task_results: [],
  started_at: "2025-01-01T00:00:00Z",
  completed_at: null,
  cancelled_at: null,
  metadata: {},
  ...overrides,
});

const mockApi = {
  getExecution: vi.fn(),
};

vi.mock("../services/api", () => ({
  getExecution: (...args: unknown[]) => mockApi.getExecution(...args),
}));

describe("useExecutionPolling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("does not poll when executionId is null", () => {
    const { result } = renderHook(() => useExecutionPolling(null));

    expect(result.current.execution).toBeNull();
    expect(result.current.isPolling).toBe(false);
    expect(mockApi.getExecution).not.toHaveBeenCalled();
  });

  it("fetches execution immediately on mount", async () => {
    mockApi.getExecution.mockResolvedValue(makeExecution("running"));

    const { result } = renderHook(() => useExecutionPolling("e1", 5000));

    await waitFor(() => {
      expect(result.current.execution).not.toBeNull();
    });

    expect(result.current.execution?.status).toBe("running");
    expect(mockApi.getExecution).toHaveBeenCalledWith("e1");
  });

  it("stops polling on terminal status (completed)", async () => {
    mockApi.getExecution.mockResolvedValue(makeExecution("completed"));

    const { result } = renderHook(() => useExecutionPolling("e1", 5000));

    await waitFor(() => {
      expect(result.current.execution?.status).toBe("completed");
    });

    expect(result.current.isPolling).toBe(false);
  });

  it("stops polling on error", async () => {
    mockApi.getExecution.mockRejectedValue(new Error("Not found"));

    const { result } = renderHook(() => useExecutionPolling("e1", 5000));

    await waitFor(() => {
      expect(result.current.error).toBe("Not found");
    });

    expect(result.current.isPolling).toBe(false);
  });

  it("stop() halts polling", async () => {
    mockApi.getExecution.mockResolvedValue(makeExecution("running"));

    const { result } = renderHook(() => useExecutionPolling("e1", 5000));

    await waitFor(() => {
      expect(result.current.execution?.status).toBe("running");
    });

    act(() => {
      result.current.stop();
    });

    expect(result.current.isPolling).toBe(false);
  });

  it("recognizes failed as terminal status", async () => {
    mockApi.getExecution.mockResolvedValue(makeExecution("failed"));

    const { result } = renderHook(() => useExecutionPolling("e1", 5000));

    await waitFor(() => {
      expect(result.current.execution?.status).toBe("failed");
    });

    expect(result.current.isPolling).toBe(false);
  });

  it("recognizes cancelled as terminal status", async () => {
    mockApi.getExecution.mockResolvedValue(makeExecution("cancelled"));

    const { result } = renderHook(() => useExecutionPolling("e1", 5000));

    await waitFor(() => {
      expect(result.current.execution?.status).toBe("cancelled");
    });

    expect(result.current.isPolling).toBe(false);
  });
});
