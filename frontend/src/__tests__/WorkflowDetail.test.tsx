import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import WorkflowDetail from "../components/WorkflowDetail";
import type { Workflow } from "../types";

vi.mock("../services/api", () => ({
  listWorkflowExecutions: vi.fn().mockResolvedValue([]),
  getWorkflowHistory: vi.fn().mockResolvedValue([]),
  addTags: vi.fn().mockResolvedValue({}),
  removeTag: vi.fn().mockResolvedValue({}),
  cloneWorkflow: vi.fn().mockResolvedValue({}),
  dryRunWorkflow: vi.fn().mockResolvedValue({
    id: "dry-1",
    workflow_id: "wf-1",
    status: "completed",
    started_at: null,
    completed_at: null,
    cancelled_at: null,
    task_results: [],
    trigger: "dry-run",
    metadata: {},
  }),
}));

const mockWorkflow: Workflow = {
  id: "wf-1",
  name: "Test Pipeline",
  description: "A test workflow",
  tasks: [
    {
      id: "t-1",
      name: "Task One",
      description: "",
      action: "log",
      parameters: { message: "hello" },
      depends_on: [],
      timeout_seconds: 300,
      retry_count: 0,
      priority: "medium",
      pre_hook: null,
      post_hook: null,
    },
  ],
  schedule: null,
  tags: ["prod", "etl"],
  version: 2,
  created_at: "2026-01-15T10:00:00Z",
  updated_at: "2026-01-16T10:00:00Z",
};

describe("WorkflowDetail", () => {
  const onBack = vi.fn();
  const onRefresh = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders workflow name", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByText("Test Pipeline")).toBeDefined();
  });

  it("renders workflow description", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByText("A test workflow")).toBeDefined();
  });

  it("renders version info", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByText(/Version 2/)).toBeDefined();
  });

  it("renders tags", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByText("prod")).toBeDefined();
    expect(screen.getByText("etl")).toBeDefined();
  });

  it("renders back button", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    const btn = screen.getByTestId("back-button");
    expect(btn).toBeDefined();
    fireEvent.click(btn);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders dry run button", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByTestId("dry-run-button")).toBeDefined();
  });

  it("renders clone button", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByTestId("clone-button")).toBeDefined();
  });

  it("renders tab buttons", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByTestId("tab-tasks")).toBeDefined();
    expect(screen.getByTestId("tab-executions")).toBeDefined();
    expect(screen.getByTestId("tab-history")).toBeDefined();
  });

  it("shows tasks by default", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByText("Task One")).toBeDefined();
  });

  it("renders tag input", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByTestId("tag-input")).toBeDefined();
  });

  it("renders remove tag buttons", () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByTestId("remove-tag-prod")).toBeDefined();
    expect(screen.getByTestId("remove-tag-etl")).toBeDefined();
  });

  it("switches to executions tab", async () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    fireEvent.click(screen.getByTestId("tab-executions"));
    await waitFor(() => {
      expect(screen.getByText("No executions yet")).toBeDefined();
    });
  });

  it("switches to history tab", async () => {
    render(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} onRefresh={onRefresh} />);
    fireEvent.click(screen.getByTestId("tab-history"));
    await waitFor(() => {
      expect(screen.getByText("No version history")).toBeDefined();
    });
  });

  it("renders with no description", () => {
    const wf = { ...mockWorkflow, description: "" };
    render(<WorkflowDetail workflow={wf} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByText("Test Pipeline")).toBeDefined();
  });

  it("renders with no tags", () => {
    const wf = { ...mockWorkflow, tags: [] };
    render(<WorkflowDetail workflow={wf} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByTestId("tag-input")).toBeDefined();
  });

  it("renders with no tasks", () => {
    const wf = { ...mockWorkflow, tasks: [] };
    render(<WorkflowDetail workflow={wf} onBack={onBack} onRefresh={onRefresh} />);
    expect(screen.getByTestId("tab-tasks")).toBeDefined();
  });
});
