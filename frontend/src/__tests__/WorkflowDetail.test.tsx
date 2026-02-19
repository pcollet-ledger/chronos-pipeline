import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import WorkflowDetail from "../components/WorkflowDetail";
import { ThemeProvider } from "../context/ThemeContext";
import type { Workflow, WorkflowExecution } from "../types";

const mockWorkflow: Workflow = {
  id: "wf-detail-1",
  name: "Test Pipeline",
  description: "A test pipeline",
  tasks: [
    {
      id: "task-1",
      name: "Step 1",
      description: "First step",
      action: "log",
      parameters: {},
      depends_on: [],
      timeout_seconds: 30,
      retry_count: 0,
      priority: "medium",
      pre_hook: null,
      post_hook: null,
    },
  ],
  schedule: null,
  tags: ["prod", "daily"],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

const mockExecution: WorkflowExecution = {
  id: "exec-detail-1",
  workflow_id: "wf-detail-1",
  status: "completed",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:01:00Z",
  cancelled_at: null,
  task_results: [],
  trigger: "manual",
  metadata: {},
};

const mockGetWorkflow = vi.fn();
const mockListWorkflowExecutions = vi.fn();
const mockGetWorkflowHistory = vi.fn();
const mockExecuteWorkflow = vi.fn();
const mockCloneWorkflow = vi.fn();
const mockDryRunWorkflow = vi.fn();
const mockAddWorkflowTags = vi.fn();
const mockRemoveWorkflowTag = vi.fn();

vi.mock("../services/api", () => ({
  getWorkflow: (...args: unknown[]) => mockGetWorkflow(...args),
  listWorkflowExecutions: (...args: unknown[]) =>
    mockListWorkflowExecutions(...args),
  getWorkflowHistory: (...args: unknown[]) => mockGetWorkflowHistory(...args),
  executeWorkflow: (...args: unknown[]) => mockExecuteWorkflow(...args),
  cloneWorkflow: (...args: unknown[]) => mockCloneWorkflow(...args),
  dryRunWorkflow: (...args: unknown[]) => mockDryRunWorkflow(...args),
  addWorkflowTags: (...args: unknown[]) => mockAddWorkflowTags(...args),
  removeWorkflowTag: (...args: unknown[]) => mockRemoveWorkflowTag(...args),
}));

function wrap(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
}

describe("WorkflowDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetWorkflow.mockResolvedValue(mockWorkflow);
    mockListWorkflowExecutions.mockResolvedValue([mockExecution]);
    mockGetWorkflowHistory.mockResolvedValue([
      { version: 1, name: "Test Pipeline", snapshot_at: "2026-01-01T00:00:00Z" },
    ]);
    mockExecuteWorkflow.mockResolvedValue(mockExecution);
    mockCloneWorkflow.mockResolvedValue({ ...mockWorkflow, id: "wf-clone-1" });
    mockDryRunWorkflow.mockResolvedValue({
      ...mockExecution,
      id: "exec-dry-1",
    });
    mockAddWorkflowTags.mockResolvedValue({
      ...mockWorkflow,
      tags: [...mockWorkflow.tags, "new-tag"],
    });
    mockRemoveWorkflowTag.mockResolvedValue({
      ...mockWorkflow,
      tags: ["daily"],
    });
  });

  it("shows loading spinner initially", () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    expect(screen.getByRole("status")).toBeDefined();
  });

  it("renders workflow name after loading", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByText("Test Pipeline")).toBeDefined(),
    );
  });

  it("renders workflow description", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByText("A test pipeline")).toBeDefined(),
    );
  });

  it("renders back button", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("back-button")).toBeDefined(),
    );
  });

  it("calls onBack when back button clicked", async () => {
    const onBack = vi.fn();
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={onBack} />);
    await waitFor(() =>
      expect(screen.getByTestId("back-button")).toBeDefined(),
    );
    fireEvent.click(screen.getByTestId("back-button"));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders tags", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("prod")).toBeDefined());
    expect(screen.getByText("daily")).toBeDefined();
  });

  it("renders action buttons", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("execute-button")).toBeDefined(),
    );
    expect(screen.getByTestId("dry-run-button")).toBeDefined();
    expect(screen.getByTestId("clone-button")).toBeDefined();
  });

  it("renders tab navigation", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("tab-tasks")).toBeDefined(),
    );
    expect(screen.getByTestId("tab-executions")).toBeDefined();
    expect(screen.getByTestId("tab-history")).toBeDefined();
  });

  it("shows tasks panel by default", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("tasks-panel")).toBeDefined(),
    );
  });

  it("switches to executions tab", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("tab-executions")).toBeDefined(),
    );
    fireEvent.click(screen.getByTestId("tab-executions"));
    expect(screen.getByTestId("execution-log")).toBeDefined();
  });

  it("switches to history tab", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("tab-history")).toBeDefined(),
    );
    fireEvent.click(screen.getByTestId("tab-history"));
    expect(screen.getByTestId("history-panel")).toBeDefined();
  });

  it("renders task count in tab label", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByText(/tasks \(1\)/i)).toBeDefined(),
    );
  });

  it("renders tag input", async () => {
    wrap(<WorkflowDetail workflowId="wf-detail-1" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByTestId("tag-input")).toBeDefined(),
    );
  });

  it("shows error when API fails", async () => {
    mockGetWorkflow.mockRejectedValue(new Error("Not found"));
    wrap(<WorkflowDetail workflowId="wf-bad" onBack={vi.fn()} />);
    await waitFor(() =>
      expect(screen.getByText("Not found")).toBeDefined(),
    );
  });
});
