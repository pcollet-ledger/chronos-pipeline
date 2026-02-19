import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useAnalytics, useTimeline } from "../hooks/useAnalytics";
import type { AnalyticsSummary, TimelineBucket } from "../types";

const mockSummary: AnalyticsSummary = {
  total_workflows: 5,
  total_executions: 42,
  success_rate: 0.85,
  avg_duration_ms: 1200,
  executions_by_status: { completed: 36, failed: 6 },
  recent_executions: [],
  top_failing_workflows: [],
};

const mockBuckets: TimelineBucket[] = [
  { time: "2025-01-01T00:00:00Z", total: 10, completed: 8, failed: 2 },
  { time: "2025-01-01T01:00:00Z", total: 5, completed: 5, failed: 0 },
];

const mockApi = {
  getAnalyticsSummary: vi.fn(),
  getTimeline: vi.fn(),
};

vi.mock("../services/api", () => ({
  getAnalyticsSummary: (...args: unknown[]) => mockApi.getAnalyticsSummary(...args),
  getTimeline: (...args: unknown[]) => mockApi.getTimeline(...args),
}));

describe("useAnalytics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.getAnalyticsSummary.mockResolvedValue(mockSummary);
  });

  it("fetches analytics summary on mount", async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockSummary);
    expect(result.current.error).toBeNull();
    expect(mockApi.getAnalyticsSummary).toHaveBeenCalledWith(30);
  });

  it("passes custom days parameter", async () => {
    const { result } = renderHook(() => useAnalytics(7));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockApi.getAnalyticsSummary).toHaveBeenCalledWith(7);
  });

  it("handles error", async () => {
    mockApi.getAnalyticsSummary.mockRejectedValue(new Error("Analytics unavailable"));

    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Analytics unavailable");
    expect(result.current.data).toBeNull();
  });
});

describe("useTimeline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.getTimeline.mockResolvedValue(mockBuckets);
  });

  it("fetches timeline on mount", async () => {
    const { result } = renderHook(() => useTimeline());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockBuckets);
    expect(mockApi.getTimeline).toHaveBeenCalledWith(24, 60);
  });

  it("passes custom parameters", async () => {
    const { result } = renderHook(() => useTimeline(48, 30));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockApi.getTimeline).toHaveBeenCalledWith(48, 30);
  });

  it("handles error", async () => {
    mockApi.getTimeline.mockRejectedValue(new Error("Timeline error"));

    const { result } = renderHook(() => useTimeline());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Timeline error");
  });
});
