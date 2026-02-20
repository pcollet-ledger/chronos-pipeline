import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useWorkflows } from "../hooks/useWorkflows";
import type { Workflow } from "../types";

const mockWorkflows: Workflow[] = [
  {
    id: "wf-1",
    name: "Pipeline A",
    description: "",
    tasks: [],
    schedule: null,
    tags: [],
    version: 1,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  },
];

vi.mock("../services/api", () => ({
  listWorkflows: vi.fn(),
}));

import * as api from "../services/api";

describe("useWorkflows", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.listWorkflows as ReturnType<typeof vi.fn>).mockResolvedValue(mockWorkflows);
  });

  it("starts with loading true", async () => {
    const { result } = renderHook(() => useWorkflows());
    expect(result.current.loading).toBe(true);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("loads workflows", async () => {
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.workflows).toEqual(mockWorkflows);
    expect(result.current.error).toBeNull();
  });

  it("sets error on failure", async () => {
    (api.listWorkflows as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Network error"),
    );
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBe("Network error");
    expect(result.current.workflows).toEqual([]);
  });

  it("passes tag parameter to API", async () => {
    const { result } = renderHook(() => useWorkflows("prod"));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(api.listWorkflows).toHaveBeenCalledWith("prod", undefined);
  });

  it("passes search parameter to API", async () => {
    const { result } = renderHook(() => useWorkflows(undefined, "test"));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(api.listWorkflows).toHaveBeenCalledWith(undefined, "test");
  });

  it("passes both tag and search to API", async () => {
    const { result } = renderHook(() => useWorkflows("prod", "test"));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(api.listWorkflows).toHaveBeenCalledWith("prod", "test");
  });

  it("refresh reloads data", async () => {
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(api.listWorkflows).toHaveBeenCalledTimes(1);

    (api.listWorkflows as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    await act(async () => {
      result.current.refresh();
    });
    await waitFor(() => {
      expect(result.current.workflows).toEqual([]);
    });
    expect(api.listWorkflows).toHaveBeenCalledTimes(2);
  });

  it("provides a refresh function", async () => {
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(typeof result.current.refresh).toBe("function");
  });

  it("re-fetches when tag changes", async () => {
    const { result, rerender } = renderHook(
      ({ tag }) => useWorkflows(tag),
      { initialProps: { tag: "a" as string | undefined } },
    );
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    rerender({ tag: "b" });
    await waitFor(() => {
      expect(api.listWorkflows).toHaveBeenCalledWith("b", undefined);
    });
  });

  it("re-fetches when search changes", async () => {
    const { result, rerender } = renderHook(
      ({ search }) => useWorkflows(undefined, search),
      { initialProps: { search: "foo" as string | undefined } },
    );
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    rerender({ search: "bar" });
    await waitFor(() => {
      expect(api.listWorkflows).toHaveBeenCalledWith(undefined, "bar");
    });
  });

  it("clears error on refresh", async () => {
    (api.listWorkflows as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("fail"),
    );
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.error).toBe("fail");
    });
    (api.listWorkflows as ReturnType<typeof vi.fn>).mockResolvedValue(mockWorkflows);
    await act(async () => {
      result.current.refresh();
    });
    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
  });

  it("handles API returning empty array", async () => {
    (api.listWorkflows as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    const { result } = renderHook(() => useWorkflows());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.workflows).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("returns empty workflows array initially", async () => {
    const { result } = renderHook(() => useWorkflows());
    expect(result.current.workflows).toEqual([]);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });
});
