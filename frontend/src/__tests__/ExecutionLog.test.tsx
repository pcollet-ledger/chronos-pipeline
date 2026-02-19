import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ExecutionLog from "../components/ExecutionLog";
import { ThemeProvider } from "../context/ThemeContext";
import type { WorkflowExecution } from "../types";

const mockExecution: WorkflowExecution = {
  id: "exec-123",
  workflow_id: "w1",
  status: "completed",
  trigger: "manual",
  started_at: "2025-01-01T00:00:00Z",
  completed_at: "2025-01-01T00:01:00Z",
  cancelled_at: null,
  metadata: {},
  task_results: [
    {
      task_id: "task-a",
      status: "completed",
      started_at: "2025-01-01T00:00:00Z",
      completed_at: "2025-01-01T00:00:30Z",
      output: null,
      error: null,
      duration_ms: 30000,
    },
    {
      task_id: "task-b",
      status: "failed",
      started_at: "2025-01-01T00:00:30Z",
      completed_at: "2025-01-01T00:01:00Z",
      output: null,
      error: "Connection timeout",
      duration_ms: 30000,
    },
  ],
};

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
}

describe("ExecutionLog", () => {
  it("shows no execution message when null", () => {
    renderWithTheme(<ExecutionLog execution={null} />);
    expect(screen.getByText("No execution selected")).toBeDefined();
  });

  it("shows loading spinner when loading", () => {
    renderWithTheme(<ExecutionLog execution={null} loading />);
    expect(screen.getByRole("status")).toBeDefined();
  });

  it("renders execution id", () => {
    renderWithTheme(<ExecutionLog execution={mockExecution} />);
    expect(screen.getByText("exec-123")).toBeDefined();
  });

  it("renders execution status", () => {
    renderWithTheme(<ExecutionLog execution={mockExecution} />);
    const matches = screen.getAllByText("completed");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("renders trigger type", () => {
    renderWithTheme(<ExecutionLog execution={mockExecution} />);
    expect(screen.getByText("manual")).toBeDefined();
  });

  it("renders task results", () => {
    renderWithTheme(<ExecutionLog execution={mockExecution} />);
    expect(screen.getByText("task-a")).toBeDefined();
    expect(screen.getByText("task-b")).toBeDefined();
  });

  it("renders task durations", () => {
    renderWithTheme(<ExecutionLog execution={mockExecution} />);
    const durationElements = screen.getAllByText("30000ms");
    expect(durationElements.length).toBe(2);
  });

  it("renders task error", () => {
    renderWithTheme(<ExecutionLog execution={mockExecution} />);
    expect(screen.getByText("Connection timeout")).toBeDefined();
  });

  it("shows no task results message for empty execution", () => {
    const emptyExec: WorkflowExecution = {
      ...mockExecution,
      task_results: [],
    };
    renderWithTheme(<ExecutionLog execution={emptyExec} />);
    expect(screen.getByText("No task results")).toBeDefined();
  });
});
