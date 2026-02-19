import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useWorkflows } from "../hooks/useWorkflows";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  listWorkflows: vi.fn(),
}));

const mockWorkflows = [
  {
    id: "wf-1",
    name: "WF 1",
    description: "",
    tasks: [],
    schedule: null,
    tags: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

describe("useWorkflows", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches workflows on mount by default", async () => {
    vi.mocked(api.listWorkflows).mockResolvedValue(mockWorkflows);
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.workflows).toEqual(mockWorkflows);
    });
  });

  it("starts with loading true", () => {
    vi.mocked(api.listWorkflows).mockResolvedValue([]);
    const { result } = renderHook(() => useWorkflows());
    expect(result.current.loading).toBe(true);
  });

  it("sets loading to false after fetch", async () => {
    vi.mocked(api.listWorkflows).mockResolvedValue([]);
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("sets error on fetch failure", async () => {
    vi.mocked(api.listWorkflows).mockRejectedValue(new Error("Network error"));
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.error).toBe("Network error");
    });
  });

  it("starts with empty workflows array", () => {
    vi.mocked(api.listWorkflows).mockResolvedValue([]);
    const { result } = renderHook(() => useWorkflows());
    expect(result.current.workflows).toEqual([]);
  });

  it("starts with null error", () => {
    vi.mocked(api.listWorkflows).mockResolvedValue([]);
    const { result } = renderHook(() => useWorkflows());
    expect(result.current.error).toBeNull();
  });

  it("does not fetch when autoFetch is false", () => {
    vi.mocked(api.listWorkflows).mockResolvedValue([]);
    renderHook(() => useWorkflows({ autoFetch: false }));
    expect(api.listWorkflows).not.toHaveBeenCalled();
  });

  it("passes tag parameter to API", async () => {
    vi.mocked(api.listWorkflows).mockResolvedValue([]);
    renderHook(() => useWorkflows({ tag: "prod" }));
    await waitFor(() => {
      expect(api.listWorkflows).toHaveBeenCalledWith(
        expect.objectContaining({ tag: "prod" }),
      );
    });
  });

  it("passes search parameter to API", async () => {
    vi.mocked(api.listWorkflows).mockResolvedValue([]);
    renderHook(() => useWorkflows({ search: "test" }));
    await waitFor(() => {
      expect(api.listWorkflows).toHaveBeenCalledWith(
        expect.objectContaining({ search: "test" }),
      );
    });
  });

  it("provides a refresh function", async () => {
    vi.mocked(api.listWorkflows).mockResolvedValue(mockWorkflows);
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.workflows.length).toBe(1);
    });
    expect(typeof result.current.refresh).toBe("function");
  });
});
