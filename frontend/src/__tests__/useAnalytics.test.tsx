import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useAnalytics } from "../hooks/useAnalytics";

const mockAnalytics = {
  total_workflows: 5,
  total_executions: 20,
  success_rate: 85,
  avg_duration_ms: 1500,
  executions_by_status: { completed: 17, failed: 3 },
  recent_executions: [],
  top_failing_workflows: [],
};

vi.mock("../services/api", () => ({
  getAnalyticsSummary: vi.fn(),
}));

describe("useAnalytics", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const api = await import("../services/api");
    (api.getAnalyticsSummary as ReturnType<typeof vi.fn>).mockResolvedValue(mockAnalytics);
  });

  it("starts in loading state", () => {
    const { result } = renderHook(() => useAnalytics());
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("loads analytics data", async () => {
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.data).toEqual(mockAnalytics);
    expect(result.current.error).toBeNull();
  });

  it("handles errors", async () => {
    const api = await import("../services/api");
    (api.getAnalyticsSummary as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("Server error"),
    );

    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBe("Server error");
    expect(result.current.data).toBeNull();
  });

  it("provides a refetch function", async () => {
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(typeof result.current.refetch).toBe("function");
  });
});
