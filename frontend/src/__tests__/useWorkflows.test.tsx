import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useWorkflows } from "../hooks/useWorkflows";

const mockData = [
  {
    id: "wf-1",
    name: "Pipeline A",
    description: "",
    tasks: [],
    schedule: null,
    tags: ["prod"],
    version: 1,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "wf-2",
    name: "Pipeline B",
    description: "",
    tasks: [],
    schedule: null,
    tags: [],
    version: 1,
    created_at: "2026-01-02T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
  },
];

vi.mock("../services/api", () => ({
  listWorkflows: vi.fn(),
}));

describe("useWorkflows", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const api = await import("../services/api");
    (api.listWorkflows as ReturnType<typeof vi.fn>).mockResolvedValue(mockData);
  });

  it("starts in loading state", () => {
    const { result } = renderHook(() => useWorkflows());
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("loads workflows", async () => {
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });

  it("handles errors", async () => {
    const api = await import("../services/api");
    (api.listWorkflows as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBe("Network error");
    expect(result.current.data).toEqual([]);
  });

  it("provides a refetch function", async () => {
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(typeof result.current.refetch).toBe("function");
  });
});
