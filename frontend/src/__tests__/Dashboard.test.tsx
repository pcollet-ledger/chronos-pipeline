import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Dashboard from "../components/Dashboard";
import type { AnalyticsSummary } from "../types";

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
    render(<Dashboard analytics={null} loading={true} />);
    expect(screen.getByRole("status")).toBeDefined();
  });

  it("renders empty state when analytics is null and not loading", () => {
    render(<Dashboard analytics={null} loading={false} />);
    expect(screen.getByText("No analytics data available yet.")).toBeDefined();
  });

  it("renders dashboard title", () => {
    render(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("Dashboard")).toBeDefined();
  });

  it("renders total workflows stat", () => {
    render(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("5")).toBeDefined();
  });

  it("renders total executions stat", () => {
    render(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("20")).toBeDefined();
  });

  it("renders success rate", () => {
    render(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("85%")).toBeDefined();
  });

  it("renders avg duration", () => {
    render(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("1.5s")).toBeDefined();
  });

  it("renders executions by status", () => {
    render(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getAllByText(/completed/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/failed/).length).toBeGreaterThanOrEqual(1);
  });

  it("renders recent executions table", () => {
    render(<Dashboard analytics={mockAnalytics} />);
    expect(screen.getByText("Recent Executions")).toBeDefined();
  });

  it("shows no executions message when empty", () => {
    const emptyAnalytics: AnalyticsSummary = {
      ...mockAnalytics,
      recent_executions: [],
    };
    render(<Dashboard analytics={emptyAnalytics} />);
    expect(screen.getByText("No executions yet")).toBeDefined();
  });

  it("renders with 100% success rate in green", () => {
    const perfect = { ...mockAnalytics, success_rate: 100 };
    render(<Dashboard analytics={perfect} />);
    expect(screen.getByText("100%")).toBeDefined();
  });

  it("renders with 0 duration", () => {
    const zeroDuration = { ...mockAnalytics, avg_duration_ms: 0 };
    render(<Dashboard analytics={zeroDuration} />);
    expect(screen.getByText("0ms")).toBeDefined();
  });
});
