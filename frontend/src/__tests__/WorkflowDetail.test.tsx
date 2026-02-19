import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ThemeProvider } from "../ThemeContext";
import WorkflowDetail from "../components/WorkflowDetail";
import type { Workflow } from "../types";
import * as api from "../services/api";

vi.mock("../services/api", () => ({
  listWorkflowExecutions: vi.fn().mockResolvedValue([]),
  getWorkflowHistory: vi.fn().mockResolvedValue([]),
  executeWorkflow: vi.fn().mockResolvedValue({
    id: "exec-1",
    workflow_id: "wf-1",
    status: "completed",
    started_at: "2026-01-15T10:00:00Z",
    completed_at: "2026-01-15T10:01:00Z",
    cancelled_at: null,
    task_results: [],
    trigger: "manual",
    metadata: {},
  }),
  dryRunWorkflow: vi.fn().mockResolvedValue({
    id: "dry-1",
    workflow_id: "wf-1",
    status: "completed",
    started_at: null,
    completed_at: null,
    cancelled_at: null,
    task_results: [],
    trigger: "dry_run",
    metadata: {},
  }),
  cloneWorkflow: vi.fn().mockResolvedValue({
    id: "wf-clone",
    name: "Test WF (copy)",
    description: "",
    tasks: [],
    schedule: null,
    tags: [],
    created_at: "2026-01-15T10:00:00Z",
    updated_at: "2026-01-15T10:00:00Z",
  }),
}));

const mockWorkflow: Workflow = {
  id: "wf-1",
  name: "Test Workflow",
  description: "A test workflow",
  tasks: [
    {
      id: "t-1",
      name: "Task 1",
      description: "First task",
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
  tags: ["test", "dev"],
  created_at: "2026-01-15T10:00:00Z",
  updated_at: "2026-01-15T10:00:00Z",
};

function renderWithTheme(workflow: Workflow = mockWorkflow) {
  const onBack = vi.fn();
  const onRefresh = vi.fn();
  const result = render(
    <ThemeProvider>
      <WorkflowDetail workflow={workflow} onBack={onBack} onRefresh={onRefresh} />
    </ThemeProvider>,
  );
  return { ...result, onBack, onRefresh };
}

describe("WorkflowDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders workflow name", async () => {
    renderWithTheme();
    expect(screen.getByText("Test Workflow")).toBeDefined();
  });

  it("renders workflow description", () => {
    renderWithTheme();
    expect(screen.getByText("A test workflow")).toBeDefined();
  });

  it("renders back button", () => {
    renderWithTheme();
    expect(screen.getByTestId("back-button")).toBeDefined();
  });

  it("calls onBack when back button is clicked", () => {
    const { onBack } = renderWithTheme();
    fireEvent.click(screen.getByTestId("back-button"));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders tags", () => {
    renderWithTheme();
    expect(screen.getByText("test")).toBeDefined();
    expect(screen.getByText("dev")).toBeDefined();
  });

  it("renders task count", () => {
    renderWithTheme();
    expect(screen.getByText("1 task")).toBeDefined();
  });

  it("renders Run button", () => {
    renderWithTheme();
    expect(screen.getByText("Run")).toBeDefined();
  });

  it("renders Dry Run button", () => {
    renderWithTheme();
    expect(screen.getByText("Dry Run")).toBeDefined();
  });

  it("renders Clone button", () => {
    renderWithTheme();
    expect(screen.getByText("Clone")).toBeDefined();
  });

  it("calls executeWorkflow when Run is clicked", async () => {
    renderWithTheme();
    fireEvent.click(screen.getByText("Run"));
    await waitFor(() => {
      expect(api.executeWorkflow).toHaveBeenCalledWith("wf-1");
    });
  });

  it("calls dryRunWorkflow when Dry Run is clicked", async () => {
    renderWithTheme();
    fireEvent.click(screen.getByText("Dry Run"));
    await waitFor(() => {
      expect(api.dryRunWorkflow).toHaveBeenCalledWith("wf-1");
    });
  });

  it("calls cloneWorkflow when Clone is clicked", async () => {
    const { onRefresh } = renderWithTheme();
    fireEvent.click(screen.getByText("Clone"));
    await waitFor(() => {
      expect(api.cloneWorkflow).toHaveBeenCalledWith("wf-1");
      expect(onRefresh).toHaveBeenCalled();
    });
  });

  it("shows execution history section", async () => {
    renderWithTheme();
    await waitFor(() => {
      expect(screen.getByText("Execution History (0)")).toBeDefined();
    });
  });

  it("shows no executions message when empty", async () => {
    renderWithTheme();
    await waitFor(() => {
      expect(screen.getByText("No executions yet")).toBeDefined();
    });
  });
});
