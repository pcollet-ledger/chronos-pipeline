import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import WorkflowDetail from "../components/WorkflowDetail";
import type { Workflow, WorkflowExecution } from "../types";

const sampleWorkflow: Workflow = {
  id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  name: "ETL Pipeline",
  description: "Extracts, transforms, and loads data",
  tasks: [
    {
      id: "t1",
      name: "Extract",
      description: "Pull data",
      action: "log",
      parameters: {},
      depends_on: [],
      timeout_seconds: 300,
      retry_count: 0,
      priority: "high",
      pre_hook: null,
      post_hook: null,
    },
  ],
  schedule: "0 * * * *",
  tags: ["production", "etl"],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-15T00:00:00Z",
};

const sampleExecution: WorkflowExecution = {
  id: "exec-1111-2222-3333-444444444444",
  workflow_id: sampleWorkflow.id,
  status: "completed",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:01:00Z",
  cancelled_at: null,
  task_results: [
    {
      task_id: "t1",
      status: "completed",
      started_at: "2026-01-15T10:00:00Z",
      completed_at: "2026-01-15T10:00:30Z",
      output: null,
      error: null,
      duration_ms: 30000,
    },
  ],
  trigger: "manual",
  metadata: {},
};

describe("WorkflowDetail", () => {
  it("renders the detail container", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByTestId("workflow-detail")).toBeDefined();
  });

  it("renders workflow name", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByTestId("workflow-name").textContent).toBe("ETL Pipeline");
  });

  it("renders workflow description", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByTestId("workflow-description")).toBeDefined();
    expect(screen.getByText("Extracts, transforms, and loads data")).toBeDefined();
  });

  it("hides description when empty", () => {
    const noDesc = { ...sampleWorkflow, description: "" };
    render(<WorkflowDetail workflow={noDesc} executions={[]} />);
    expect(screen.queryByTestId("workflow-description")).toBeNull();
  });

  it("renders workflow tags", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByTestId("workflow-tags")).toBeDefined();
    expect(screen.getByText("production")).toBeDefined();
    expect(screen.getByText("etl")).toBeDefined();
  });

  it("hides tags section when no tags", () => {
    const noTags = { ...sampleWorkflow, tags: [] };
    render(<WorkflowDetail workflow={noTags} executions={[]} />);
    expect(screen.queryByTestId("workflow-tags")).toBeNull();
  });

  it("renders truncated workflow ID", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByTestId("workflow-id").textContent).toContain("aaaaaaaa");
  });

  it("renders schedule when present", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByTestId("workflow-schedule")).toBeDefined();
    expect(screen.getByText(/0 \* \* \* \*/)).toBeDefined();
  });

  it("hides schedule when null", () => {
    const noSched = { ...sampleWorkflow, schedule: null };
    render(<WorkflowDetail workflow={noSched} executions={[]} />);
    expect(screen.queryByTestId("workflow-schedule")).toBeNull();
  });

  it("renders created date", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByTestId("workflow-created")).toBeDefined();
  });

  it("renders task list", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByTestId("task-list")).toBeDefined();
    expect(screen.getByText("Extract")).toBeDefined();
  });

  it("renders tasks count heading", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByText("Tasks (1)")).toBeDefined();
  });

  it("hides task list when no tasks", () => {
    const noTasks = { ...sampleWorkflow, tasks: [] };
    render(<WorkflowDetail workflow={noTasks} executions={[]} />);
    expect(screen.queryByTestId("task-list")).toBeNull();
  });

  it("renders empty state when no executions", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.getByText("No executions yet. Run this workflow to see results.")).toBeDefined();
  });

  it("renders execution list when executions exist", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[sampleExecution]} />);
    expect(screen.getByTestId("execution-list")).toBeDefined();
    expect(screen.getByTestId("execution-log")).toBeDefined();
  });

  it("renders executions count heading", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[sampleExecution]} />);
    expect(screen.getByText("Executions (1)")).toBeDefined();
  });

  it("renders execute button when onExecute provided", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onExecute={vi.fn()} />);
    expect(screen.getByTestId("execute-button")).toBeDefined();
  });

  it("calls onExecute when execute button clicked", () => {
    const onExecute = vi.fn();
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onExecute={onExecute} />);
    fireEvent.click(screen.getByTestId("execute-button"));
    expect(onExecute).toHaveBeenCalledTimes(1);
  });

  it("renders dry-run button when onDryRun provided", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onDryRun={vi.fn()} />);
    expect(screen.getByTestId("dry-run-button")).toBeDefined();
  });

  it("calls onDryRun when dry-run button clicked", () => {
    const onDryRun = vi.fn();
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onDryRun={onDryRun} />);
    fireEvent.click(screen.getByTestId("dry-run-button"));
    expect(onDryRun).toHaveBeenCalledTimes(1);
  });

  it("renders clone button when onClone provided", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onClone={vi.fn()} />);
    expect(screen.getByTestId("clone-button")).toBeDefined();
  });

  it("calls onClone when clone button clicked", () => {
    const onClone = vi.fn();
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onClone={onClone} />);
    fireEvent.click(screen.getByTestId("clone-button"));
    expect(onClone).toHaveBeenCalledTimes(1);
  });

  it("renders delete button when onDelete provided", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onDelete={vi.fn()} />);
    expect(screen.getByTestId("delete-button")).toBeDefined();
  });

  it("calls onDelete when delete button clicked", () => {
    const onDelete = vi.fn();
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onDelete={onDelete} />);
    fireEvent.click(screen.getByTestId("delete-button"));
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it("renders back button when onBack provided", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onBack={vi.fn()} />);
    expect(screen.getByTestId("back-button")).toBeDefined();
  });

  it("calls onBack when back button clicked", () => {
    const onBack = vi.fn();
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} onBack={onBack} />);
    fireEvent.click(screen.getByTestId("back-button"));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("hides back button when onBack not provided", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.queryByTestId("back-button")).toBeNull();
  });

  it("hides action buttons when callbacks not provided", () => {
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[]} />);
    expect(screen.queryByTestId("execute-button")).toBeNull();
    expect(screen.queryByTestId("dry-run-button")).toBeNull();
    expect(screen.queryByTestId("clone-button")).toBeNull();
    expect(screen.queryByTestId("delete-button")).toBeNull();
  });

  it("renders all action buttons together", () => {
    render(
      <WorkflowDetail
        workflow={sampleWorkflow}
        executions={[]}
        onExecute={vi.fn()}
        onDryRun={vi.fn()}
        onClone={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByTestId("execute-button")).toBeDefined();
    expect(screen.getByTestId("dry-run-button")).toBeDefined();
    expect(screen.getByTestId("clone-button")).toBeDefined();
    expect(screen.getByTestId("delete-button")).toBeDefined();
  });

  it("renders multiple executions", () => {
    const exec2: WorkflowExecution = { ...sampleExecution, id: "exec-2222-3333-4444-555555555555" };
    render(<WorkflowDetail workflow={sampleWorkflow} executions={[sampleExecution, exec2]} />);
    expect(screen.getByText("Executions (2)")).toBeDefined();
    expect(screen.getAllByTestId("execution-log").length).toBe(2);
  });
});
