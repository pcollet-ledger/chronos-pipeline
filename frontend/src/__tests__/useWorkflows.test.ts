import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useWorkflows } from "../hooks/useWorkflows";
import type { Workflow } from "../types";

const mockWorkflows: Workflow[] = [
  {
    id: "w1",
    name: "Pipeline A",
    description: "Test pipeline",
    tasks: [],
    tags: ["prod"],
    schedule: null,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  },
];

const mockApi = {
  listWorkflows: vi.fn(),
  createWorkflow: vi.fn(),
  deleteWorkflow: vi.fn(),
  cloneWorkflow: vi.fn(),
};

vi.mock("../services/api", () => ({
  listWorkflows: (...args: unknown[]) => mockApi.listWorkflows(...args),
  createWorkflow: (...args: unknown[]) => mockApi.createWorkflow(...args),
  deleteWorkflow: (...args: unknown[]) => mockApi.deleteWorkflow(...args),
  cloneWorkflow: (...args: unknown[]) => mockApi.cloneWorkflow(...args),
}));

describe("useWorkflows", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.listWorkflows.mockResolvedValue(mockWorkflows);
  });

  it("fetches workflows on mount", async () => {
    const { result } = renderHook(() => useWorkflows());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockWorkflows);
    expect(result.current.error).toBeNull();
  });

  it("passes filter options to API", async () => {
    const { result } = renderHook(() =>
      useWorkflows({ tag: "prod", search: "pipe", limit: 10, offset: 5 }),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockApi.listWorkflows).toHaveBeenCalledWith("prod", "pipe", 10, 5);
  });

  it("handles fetch error", async () => {
    mockApi.listWorkflows.mockRejectedValue(new Error("Server error"));

    const { result } = renderHook(() => useWorkflows());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Server error");
    expect(result.current.data).toBeNull();
  });

  it("createWorkflow calls API and refetches", async () => {
    const newWf: Workflow = {
      id: "w2",
      name: "New Pipeline",
      description: "",
      tasks: [],
      tags: [],
      schedule: null,
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    };
    mockApi.createWorkflow.mockResolvedValue(newWf);

    const { result } = renderHook(() => useWorkflows());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.createWorkflow({
        name: "New Pipeline",
        tasks: [],
      });
    });

    expect(mockApi.createWorkflow).toHaveBeenCalledWith({
      name: "New Pipeline",
      tasks: [],
    });
    expect(mockApi.listWorkflows).toHaveBeenCalledTimes(2);
  });

  it("deleteWorkflow calls API and refetches", async () => {
    mockApi.deleteWorkflow.mockResolvedValue(undefined);

    const { result } = renderHook(() => useWorkflows());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.deleteWorkflow("w1");
    });

    expect(mockApi.deleteWorkflow).toHaveBeenCalledWith("w1");
    expect(mockApi.listWorkflows).toHaveBeenCalledTimes(2);
  });

  it("cloneWorkflow calls API and refetches", async () => {
    const cloned: Workflow = {
      id: "w1-clone",
      name: "Pipeline A (clone)",
      description: "Test pipeline",
      tasks: [],
      tags: ["prod"],
      schedule: null,
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    };
    mockApi.cloneWorkflow.mockResolvedValue(cloned);

    const { result } = renderHook(() => useWorkflows());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    let cloneResult: Workflow | undefined;
    await act(async () => {
      cloneResult = await result.current.cloneWorkflow("w1");
    });

    expect(cloneResult?.id).toBe("w1-clone");
    expect(mockApi.cloneWorkflow).toHaveBeenCalledWith("w1");
    expect(mockApi.listWorkflows).toHaveBeenCalledTimes(2);
  });

  it("refetch re-fetches workflow list", async () => {
    const { result } = renderHook(() => useWorkflows());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.refetch();
    });

    await waitFor(() => {
      expect(mockApi.listWorkflows).toHaveBeenCalledTimes(2);
    });
  });
});
