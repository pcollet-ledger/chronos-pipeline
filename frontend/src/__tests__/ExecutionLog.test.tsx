import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ExecutionLog from "../components/ExecutionLog";
import type { WorkflowExecution, TaskResult } from "../types";

vi.mock("../services/api", () => ({
  retryExecution: vi.fn().mockResolvedValue({
    id: "retry-1",
    workflow_id: "wf-1",
    status: "completed",
    started_at: "2024-01-01T00:00:00Z",
    completed_at: "2024-01-01T00:01:00Z",
    cancelled_at: null,
    task_results: [],
    trigger: "retry",
    metadata: {},
  }),
}));

const completedTask: TaskResult = {
  task_id: "task-1",
  status: "completed",
  started_at: "2024-01-01T00:00:00Z",
  completed_at: "2024-01-01T00:00:01Z",
  output: { message: "done" },
  error: null,
  duration_ms: 1000,
};

const failedTask: TaskResult = {
  task_id: "task-2",
  status: "failed",
  started_at: "2024-01-01T00:00:01Z",
  completed_at: "2024-01-01T00:00:02Z",
  output: null,
  error: "Something went wrong",
  duration_ms: 500,
};

const completedExecution: WorkflowExecution = {
  id: "exec-1",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2024-01-01T00:00:00Z",
  completed_at: "2024-01-01T00:01:00Z",
  cancelled_at: null,
  task_results: [completedTask],
  trigger: "manual",
  metadata: {},
};

const failedExecution: WorkflowExecution = {
  id: "exec-2",
  workflow_id: "wf-1",
  status: "failed",
  started_at: "2024-01-01T00:00:00Z",
  completed_at: "2024-01-01T00:01:00Z",
  cancelled_at: null,
  task_results: [completedTask, failedTask],
  trigger: "manual",
  metadata: {},
};

const emptyExecution: WorkflowExecution = {
  id: "exec-3",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2024-01-01T00:00:00Z",
  completed_at: "2024-01-01T00:01:00Z",
  cancelled_at: null,
  task_results: [],
  trigger: "manual",
  metadata: {},
};

describe("ExecutionLog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the execution log container", () => {
    render(<ExecutionLog execution={completedExecution} />);
    expect(screen.getByTestId("execution-log")).toBeDefined();
  });

  it("renders task steps", () => {
    render(<ExecutionLog execution={completedExecution} />);
    expect(screen.getByTestId("task-step-task-1")).toBeDefined();
  });

  it("shows completed icon for completed tasks", () => {
    render(<ExecutionLog execution={completedExecution} />);
    expect(screen.getByTestId("icon-task-1").textContent).toBe("\u2713");
  });

  it("shows failed icon for failed tasks", () => {
    render(<ExecutionLog execution={failedExecution} />);
    expect(screen.getByTestId("icon-task-2").textContent).toBe("\u2717");
  });

  it("shows error message for failed tasks", () => {
    render(<ExecutionLog execution={failedExecution} />);
    expect(screen.getByTestId("error-task-2")).toBeDefined();
    expect(screen.getByText("Something went wrong")).toBeDefined();
  });

  it("shows retry button for failed executions", () => {
    render(<ExecutionLog execution={failedExecution} />);
    expect(screen.getByTestId("retry-button")).toBeDefined();
    expect(screen.getByText("Retry Failed Tasks")).toBeDefined();
  });

  it("does not show retry button for completed executions", () => {
    render(<ExecutionLog execution={completedExecution} />);
    expect(screen.queryByTestId("retry-button")).toBeNull();
  });

  it("shows empty message for empty execution", () => {
    render(<ExecutionLog execution={emptyExecution} />);
    expect(screen.getByTestId("empty-log")).toBeDefined();
  });

  it("expands failed tasks by default", () => {
    render(<ExecutionLog execution={failedExecution} />);
    expect(screen.getByTestId("error-task-2")).toBeDefined();
  });

  it("can toggle task output visibility", () => {
    render(<ExecutionLog execution={completedExecution} />);
    expect(screen.queryByTestId("output-task-1")).toBeNull();
    const toggle = screen.getByTestId("toggle-task-1");
    fireEvent.click(toggle);
    expect(screen.getByTestId("output-task-1")).toBeDefined();
    fireEvent.click(toggle);
    expect(screen.queryByTestId("output-task-1")).toBeNull();
  });

  it("formats duration correctly", () => {
    render(<ExecutionLog execution={completedExecution} />);
    expect(screen.getByText("1.0s")).toBeDefined();
  });

  it("calls retry API and onRetryComplete", async () => {
    const onRetryComplete = vi.fn();
    render(
      <ExecutionLog execution={failedExecution} onRetryComplete={onRetryComplete} />,
    );
    fireEvent.click(screen.getByTestId("retry-button"));
    await waitFor(() => {
      expect(onRetryComplete).toHaveBeenCalled();
    });
  });

  it("renders multiple task steps", () => {
    render(<ExecutionLog execution={failedExecution} />);
    expect(screen.getByTestId("task-step-task-1")).toBeDefined();
    expect(screen.getByTestId("task-step-task-2")).toBeDefined();
  });
});
