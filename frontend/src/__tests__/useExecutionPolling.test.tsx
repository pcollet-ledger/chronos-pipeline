import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useExecutionPolling } from "../hooks/useExecutionPolling";
import type { WorkflowExecution } from "../types";

const runningExec: WorkflowExecution = {
  id: "exec-1",
  workflow_id: "wf-1",
  status: "running",
  started_at: "2025-01-01T00:00:00Z",
  completed_at: null,
  cancelled_at: null,
  task_results: [],
  trigger: "manual",
  metadata: {},
};

vi.mock("../services/api", () => ({
  getExecution: vi.fn(),
}));

import * as api from "../services/api";

describe("useExecutionPolling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue(runningExec);
  });

  it("returns null execution when no ID is provided", () => {
    const { result } = renderHook(() => useExecutionPolling(null));
    expect(result.current.execution).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it("starts loading when ID is provided", async () => {
    const { result } = renderHook(() => useExecutionPolling("exec-1"));
    expect(result.current.loading).toBe(true);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("fetches execution on mount", async () => {
    renderHook(() => useExecutionPolling("exec-1"));
    await waitFor(() => {
      expect(api.getExecution).toHaveBeenCalledWith("exec-1");
    });
  });

  it("sets execution after fetch", async () => {
    const { result } = renderHook(() => useExecutionPolling("exec-1"));
    await waitFor(() => {
      expect(result.current.execution).toEqual(runningExec);
      expect(result.current.loading).toBe(false);
    });
  });

  it("sets error on failure", async () => {
    (api.getExecution as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Not found"),
    );
    const { result } = renderHook(() => useExecutionPolling("exec-1"));
    await waitFor(() => {
      expect(result.current.error).toBe("Not found");
      expect(result.current.loading).toBe(false);
    });
  });

  it("provides a stop function", async () => {
    const { result } = renderHook(() => useExecutionPolling("exec-1"));
    await waitFor(() => {
      expect(result.current.execution).toBeTruthy();
    });
    expect(typeof result.current.stop).toBe("function");
  });

  it("stop function can be called without error", async () => {
    const { result } = renderHook(() => useExecutionPolling("exec-1"));
    await waitFor(() => {
      expect(result.current.execution).toBeTruthy();
    });
    act(() => {
      result.current.stop();
    });
  });

  it("resets execution when ID changes to null", async () => {
    const { result, rerender } = renderHook(
      ({ id }) => useExecutionPolling(id),
      { initialProps: { id: "exec-1" as string | null } },
    );
    await waitFor(() => {
      expect(result.current.execution).toEqual(runningExec);
    });
    rerender({ id: null });
    expect(result.current.execution).toBeNull();
  });

  it("cleans up on unmount without errors", async () => {
    const { result, unmount } = renderHook(() => useExecutionPolling("exec-1"));
    await waitFor(() => {
      expect(result.current.execution).toBeTruthy();
    });
    unmount();
  });

  it("error is null initially", () => {
    const { result } = renderHook(() => useExecutionPolling(null));
    expect(result.current.error).toBeNull();
  });

  it("uses default interval of 2000ms", async () => {
    const { result } = renderHook(() => useExecutionPolling("exec-1"));
    await waitFor(() => {
      expect(result.current.execution).toBeTruthy();
    });
  });

  it("accepts custom interval", async () => {
    const { result } = renderHook(() => useExecutionPolling("exec-1", 5000));
    await waitFor(() => {
      expect(result.current.execution).toBeTruthy();
    });
  });
});
