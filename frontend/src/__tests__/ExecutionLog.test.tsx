import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider } from "../ThemeContext";
import ExecutionLog from "../components/ExecutionLog";
import type { WorkflowExecution } from "../types";

const mockExecution: WorkflowExecution = {
  id: "exec-abc12345-6789",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:01:00Z",
  cancelled_at: null,
  task_results: [
    {
      task_id: "task-111-aaa",
      status: "completed",
      started_at: "2026-01-15T10:00:00Z",
      completed_at: "2026-01-15T10:00:30Z",
      output: { result: "ok" },
      error: null,
      duration_ms: 500,
    },
    {
      task_id: "task-222-bbb",
      status: "failed",
      started_at: "2026-01-15T10:00:30Z",
      completed_at: "2026-01-15T10:01:00Z",
      output: null,
      error: "Timeout exceeded",
      duration_ms: 1200,
    },
  ],
  trigger: "manual",
  metadata: {},
};

function renderWithTheme(execution: WorkflowExecution, onClose?: () => void) {
  return render(
    <ThemeProvider>
      <ExecutionLog execution={execution} onClose={onClose} />
    </ThemeProvider>,
  );
}

describe("ExecutionLog", () => {
  it("renders the execution log container", () => {
    renderWithTheme(mockExecution);
    expect(screen.getByTestId("execution-log")).toBeDefined();
  });

  it("shows truncated execution ID", () => {
    renderWithTheme(mockExecution);
    expect(screen.getByText("exec-abc")).toBeDefined();
  });

  it("shows trigger type", () => {
    renderWithTheme(mockExecution);
    expect(screen.getByText(/manual/)).toBeDefined();
  });

  it("shows execution status", () => {
    renderWithTheme(mockExecution);
    expect(screen.getAllByText("completed").length).toBeGreaterThanOrEqual(1);
  });

  it("renders close button when onClose is provided", () => {
    const onClose = vi.fn();
    renderWithTheme(mockExecution, onClose);
    expect(screen.getByLabelText("Close execution log")).toBeDefined();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    renderWithTheme(mockExecution, onClose);
    fireEvent.click(screen.getByLabelText("Close execution log"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not render close button when onClose is not provided", () => {
    renderWithTheme(mockExecution);
    expect(screen.queryByLabelText("Close execution log")).toBeNull();
  });

  it("renders progress bar", () => {
    renderWithTheme(mockExecution);
    expect(screen.getByRole("progressbar")).toBeDefined();
  });

  it("shows task count in progress label", () => {
    renderWithTheme(mockExecution);
    expect(screen.getByText("1/2 tasks completed")).toBeDefined();
  });

  it("renders task result rows", () => {
    renderWithTheme(mockExecution);
    expect(screen.getByText("task-111")).toBeDefined();
    expect(screen.getByText("task-222")).toBeDefined();
  });

  it("shows task duration", () => {
    renderWithTheme(mockExecution);
    expect(screen.getByText("500ms")).toBeDefined();
    expect(screen.getByText("1200ms")).toBeDefined();
  });

  it("shows task error message", () => {
    renderWithTheme(mockExecution);
    expect(screen.getByText("Timeout exceeded")).toBeDefined();
  });

  it("shows no task results message when empty", () => {
    const emptyExec: WorkflowExecution = {
      ...mockExecution,
      task_results: [],
    };
    renderWithTheme(emptyExec);
    expect(screen.getByText("No task results")).toBeDefined();
  });

  it("renders with failed status", () => {
    const failedExec: WorkflowExecution = {
      ...mockExecution,
      status: "failed",
    };
    renderWithTheme(failedExec);
    expect(screen.getAllByText("failed").length).toBeGreaterThanOrEqual(1);
  });
});
