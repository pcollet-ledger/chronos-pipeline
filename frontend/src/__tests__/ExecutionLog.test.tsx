import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ExecutionLog from "../components/ExecutionLog";
import type { WorkflowExecution } from "../types";
import { ThemeProvider } from "../context/ThemeContext";

function wrap(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
}

const baseExecution: WorkflowExecution = {
  id: "exec-abc-123-def-456",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:01:00Z",
  cancelled_at: null,
  task_results: [
    {
      task_id: "task-aaa-bbb-ccc",
      status: "completed",
      started_at: "2026-01-15T10:00:00Z",
      completed_at: "2026-01-15T10:00:30Z",
      output: { result: "ok" },
      error: null,
      duration_ms: 500,
    },
  ],
  trigger: "manual",
  metadata: {},
};

describe("ExecutionLog", () => {
  it("renders loading spinner when loading", () => {
    wrap(<ExecutionLog executions={[]} loading={true} />);
    expect(screen.getByRole("status")).toBeDefined();
  });

  it("renders empty state when no executions", () => {
    wrap(<ExecutionLog executions={[]} loading={false} />);
    expect(screen.getByText("No executions to display.")).toBeDefined();
  });

  it("renders execution count in heading", () => {
    wrap(<ExecutionLog executions={[baseExecution]} />);
    expect(screen.getByText("Execution Log (1)")).toBeDefined();
  });

  it("renders execution entry with truncated ID", () => {
    wrap(<ExecutionLog executions={[baseExecution]} />);
    expect(screen.getByTestId(`execution-entry-${baseExecution.id}`)).toBeDefined();
  });

  it("renders status badge for completed execution", () => {
    wrap(<ExecutionLog executions={[baseExecution]} />);
    const badges = screen.getAllByTestId("status-badge-completed");
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it("renders trigger information", () => {
    wrap(<ExecutionLog executions={[baseExecution]} />);
    expect(screen.getByText(/Trigger: manual/)).toBeDefined();
  });

  it("renders task results table headers", () => {
    wrap(<ExecutionLog executions={[baseExecution]} />);
    expect(screen.getByText("Task ID")).toBeDefined();
    expect(screen.getByText("Duration")).toBeDefined();
    expect(screen.getByText("Output / Error")).toBeDefined();
  });

  it("renders task duration in milliseconds", () => {
    wrap(<ExecutionLog executions={[baseExecution]} />);
    expect(screen.getByText("500ms")).toBeDefined();
  });

  it("renders failed execution status badge", () => {
    const failedExec: WorkflowExecution = {
      ...baseExecution,
      id: "exec-fail-001",
      status: "failed",
      task_results: [
        {
          task_id: "task-fail-001",
          status: "failed",
          started_at: "2026-01-15T10:00:00Z",
          completed_at: "2026-01-15T10:00:10Z",
          output: null,
          error: "Connection timeout",
          duration_ms: 10000,
        },
      ],
    };
    wrap(<ExecutionLog executions={[failedExec]} />);
    expect(screen.getByText("Connection timeout")).toBeDefined();
  });

  it("renders multiple executions", () => {
    const second: WorkflowExecution = {
      ...baseExecution,
      id: "exec-second-789",
    };
    wrap(<ExecutionLog executions={[baseExecution, second]} />);
    expect(screen.getByText("Execution Log (2)")).toBeDefined();
  });

  it("shows no task results message for empty results", () => {
    const noResults: WorkflowExecution = {
      ...baseExecution,
      id: "exec-empty-results",
      task_results: [],
    };
    wrap(<ExecutionLog executions={[noResults]} />);
    expect(screen.getByText("No task results recorded.")).toBeDefined();
  });

  it("renders execution-log test id container", () => {
    wrap(<ExecutionLog executions={[baseExecution]} />);
    expect(screen.getByTestId("execution-log")).toBeDefined();
  });
});
