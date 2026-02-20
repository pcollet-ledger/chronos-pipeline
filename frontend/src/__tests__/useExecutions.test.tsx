import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useExecutions } from "../hooks/useExecutions";
import type { WorkflowExecution } from "../types";

const mockExecutions: WorkflowExecution[] = [
  {
    id: "exec-1",
    workflow_id: "wf-1",
    status: "completed",
    started_at: "2025-01-01T00:00:00Z",
    completed_at: "2025-01-01T00:01:00Z",
    cancelled_at: null,
    task_results: [],
    trigger: "manual",
    metadata: {},
  },
];

vi.mock("../services/api", () => ({
  listExecutions: vi.fn(),
}));

import * as api from "../services/api";

describe("useExecutions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.listExecutions as ReturnType<typeof vi.fn>).mockResolvedValue(mockExecutions);
  });

  it("starts with loading true", async () => {
    const { result } = renderHook(() => useExecutions());
    expect(result.current.loading).toBe(true);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("loads executions", async () => {
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.executions).toEqual(mockExecutions);
    expect(result.current.error).toBeNull();
  });

  it("sets error on failure", async () => {
    (api.listExecutions as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Server error"),
    );
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBe("Server error");
  });

  it("passes status filter to API", async () => {
    const { result } = renderHook(() => useExecutions("failed"));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(api.listExecutions).toHaveBeenCalledWith("failed");
  });

  it("calls API without status when not provided", async () => {
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(api.listExecutions).toHaveBeenCalledWith(undefined);
  });

  it("refresh reloads data", async () => {
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    (api.listExecutions as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    await act(async () => {
      result.current.refresh();
    });
    await waitFor(() => {
      expect(result.current.executions).toEqual([]);
    });
  });

  it("re-fetches when status changes", async () => {
    const { result, rerender } = renderHook(
      ({ status }) => useExecutions(status),
      { initialProps: { status: "running" as string | undefined } },
    );
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    rerender({ status: "completed" });
    await waitFor(() => {
      expect(api.listExecutions).toHaveBeenCalledWith("completed");
    });
  });

  it("provides a refresh function", async () => {
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(typeof result.current.refresh).toBe("function");
  });

  it("clears error on successful refresh", async () => {
    (api.listExecutions as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("fail"),
    );
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.error).toBe("fail");
    });
    (api.listExecutions as ReturnType<typeof vi.fn>).mockResolvedValue(mockExecutions);
    await act(async () => {
      result.current.refresh();
    });
    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
  });

  it("returns empty array initially", async () => {
    const { result } = renderHook(() => useExecutions());
    expect(result.current.executions).toEqual([]);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });
});
