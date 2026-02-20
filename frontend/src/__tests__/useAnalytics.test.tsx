import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useAnalytics } from "../hooks/useAnalytics";
import type { AnalyticsSummary, TimelineBucket } from "../types";

const mockSummary: AnalyticsSummary = {
  total_workflows: 5,
  total_executions: 20,
  success_rate: 0.85,
  avg_duration_ms: 1200,
  executions_by_status: { completed: 17, failed: 3 },
  recent_executions: [],
  top_failing_workflows: [],
};

const mockTimeline: TimelineBucket[] = [
  { time: "2025-01-01T00:00:00Z", total: 10, completed: 8, failed: 2 },
];

vi.mock("../services/api", () => ({
  getAnalyticsSummary: vi.fn(),
  getTimeline: vi.fn(),
}));

import * as api from "../services/api";

describe("useAnalytics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getAnalyticsSummary as ReturnType<typeof vi.fn>).mockResolvedValue(mockSummary);
    (api.getTimeline as ReturnType<typeof vi.fn>).mockResolvedValue(mockTimeline);
  });

  it("starts with loading true", async () => {
    const { result } = renderHook(() => useAnalytics());
    expect(result.current.loading).toBe(true);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("loads summary and timeline", async () => {
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.summary).toEqual(mockSummary);
    expect(result.current.timeline).toEqual(mockTimeline);
    expect(result.current.error).toBeNull();
  });

  it("sets error on failure", async () => {
    (api.getAnalyticsSummary as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Analytics error"),
    );
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBe("Analytics error");
  });

  it("passes days parameter", async () => {
    const { result } = renderHook(() => useAnalytics(7));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(api.getAnalyticsSummary).toHaveBeenCalledWith(7);
  });

  it("passes hours and bucketMinutes parameters", async () => {
    const { result } = renderHook(() => useAnalytics(30, 48, 30));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(api.getTimeline).toHaveBeenCalledWith(48, 30);
  });

  it("uses default parameters", async () => {
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(api.getAnalyticsSummary).toHaveBeenCalledWith(30);
    expect(api.getTimeline).toHaveBeenCalledWith(24, 60);
  });

  it("refresh reloads data", async () => {
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    const updatedSummary = { ...mockSummary, total_workflows: 10 };
    (api.getAnalyticsSummary as ReturnType<typeof vi.fn>).mockResolvedValue(updatedSummary);
    await act(async () => {
      result.current.refresh();
    });
    await waitFor(() => {
      expect(result.current.summary).toEqual(updatedSummary);
    });
  });

  it("provides a refresh function", async () => {
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(typeof result.current.refresh).toBe("function");
  });

  it("summary starts as null", async () => {
    const { result } = renderHook(() => useAnalytics());
    expect(result.current.summary).toBeNull();
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("timeline starts as empty array", async () => {
    const { result } = renderHook(() => useAnalytics());
    expect(result.current.timeline).toEqual([]);
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("clears error on successful refresh", async () => {
    (api.getAnalyticsSummary as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error("fail"),
    );
    const { result } = renderHook(() => useAnalytics());
    await waitFor(() => {
      expect(result.current.error).toBe("fail");
    });
    (api.getAnalyticsSummary as ReturnType<typeof vi.fn>).mockResolvedValue(mockSummary);
    await act(async () => {
      result.current.refresh();
    });
    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
  });
});
