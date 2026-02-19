import { describe, it, expect, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useApi } from "../hooks/useApi";

describe("useApi", () => {
  it("starts in loading state", () => {
    const fetcher = vi.fn().mockResolvedValue("data");
    const { result } = renderHook(() => useApi(fetcher));
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("resolves data on success", async () => {
    const fetcher = vi.fn().mockResolvedValue("hello");
    const { result } = renderHook(() => useApi(fetcher));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toBe("hello");
    expect(result.current.error).toBeNull();
  });

  it("sets error on failure", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("fail"));
    const { result } = renderHook(() => useApi(fetcher));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("fail");
  });

  it("handles non-Error rejection", async () => {
    const fetcher = vi.fn().mockRejectedValue("string error");
    const { result } = renderHook(() => useApi(fetcher));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBe("Unknown error");
  });

  it("calls fetcher once on mount", async () => {
    const fetcher = vi.fn().mockResolvedValue(42);
    renderHook(() => useApi(fetcher));
    await waitFor(() => {
      expect(fetcher).toHaveBeenCalledTimes(1);
    });
  });

  it("returns refresh function", async () => {
    const fetcher = vi.fn().mockResolvedValue("a");
    const { result } = renderHook(() => useApi(fetcher));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(typeof result.current.refresh).toBe("function");
  });

  it("resolves with array data", async () => {
    const fetcher = vi.fn().mockResolvedValue([1, 2, 3]);
    const { result } = renderHook(() => useApi(fetcher));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual([1, 2, 3]);
  });

  it("resolves with null data", async () => {
    const fetcher = vi.fn().mockResolvedValue(null);
    const { result } = renderHook(() => useApi(fetcher));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toBeNull();
  });

  it("resolves with object data", async () => {
    const fetcher = vi.fn().mockResolvedValue({ key: "value" });
    const { result } = renderHook(() => useApi(fetcher));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual({ key: "value" });
  });

  it("resolves with empty string", async () => {
    const fetcher = vi.fn().mockResolvedValue("");
    const { result } = renderHook(() => useApi(fetcher));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toBe("");
  });
});
