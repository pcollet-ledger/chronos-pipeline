import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useExecutions } from "../hooks/useExecutions";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  listExecutions: vi.fn(),
  listWorkflowExecutions: vi.fn(),
}));

const mockExecs = [
  {
    id: "exec-1",
    workflow_id: "wf-1",
    status: "completed" as const,
    started_at: "2026-01-01T00:00:00Z",
    completed_at: "2026-01-01T00:01:00Z",
    cancelled_at: null,
    task_results: [],
    trigger: "manual",
    metadata: {},
  },
];

describe("useExecutions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches all executions by default", async () => {
    vi.mocked(api.listExecutions).mockResolvedValue(mockExecs);
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.executions).toEqual(mockExecs);
    });
  });

  it("fetches workflow-specific executions when workflowId is set", async () => {
    vi.mocked(api.listWorkflowExecutions).mockResolvedValue(mockExecs);
    const { result } = renderHook(() =>
      useExecutions({ workflowId: "wf-1" }),
    );
    await waitFor(() => {
      expect(api.listWorkflowExecutions).toHaveBeenCalledWith("wf-1", 50);
      expect(result.current.executions).toEqual(mockExecs);
    });
  });

  it("starts with empty executions", () => {
    vi.mocked(api.listExecutions).mockResolvedValue([]);
    const { result } = renderHook(() => useExecutions());
    expect(result.current.executions).toEqual([]);
  });

  it("starts with loading true", () => {
    vi.mocked(api.listExecutions).mockResolvedValue([]);
    const { result } = renderHook(() => useExecutions());
    expect(result.current.loading).toBe(true);
  });

  it("sets loading to false after fetch", async () => {
    vi.mocked(api.listExecutions).mockResolvedValue([]);
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("sets error on failure", async () => {
    vi.mocked(api.listExecutions).mockRejectedValue(new Error("Fail"));
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.error).toBe("Fail");
    });
  });

  it("does not fetch when autoFetch is false", () => {
    vi.mocked(api.listExecutions).mockResolvedValue([]);
    renderHook(() => useExecutions({ autoFetch: false }));
    expect(api.listExecutions).not.toHaveBeenCalled();
  });

  it("passes status filter to API", async () => {
    vi.mocked(api.listExecutions).mockResolvedValue([]);
    renderHook(() => useExecutions({ status: "failed" }));
    await waitFor(() => {
      expect(api.listExecutions).toHaveBeenCalledWith("failed");
    });
  });

  it("provides a refresh function", async () => {
    vi.mocked(api.listExecutions).mockResolvedValue([]);
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(typeof result.current.refresh).toBe("function");
  });

  it("handles non-Error exceptions", async () => {
    vi.mocked(api.listExecutions).mockRejectedValue("string error");
    const { result } = renderHook(() => useExecutions());
    await waitFor(() => {
      expect(result.current.error).toBe("Failed to load executions");
    });
  });
});
