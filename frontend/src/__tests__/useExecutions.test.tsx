import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useExecutions, useWorkflowExecutions, useExecution } from "../hooks/useExecutions";

const mockExecution = {
  id: "ex-1",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2026-01-01T00:00:00Z",
  completed_at: "2026-01-01T00:01:00Z",
  cancelled_at: null,
  task_results: [],
  trigger: "manual",
  metadata: {},
};

vi.mock("../services/api", () => ({
  listExecutions: vi.fn(),
  listWorkflowExecutions: vi.fn(),
  getExecution: vi.fn(),
}));

describe("useExecutions", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const api = await import("../services/api");
    (api.listExecutions as ReturnType<typeof vi.fn>).mockResolvedValue([mockExecution]);
    (api.listWorkflowExecutions as ReturnType<typeof vi.fn>).mockResolvedValue([mockExecution]);
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue(mockExecution);
  });

  it("starts in loading state", () => {
    const { result } = renderHook(() => useExecutions());
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toEqual([]);
  });

  it("loads executions", async () => {
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual([mockExecution]);
  });

  it("handles errors", async () => {
    const api = await import("../services/api");
    (api.listExecutions as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error("Fail"));

    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBe("Fail");
  });
});

describe("useWorkflowExecutions", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const api = await import("../services/api");
    (api.listWorkflowExecutions as ReturnType<typeof vi.fn>).mockResolvedValue([mockExecution]);
  });

  it("loads executions for a workflow", async () => {
    const { result } = renderHook(() => useWorkflowExecutions("wf-1"));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual([mockExecution]);
  });
});

describe("useExecution", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const api = await import("../services/api");
    (api.getExecution as ReturnType<typeof vi.fn>).mockResolvedValue(mockExecution);
  });

  it("loads a single execution", async () => {
    const { result } = renderHook(() => useExecution("ex-1"));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual(mockExecution);
  });

  it("handles errors", async () => {
    const api = await import("../services/api");
    (api.getExecution as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error("Not found"));

    const { result } = renderHook(() => useExecution("ex-bad"));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBe("Not found");
    expect(result.current.data).toBeNull();
  });
});
