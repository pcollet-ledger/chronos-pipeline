import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useApi } from "../hooks/useApi";

describe("useApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts in loading state", () => {
    const fetcher = vi.fn(() => new Promise<string>(() => {}));
    const { result } = renderHook(() => useApi(fetcher));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("resolves data on successful fetch", async () => {
    const fetcher = vi.fn().mockResolvedValue({ id: "1", name: "test" });
    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual({ id: "1", name: "test" });
    expect(result.current.error).toBeNull();
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("sets error on failed fetch", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("Network failure"));
    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("Network failure");
  });

  it("handles non-Error rejection", async () => {
    const fetcher = vi.fn().mockRejectedValue("string error");
    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Unknown error");
  });

  it("refetch re-fetches data", async () => {
    let callCount = 0;
    const fetcher = vi.fn(() => {
      callCount++;
      return Promise.resolve(`result-${callCount}`);
    });

    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toBe("result-1");

    act(() => {
      result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.data).toBe("result-2");
    });
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("refetch clears error on success", async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValueOnce(new Error("fail"))
      .mockResolvedValueOnce("ok");

    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => {
      expect(result.current.error).toBe("fail");
    });

    act(() => {
      result.current.refetch();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
    expect(result.current.data).toBe("ok");
  });
});
