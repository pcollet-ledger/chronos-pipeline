import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { useAnalytics } from "../hooks/useAnalytics";
import type { AnalyticsSummary } from "../types";

const mockSummary: AnalyticsSummary = {
  total_workflows: 5,
  total_executions: 20,
  success_rate: 85,
  avg_duration_ms: 1500,
  executions_by_status: { completed: 17, failed: 3 },
  recent_executions: [],
  top_failing_workflows: [],
};

const mockGetAnalyticsSummary = vi.fn();

vi.mock("../services/api", () => ({
  getAnalyticsSummary: (...args: unknown[]) => mockGetAnalyticsSummary(...args),
}));

function TestComponent({ days }: { days?: number }) {
  const { data, loading, error, refetch } = useAnalytics(days);
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="error">{error ?? "none"}</span>
      <span data-testid="total">{data?.total_workflows ?? "null"}</span>
      <span data-testid="rate">{data?.success_rate ?? "null"}</span>
      <button data-testid="refetch" onClick={refetch}>
        Refetch
      </button>
    </div>
  );
}

describe("useAnalytics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetAnalyticsSummary.mockResolvedValue(mockSummary);
  });

  it("starts in loading state", () => {
    render(<TestComponent />);
    expect(screen.getByTestId("loading").textContent).toBe("true");
  });

  it("loads analytics on mount", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(screen.getByTestId("total").textContent).toBe("5");
  });

  it("returns success rate", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("rate").textContent).toBe("85"),
    );
  });

  it("passes default days=30 to API", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(mockGetAnalyticsSummary).toHaveBeenCalledWith(30);
  });

  it("passes custom days to API", async () => {
    render(<TestComponent days={7} />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(mockGetAnalyticsSummary).toHaveBeenCalledWith(7);
  });

  it("handles API error", async () => {
    mockGetAnalyticsSummary.mockRejectedValue(new Error("Server error"));
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe("Server error"),
    );
  });

  it("handles non-Error rejection", async () => {
    mockGetAnalyticsSummary.mockRejectedValue(42);
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe(
        "Failed to load analytics",
      ),
    );
  });

  it("data is null initially", () => {
    mockGetAnalyticsSummary.mockImplementation(() => new Promise(() => {}));
    render(<TestComponent />);
    expect(screen.getByTestId("total").textContent).toBe("null");
  });

  it("refetch reloads data", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    await act(async () => {
      screen.getByTestId("refetch").click();
    });
    await waitFor(() =>
      expect(mockGetAnalyticsSummary).toHaveBeenCalledTimes(2),
    );
  });

  it("clears error on successful refetch", async () => {
    mockGetAnalyticsSummary.mockRejectedValueOnce(new Error("fail"));
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe("fail"),
    );
    mockGetAnalyticsSummary.mockResolvedValueOnce(mockSummary);
    await act(async () => {
      screen.getByTestId("refetch").click();
    });
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe("none"),
    );
  });
});
