import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import WorkflowDetail from "../components/WorkflowDetail";
import type { Workflow, WorkflowExecution } from "../types";

const mockWorkflow: Workflow = {
  id: "wf-1",
  name: "Test Pipeline",
  description: "A test workflow",
  tasks: [
    {
      id: "t1",
      name: "Task 1",
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
  tags: ["prod", "etl"],
  version: 2,
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-02T00:00:00Z",
};

const mockExecution: WorkflowExecution = {
  id: "exec-1",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2025-01-01T00:00:00Z",
  completed_at: "2025-01-01T00:01:00Z",
  cancelled_at: null,
  task_results: [
    {
      task_id: "t1",
      status: "completed",
      started_at: "2025-01-01T00:00:00Z",
      completed_at: "2025-01-01T00:01:00Z",
      output: null,
      error: null,
      duration_ms: 1000,
    },
  ],
  trigger: "manual",
  metadata: {},
};

vi.mock("../services/api", () => ({
  getWorkflow: vi.fn(),
  listWorkflowExecutions: vi.fn(),
  executeWorkflow: vi.fn(),
  cloneWorkflow: vi.fn(),
  dryRunWorkflow: vi.fn(),
}));

import * as api from "../services/api";

describe("WorkflowDetail", () => {
  const onBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (api.getWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue(mockWorkflow);
    (api.listWorkflowExecutions as ReturnType<typeof vi.fn>).mockResolvedValue([
      mockExecution,
    ]);
  });

  it("renders workflow name after loading", async () => {
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByText("Test Pipeline")).toBeDefined();
    });
  });

  it("renders workflow description", async () => {
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByText("A test workflow")).toBeDefined();
    });
  });

  it("renders version number", async () => {
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByText("v2")).toBeDefined();
    });
  });

  it("renders tags", async () => {
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByText("prod")).toBeDefined();
      expect(screen.getByText("etl")).toBeDefined();
    });
  });

  it("renders back button that calls onBack", async () => {
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByTestId("back-btn")).toBeDefined();
    });
    fireEvent.click(screen.getByTestId("back-btn"));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("renders execute, clone, and dry-run buttons", async () => {
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByTestId("execute-btn")).toBeDefined();
      expect(screen.getByTestId("clone-btn")).toBeDefined();
      expect(screen.getByTestId("dry-run-btn")).toBeDefined();
    });
  });

  it("renders task count", async () => {
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByText("Tasks (1)")).toBeDefined();
    });
  });

  it("renders execution rows", async () => {
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      const rows = screen.getAllByTestId("execution-row");
      expect(rows.length).toBe(1);
    });
  });

  it("shows error when API fails", async () => {
    (api.getWorkflow as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Network error"),
    );
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeDefined();
    });
  });

  it("calls executeWorkflow when execute button is clicked", async () => {
    (api.executeWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue(mockExecution);
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByTestId("execute-btn")).toBeDefined();
    });
    fireEvent.click(screen.getByTestId("execute-btn"));
    await waitFor(() => {
      expect(api.executeWorkflow).toHaveBeenCalledWith("wf-1");
    });
  });

  it("calls cloneWorkflow when clone button is clicked", async () => {
    (api.cloneWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue(mockWorkflow);
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByTestId("clone-btn")).toBeDefined();
    });
    fireEvent.click(screen.getByTestId("clone-btn"));
    await waitFor(() => {
      expect(api.cloneWorkflow).toHaveBeenCalledWith("wf-1");
    });
  });

  it("calls dryRunWorkflow when dry-run button is clicked", async () => {
    (api.dryRunWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue(mockExecution);
    render(<WorkflowDetail workflowId="wf-1" onBack={onBack} />);
    await waitFor(() => {
      expect(screen.getByTestId("dry-run-btn")).toBeDefined();
    });
    fireEvent.click(screen.getByTestId("dry-run-btn"));
    await waitFor(() => {
      expect(api.dryRunWorkflow).toHaveBeenCalledWith("wf-1");
    });
  });
});
