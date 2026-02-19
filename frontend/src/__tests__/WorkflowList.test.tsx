import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import WorkflowList from "../components/WorkflowList";
import type { Workflow } from "../types";

vi.mock("../services/api", () => ({
  createWorkflow: vi.fn().mockResolvedValue({}),
  deleteWorkflow: vi.fn().mockResolvedValue(undefined),
  executeWorkflow: vi.fn().mockResolvedValue({
    id: "exec-1",
    workflow_id: "wf-1",
    status: "completed",
    started_at: null,
    completed_at: null,
    cancelled_at: null,
    task_results: [],
    trigger: "manual",
    metadata: {},
  }),
}));

const mockWorkflows: Workflow[] = [
  {
    id: "wf-1",
    name: "Pipeline Alpha",
    description: "First pipeline",
    tasks: [
      {
        id: "t-1",
        name: "Task A",
        description: "",
        action: "log",
        parameters: {},
        depends_on: [],
        timeout_seconds: 300,
        retry_count: 0,
        priority: "medium",
        pre_hook: null,
        post_hook: null,
      },
    ],
    schedule: null,
    tags: ["prod"],
    version: 1,
    created_at: "2026-01-15T10:00:00Z",
    updated_at: "2026-01-15T10:00:00Z",
  },
  {
    id: "wf-2",
    name: "Pipeline Beta",
    description: "",
    tasks: [],
    schedule: null,
    tags: [],
    version: 1,
    created_at: "2026-01-16T10:00:00Z",
    updated_at: "2026-01-16T10:00:00Z",
  },
];

describe("WorkflowList", () => {
  const onRefresh = vi.fn();
  const onSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders workflow names", () => {
    render(<WorkflowList workflows={mockWorkflows} onRefresh={onRefresh} />);
    expect(screen.getByText("Pipeline Alpha")).toBeDefined();
    expect(screen.getByText("Pipeline Beta")).toBeDefined();
  });

  it("renders empty state when no workflows", () => {
    render(<WorkflowList workflows={[]} onRefresh={onRefresh} />);
    expect(screen.getByText("No pipelines yet. Create one to get started.")).toBeDefined();
  });

  it("renders new pipeline button", () => {
    render(<WorkflowList workflows={mockWorkflows} onRefresh={onRefresh} />);
    expect(screen.getByTestId("toggle-form-button")).toBeDefined();
  });

  it("toggles form visibility", () => {
    render(<WorkflowList workflows={mockWorkflows} onRefresh={onRefresh} />);
    const btn = screen.getByTestId("toggle-form-button");
    fireEvent.click(btn);
    expect(screen.getByTestId("workflow-form")).toBeDefined();
  });

  it("renders tags", () => {
    render(<WorkflowList workflows={mockWorkflows} onRefresh={onRefresh} />);
    expect(screen.getByText("prod")).toBeDefined();
  });

  it("renders task count", () => {
    render(<WorkflowList workflows={mockWorkflows} onRefresh={onRefresh} />);
    expect(screen.getByText("1 task")).toBeDefined();
  });

  it("renders view button when onSelect provided", () => {
    render(
      <WorkflowList
        workflows={mockWorkflows}
        onRefresh={onRefresh}
        onSelect={onSelect}
      />,
    );
    expect(screen.getByTestId("view-wf-1")).toBeDefined();
  });

  it("calls onSelect when view button clicked", () => {
    render(
      <WorkflowList
        workflows={mockWorkflows}
        onRefresh={onRefresh}
        onSelect={onSelect}
      />,
    );
    fireEvent.click(screen.getByTestId("view-wf-1"));
    expect(onSelect).toHaveBeenCalledWith(mockWorkflows[0]);
  });

  it("does not render view button when onSelect not provided", () => {
    render(<WorkflowList workflows={mockWorkflows} onRefresh={onRefresh} />);
    expect(screen.queryByTestId("view-wf-1")).toBeNull();
  });

  it("renders description when present", () => {
    render(<WorkflowList workflows={mockWorkflows} onRefresh={onRefresh} />);
    expect(screen.getByText("First pipeline")).toBeDefined();
  });

  it("renders pipelines heading", () => {
    render(<WorkflowList workflows={mockWorkflows} onRefresh={onRefresh} />);
    expect(screen.getByText("Pipelines")).toBeDefined();
  });

  it("renders run and delete buttons for each workflow", () => {
    render(<WorkflowList workflows={mockWorkflows} onRefresh={onRefresh} />);
    const runButtons = screen.getAllByText("Run");
    const deleteButtons = screen.getAllByText("Delete");
    expect(runButtons.length).toBe(2);
    expect(deleteButtons.length).toBe(2);
  });
});
