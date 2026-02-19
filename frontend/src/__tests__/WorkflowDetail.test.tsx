import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import WorkflowDetail from "../components/WorkflowDetail";
import { ThemeProvider } from "../context/ThemeContext";
import type { Workflow, WorkflowExecution } from "../types";

const mockWorkflow: Workflow = {
  id: "w1",
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
  tags: ["prod", "v2"],
  schedule: "0 * * * *",
  created_at: "2025-01-01T00:00:00Z",
  updated_at: "2025-01-01T00:00:00Z",
};

const mockExecutions: WorkflowExecution[] = [
  {
    id: "exec-001",
    workflow_id: "w1",
    status: "completed",
    trigger: "manual",
    started_at: "2025-01-01T00:00:00Z",
    completed_at: "2025-01-01T00:01:00Z",
    cancelled_at: null,
    metadata: {},
    task_results: [],
  },
];

const mockApi = {
  listExecutions: vi.fn(),
};

vi.mock("../services/api", () => ({
  listExecutions: (...args: unknown[]) => mockApi.listExecutions(...args),
}));

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
}

describe("WorkflowDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.listExecutions.mockResolvedValue(mockExecutions);
  });

  it("renders workflow name", () => {
    renderWithTheme(<WorkflowDetail workflow={mockWorkflow} onBack={() => {}} />);
    expect(screen.getByText("Test Pipeline")).toBeDefined();
  });

  it("renders workflow description", () => {
    renderWithTheme(<WorkflowDetail workflow={mockWorkflow} onBack={() => {}} />);
    expect(screen.getByText("A test workflow")).toBeDefined();
  });

  it("renders task count", () => {
    renderWithTheme(<WorkflowDetail workflow={mockWorkflow} onBack={() => {}} />);
    expect(screen.getByText("1 tasks")).toBeDefined();
  });

  it("renders schedule", () => {
    renderWithTheme(<WorkflowDetail workflow={mockWorkflow} onBack={() => {}} />);
    expect(screen.getByText("Schedule: 0 * * * *")).toBeDefined();
  });

  it("renders tags", () => {
    renderWithTheme(<WorkflowDetail workflow={mockWorkflow} onBack={() => {}} />);
    expect(screen.getByText("prod")).toBeDefined();
    expect(screen.getByText("v2")).toBeDefined();
  });

  it("renders back button and calls onBack", () => {
    const onBack = vi.fn();
    renderWithTheme(<WorkflowDetail workflow={mockWorkflow} onBack={onBack} />);
    const backBtn = screen.getByText(/back to workflows/i);
    fireEvent.click(backBtn);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders executions after loading", async () => {
    renderWithTheme(<WorkflowDetail workflow={mockWorkflow} onBack={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText("exec-001".slice(0, 8))).toBeDefined();
    });
  });

  it("shows no executions message when empty", async () => {
    mockApi.listExecutions.mockResolvedValue([]);
    renderWithTheme(<WorkflowDetail workflow={mockWorkflow} onBack={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText("No executions yet")).toBeDefined();
    });
  });
});
