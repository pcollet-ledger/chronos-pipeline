import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import WorkflowDetail from "../components/WorkflowDetail";
import { ThemeProvider } from "../context/ThemeContext";

const mockWorkflow = {
  id: "wf-123",
  name: "Test Pipeline",
  description: "A test workflow",
  tasks: [
    {
      id: "t1",
      name: "Task One",
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
  tags: ["test", "dev"],
  version: 2,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-15T00:00:00Z",
};

const mockExecution = {
  id: "ex-456",
  workflow_id: "wf-123",
  status: "completed",
  started_at: "2026-01-15T10:00:00Z",
  completed_at: "2026-01-15T10:01:00Z",
  cancelled_at: null,
  task_results: [
    {
      task_id: "t1",
      status: "completed",
      started_at: "2026-01-15T10:00:00Z",
      completed_at: "2026-01-15T10:01:00Z",
      output: { result: "ok" },
      error: null,
      duration_ms: 60000,
    },
  ],
  trigger: "manual",
  metadata: {},
};

vi.mock("../services/api", () => ({
  getWorkflow: vi.fn(),
  listWorkflowExecutions: vi.fn(),
  executeWorkflow: vi.fn(),
  dryRunWorkflow: vi.fn(),
  cloneWorkflow: vi.fn(),
  deleteWorkflow: vi.fn(),
  addWorkflowTags: vi.fn(),
  removeWorkflowTag: vi.fn(),
  getWorkflowHistory: vi.fn(),
  updateWorkflow: vi.fn(),
}));

function renderDetail(props?: Partial<React.ComponentProps<typeof WorkflowDetail>>) {
  const defaultProps = {
    workflowId: "wf-123",
    onBack: vi.fn(),
    onRefresh: vi.fn(),
  };
  return render(
    <ThemeProvider>
      <WorkflowDetail {...defaultProps} {...props} />
    </ThemeProvider>,
  );
}

describe("WorkflowDetail", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    localStorage.clear();
    const api = await import("../services/api");
    (api.getWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue(mockWorkflow);
    (api.listWorkflowExecutions as ReturnType<typeof vi.fn>).mockResolvedValue([mockExecution]);
    (api.executeWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue(mockExecution);
    (api.dryRunWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue({ ...mockExecution, trigger: "dry_run" });
    (api.cloneWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue({ ...mockWorkflow, id: "wf-clone" });
    (api.deleteWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue(undefined);
    (api.addWorkflowTags as ReturnType<typeof vi.fn>).mockResolvedValue({ ...mockWorkflow, tags: ["test", "dev", "new"] });
    (api.removeWorkflowTag as ReturnType<typeof vi.fn>).mockResolvedValue({ ...mockWorkflow, tags: ["dev"] });
    (api.getWorkflowHistory as ReturnType<typeof vi.fn>).mockResolvedValue([
      { ...mockWorkflow, version: 1, name: "Old Name" },
    ]);
    (api.updateWorkflow as ReturnType<typeof vi.fn>).mockResolvedValue({ ...mockWorkflow, name: "Updated" });
  });

  it("renders workflow name after loading", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Test Pipeline")).toBeDefined();
    });
  });

  it("renders workflow description", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("A test workflow")).toBeDefined();
    });
  });

  it("renders tags", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("test")).toBeDefined();
      expect(screen.getByText("dev")).toBeDefined();
    });
  });

  it("renders version info", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText(/Version 2/)).toBeDefined();
    });
  });

  it("renders task count", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Tasks (1)")).toBeDefined();
    });
  });

  it("renders back button", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("back-button")).toBeDefined();
    });
  });

  it("calls onBack when back button clicked", async () => {
    const onBack = vi.fn();
    renderDetail({ onBack });
    await waitFor(() => {
      expect(screen.getByTestId("back-button")).toBeDefined();
    });
    fireEvent.click(screen.getByTestId("back-button"));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("renders execution table", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Recent Executions")).toBeDefined();
      expect(screen.getByText("ex-456...")).toBeDefined();
    });
  });

  it("renders version history toggle", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("toggle-history")).toBeDefined();
    });
  });

  it("renders action buttons", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Run")).toBeDefined();
      expect(screen.getByText("Dry Run")).toBeDefined();
      expect(screen.getByText("Clone")).toBeDefined();
      expect(screen.getByText("Delete")).toBeDefined();
      expect(screen.getByText("Edit")).toBeDefined();
    });
  });

  it("shows edit form when Edit is clicked", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Edit")).toBeDefined();
    });
    fireEvent.click(screen.getByText("Edit"));
    expect(screen.getByTestId("edit-name-input")).toBeDefined();
    expect(screen.getByTestId("edit-description-input")).toBeDefined();
  });

  it("renders tag input", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByTestId("tag-input")).toBeDefined();
    });
  });
});
