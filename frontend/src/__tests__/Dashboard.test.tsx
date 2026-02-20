import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import Dashboard from "../components/Dashboard";
import { ThemeProvider } from "../contexts/ThemeContext";
import type { AnalyticsSummary } from "../types";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
}

const mockAnalytics: AnalyticsSummary = {
  total_workflows: 5,
  total_executions: 20,
  success_rate: 85.0,
  avg_duration_ms: 1500,
  executions_by_status: { completed: 17, failed: 3 },
  recent_executions: [
    {
      id: "exec-1",
      workflow_id: "wf-1",
      status: "completed",
      started_at: "2026-01-15T10:00:00Z",
      completed_at: "2026-01-15T10:01:00Z",
      cancelled_at: null,
      task_results: [],
      trigger: "manual",
      metadata: {},
    },
  ],
  top_failing_workflows: [],
};

describe("Dashboard", () => {
  it("renders loading spinner when loading", () => {
    renderWithTheme(<Dashboard analytics={null} loading={true} />);
    expect(screen.getByRole("status")).toBeDefined();
  });

  it("renders empty state when analytics is null and not loading", () => {
    renderWithTheme(<Dashboard analytics={null} loading={false} />);
    expect(screen.getByText("No analytics data available yet.")).toBeDefined();
  });

  it("renders dashboard title", () => {
    renderWithTheme(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("Dashboard")).toBeDefined();
  });

  it("renders total workflows stat", () => {
    renderWithTheme(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("5")).toBeDefined();
  });

  it("renders total executions stat", () => {
    renderWithTheme(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("20")).toBeDefined();
  });

  it("renders success rate", () => {
    renderWithTheme(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("85%")).toBeDefined();
  });

  it("renders avg duration", () => {
    renderWithTheme(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("1.5s")).toBeDefined();
  });

  it("renders executions by status", () => {
    renderWithTheme(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getAllByText(/completed/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/failed/).length).toBeGreaterThanOrEqual(1);
  });

  it("renders recent executions table", () => {
    renderWithTheme(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("Recent Executions")).toBeDefined();
  });

  it("shows no executions message when empty", () => {
    const emptyAnalytics: AnalyticsSummary = {
      ...mockAnalytics,
      recent_executions: [],
    };
    renderWithTheme(<Dashboard analytics={emptyAnalytics} />);
    expect(screen.getByText("No executions yet")).toBeDefined();
  });

  it("renders with 100% success rate in green", () => {
    const perfect = { ...mockAnalytics, success_rate: 100 };
    renderWithTheme(<Dashboard analytics={perfect} />);
    expect(screen.getByText("100%")).toBeDefined();
  });

  it("renders with 0 duration", () => {
    const zeroDuration = { ...mockAnalytics, avg_duration_ms: 0 };
    renderWithTheme(<Dashboard analytics={zeroDuration} />);
    expect(screen.getByText("0ms")).toBeDefined();
  });
});
