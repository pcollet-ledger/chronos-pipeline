import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ExecutionLog from "../components/ExecutionLog";
import type { WorkflowExecution } from "../types";

const baseExecution: WorkflowExecution = {
  id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:01:00Z",
  cancelled_at: null,
  task_results: [
    {
      task_id: "11111111-2222-3333-4444-555555555555",
      status: "completed",
      started_at: "2026-01-15T10:00:00Z",
      completed_at: "2026-01-15T10:00:30Z",
      output: { result: "ok" },
      error: null,
      duration_ms: 30000,
    },
  ],
  trigger: "manual",
  metadata: {},
};

describe("ExecutionLog", () => {
  it("renders the execution log container", () => {
    render(<ExecutionLog execution={baseExecution} />);
    expect(screen.getByTestId("execution-log")).toBeDefined();
  });

  it("renders truncated execution ID", () => {
    render(<ExecutionLog execution={baseExecution} />);
    expect(screen.getByTestId("execution-id").textContent).toBe("aaaaaaaa...");
  });

  it("renders execution status", () => {
    render(<ExecutionLog execution={baseExecution} />);
    expect(screen.getByTestId("execution-status").textContent).toBe("completed");
  });

  it("renders trigger info", () => {
    render(<ExecutionLog execution={baseExecution} />);
    expect(screen.getByTestId("execution-trigger")).toBeDefined();
    expect(screen.getByText("manual")).toBeDefined();
  });

  it("renders started_at when present", () => {
    render(<ExecutionLog execution={baseExecution} />);
    expect(screen.getByTestId("execution-started")).toBeDefined();
  });

  it("renders completed_at when present", () => {
    render(<ExecutionLog execution={baseExecution} />);
    expect(screen.getByTestId("execution-completed")).toBeDefined();
  });

  it("renders task results", () => {
    render(<ExecutionLog execution={baseExecution} />);
    expect(screen.getByText("Task Results")).toBeDefined();
    expect(screen.getByTestId("task-result-11111111-2222-3333-4444-555555555555")).toBeDefined();
  });

  it("renders progress bar", () => {
    render(<ExecutionLog execution={baseExecution} />);
    expect(screen.getByRole("progressbar")).toBeDefined();
  });

  it("shows retry button for failed execution", () => {
    const failed: WorkflowExecution = { ...baseExecution, status: "failed" };
    const onRetry = vi.fn();
    render(<ExecutionLog execution={failed} onRetry={onRetry} />);
    expect(screen.getByTestId("retry-button")).toBeDefined();
  });

  it("calls onRetry with execution id", () => {
    const failed: WorkflowExecution = { ...baseExecution, status: "failed" };
    const onRetry = vi.fn();
    render(<ExecutionLog execution={failed} onRetry={onRetry} />);
    fireEvent.click(screen.getByTestId("retry-button"));
    expect(onRetry).toHaveBeenCalledWith(baseExecution.id);
  });

  it("shows cancel button for running execution", () => {
    const running: WorkflowExecution = { ...baseExecution, status: "running" };
    const onCancel = vi.fn();
    render(<ExecutionLog execution={running} onCancel={onCancel} />);
    expect(screen.getByTestId("cancel-button")).toBeDefined();
  });

  it("calls onCancel with execution id", () => {
    const running: WorkflowExecution = { ...baseExecution, status: "running" };
    const onCancel = vi.fn();
    render(<ExecutionLog execution={running} onCancel={onCancel} />);
    fireEvent.click(screen.getByTestId("cancel-button"));
    expect(onCancel).toHaveBeenCalledWith(baseExecution.id);
  });

  it("shows cancel button for pending execution", () => {
    const pending: WorkflowExecution = { ...baseExecution, status: "pending" };
    const onCancel = vi.fn();
    render(<ExecutionLog execution={pending} onCancel={onCancel} />);
    expect(screen.getByTestId("cancel-button")).toBeDefined();
  });

  it("does not show retry for running execution", () => {
    const running: WorkflowExecution = { ...baseExecution, status: "running" };
    render(<ExecutionLog execution={running} onRetry={vi.fn()} />);
    expect(screen.queryByTestId("retry-button")).toBeNull();
  });

  it("does not show cancel for completed execution", () => {
    render(<ExecutionLog execution={baseExecution} onCancel={vi.fn()} />);
    expect(screen.queryByTestId("cancel-button")).toBeNull();
  });

  it("does not show retry button when onRetry is not provided", () => {
    const failed: WorkflowExecution = { ...baseExecution, status: "failed" };
    render(<ExecutionLog execution={failed} />);
    expect(screen.queryByTestId("retry-button")).toBeNull();
  });

  it("does not show cancel button when onCancel is not provided", () => {
    const running: WorkflowExecution = { ...baseExecution, status: "running" };
    render(<ExecutionLog execution={running} />);
    expect(screen.queryByTestId("cancel-button")).toBeNull();
  });

  it("renders with no task results", () => {
    const empty: WorkflowExecution = { ...baseExecution, task_results: [] };
    render(<ExecutionLog execution={empty} />);
    expect(screen.getByTestId("execution-log")).toBeDefined();
    expect(screen.queryByText("Task Results")).toBeNull();
  });

  it("renders with multiple task results", () => {
    const multi: WorkflowExecution = {
      ...baseExecution,
      task_results: [
        { ...baseExecution.task_results[0]!, task_id: "aaa-1", status: "completed" },
        { ...baseExecution.task_results[0]!, task_id: "bbb-2", status: "failed", error: "timeout" },
      ],
    };
    render(<ExecutionLog execution={multi} />);
    expect(screen.getByTestId("task-result-aaa-1")).toBeDefined();
    expect(screen.getByTestId("task-result-bbb-2")).toBeDefined();
  });

  it("shows task duration when available", () => {
    render(<ExecutionLog execution={baseExecution} />);
    expect(screen.getByText("30000ms")).toBeDefined();
  });

  it("renders cancelled execution status", () => {
    const cancelled: WorkflowExecution = { ...baseExecution, status: "cancelled" };
    render(<ExecutionLog execution={cancelled} />);
    expect(screen.getByTestId("execution-status").textContent).toBe("cancelled");
  });

  it("does not render started when null", () => {
    const noStart: WorkflowExecution = { ...baseExecution, started_at: null };
    render(<ExecutionLog execution={noStart} />);
    expect(screen.queryByTestId("execution-started")).toBeNull();
  });

  it("does not render completed when null", () => {
    const noEnd: WorkflowExecution = { ...baseExecution, completed_at: null };
    render(<ExecutionLog execution={noEnd} />);
    expect(screen.queryByTestId("execution-completed")).toBeNull();
  });
});
