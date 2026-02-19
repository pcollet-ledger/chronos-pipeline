import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useExecutionPolling } from "../hooks/useExecutionPolling";

const runningExecution = {
  id: "ex-poll",
  workflow_id: "wf-1",
  status: "running" as const,
  started_at: "2026-01-01T00:00:00Z",
  completed_at: null,
  cancelled_at: null,
  task_results: [],
  trigger: "manual",
  metadata: {},
};

const completedExecution = {
  ...runningExecution,
  status: "completed" as const,
  completed_at: "2026-01-01T00:01:00Z",
};

vi.mock("../services/api", () => ({
  getExecution: vi.fn(),
}));

describe("useExecutionPolling", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const api = await import("../services/api");
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue(runningExecution);
  });

  it("starts not polling", () => {
    const { result } = renderHook(() => useExecutionPolling("ex-poll"));
    expect(result.current.isPolling).toBe(false);
    expect(result.current.data).toBeNull();
  });

  it("provides a loading state", () => {
    const { result } = renderHook(() => useExecutionPolling("ex-poll"));
    expect(result.current.loading).toBe(true);
  });

  it("fetches data when polling starts", async () => {
    const { result } = renderHook(() => useExecutionPolling("ex-poll", 5000));

    act(() => {
      result.current.startPolling();
    });

    await waitFor(() => {
      expect(result.current.data).toEqual(runningExecution);
    });
  });

  it("stops polling on terminal status", async () => {
    const api = await import("../services/api");
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue(completedExecution);

    const { result } = renderHook(() => useExecutionPolling("ex-poll", 5000));

    act(() => {
      result.current.startPolling();
    });

    await waitFor(() => {
      expect(result.current.isPolling).toBe(false);
      expect(result.current.data?.status).toBe("completed");
    });
  });

  it("can be manually stopped", async () => {
    const { result } = renderHook(() => useExecutionPolling("ex-poll", 5000));

    act(() => {
      result.current.startPolling();
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    act(() => {
      result.current.stopPolling();
    });

    expect(result.current.isPolling).toBe(false);
  });

  it("exposes startPolling and stopPolling functions", () => {
    const { result } = renderHook(() => useExecutionPolling("ex-poll"));
    expect(typeof result.current.startPolling).toBe("function");
    expect(typeof result.current.stopPolling).toBe("function");
  });

  it("handles fetch errors gracefully", async () => {
    const api = await import("../services/api");
    (api.getExecution as ReturnType<typeof vi.fn>).mockRejectedValue(new Error("Network fail"));

    const { result } = renderHook(() => useExecutionPolling("ex-poll", 5000));

    act(() => {
      result.current.startPolling();
    });

    await waitFor(() => {
      expect(result.current.error).toBe("Network fail");
    });
  });
});
