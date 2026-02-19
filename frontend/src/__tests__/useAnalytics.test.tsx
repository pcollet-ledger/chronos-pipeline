import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useAnalytics } from "../hooks/useAnalytics";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  getAnalyticsSummary: vi.fn(),
}));

const mockAnalytics = {
  total_workflows: 5,
  total_executions: 20,
  success_rate: 85,
  avg_duration_ms: 1500,
  executions_by_status: {},
  recent_executions: [],
  top_failing_workflows: [],
};

describe("useAnalytics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches analytics on mount", async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockAnalytics);
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.analytics).toEqual(mockAnalytics);
    });
  });

  it("starts with null analytics", () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockAnalytics);
    const { result } = renderHook(() => useAnalytics());
    expect(result.current.analytics).toBeNull();
  });

  it("starts with loading state", () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockAnalytics);
    const { result } = renderHook(() => useAnalytics());
    expect(result.current.loading).toBe(true);
  });

  it("sets loading to false after fetch", async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockAnalytics);
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("sets error on failure", async () => {
    vi.mocked(api.getAnalyticsSummary).mockRejectedValue(new Error("Fail"));
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.error).toBe("Fail");
    });
  });

  it("starts with null error", () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockAnalytics);
    const { result } = renderHook(() => useAnalytics());
    expect(result.current.error).toBeNull();
  });

  it("passes days parameter to API", async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockAnalytics);
    renderHook(() => useAnalytics(7));
    await waitFor(() => {
      expect(api.getAnalyticsSummary).toHaveBeenCalledWith(7);
    });
  });

  it("defaults to 30 days", async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockAnalytics);
    renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(api.getAnalyticsSummary).toHaveBeenCalledWith(30);
    });
  });

  it("provides a refresh function", async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockAnalytics);
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.analytics).toBeDefined();
    });
    expect(typeof result.current.refresh).toBe("function");
  });

  it("handles non-Error exceptions", async () => {
    vi.mocked(api.getAnalyticsSummary).mockRejectedValue("string error");
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.error).toBe("Failed to load analytics");
    });
  });
});
