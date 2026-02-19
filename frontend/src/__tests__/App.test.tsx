import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "../App";

vi.mock("../services/api", () => ({
  listWorkflows: vi.fn().mockResolvedValue([]),
  getAnalyticsSummary: vi.fn().mockResolvedValue({
    total_workflows: 0,
    total_executions: 0,
    success_rate: 0,
    avg_duration_ms: 0,
    executions_by_status: {},
    recent_executions: [],
    top_failing_workflows: [],
  }),
}));

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the header with Chronos Pipeline title", () => {
    render(<App />);
    expect(screen.getByText("Chronos Pipeline")).toBeDefined();
  });

  it("renders navigation buttons", () => {
    render(<App />);
    expect(screen.getByText("dashboard")).toBeDefined();
    expect(screen.getByText("workflows")).toBeDefined();
    expect(screen.getByText("compare")).toBeDefined();
  });

  it("renders refresh button", () => {
    render(<App />);
    expect(screen.getByText("Refresh")).toBeDefined();
  });
});
