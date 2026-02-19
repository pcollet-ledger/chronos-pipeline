import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import WorkflowForm, { validateForm } from "../components/WorkflowForm";
import type { Workflow, TaskFormEntry } from "../types";

// ---------------------------------------------------------------------------
// Mock API
// ---------------------------------------------------------------------------

const mockCreate = vi.fn().mockResolvedValue({ id: "new-id", name: "Test" });
const mockUpdate = vi.fn().mockResolvedValue({ id: "edit-id", name: "Edited" });

vi.mock("../services/api", () => ({
  createWorkflow: (...args: unknown[]) => mockCreate(...args),
  updateWorkflow: (...args: unknown[]) => mockUpdate(...args),
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const sampleWorkflow: Workflow = {
  id: "wf-1",
  name: "Existing Pipeline",
  description: "A test pipeline",
  tasks: [
    {
      id: "t-1",
      name: "Log Step",
      description: "",
      action: "log",
      parameters: { message: "hello" },
      depends_on: [],
      timeout_seconds: 300,
      retry_count: 0,
      priority: "high",
      pre_hook: "validate",
      post_hook: null,
    },
  ],
  schedule: null,
  tags: ["prod", "etl"],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const onSuccess = vi.fn();
const onCancel = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
});

// ===========================================================================
// Unit tests for validateForm
// ===========================================================================

describe("validateForm", () => {
  it("returns empty errors for valid input", () => {
    const tasks: TaskFormEntry[] = [
      {
        name: "Step",
        action: "log",
        parameters: {},
        depends_on: [],
        pre_hook: "",
        post_hook: "",
        priority: "medium",
      },
    ];
    const errors = validateForm("My WF", "desc", tasks);
    expect(errors.name).toBeUndefined();
    expect(errors.taskErrors).toBeUndefined();
  });

  it("requires a non-empty name", () => {
    const errors = validateForm("", "", []);
    expect(errors.name).toBeDefined();
  });

  it("requires name trimmed to be non-empty", () => {
    const errors = validateForm("   ", "", []);
    expect(errors.name).toBeDefined();
  });

  it("rejects names longer than 200 characters", () => {
    const errors = validateForm("A".repeat(201), "", []);
    expect(errors.name).toContain("200");
  });

  it("accepts names at exactly 200 characters", () => {
    const errors = validateForm("A".repeat(200), "", []);
    expect(errors.name).toBeUndefined();
  });

  it("rejects descriptions longer than 5000 characters", () => {
    const errors = validateForm("Valid", "D".repeat(5001), []);
    expect(errors.description).toBeDefined();
  });

  it("flags empty task name", () => {
    const tasks: TaskFormEntry[] = [
      {
        name: "",
        action: "log",
        parameters: {},
        depends_on: [],
        pre_hook: "",
        post_hook: "",
        priority: "medium",
      },
    ];
    const errors = validateForm("WF", "", tasks);
    expect(errors.taskErrors?.[0]?.name).toBeDefined();
  });

  it("flags duplicate task names", () => {
    const tasks: TaskFormEntry[] = [
      { name: "Same", action: "log", parameters: {}, depends_on: [], pre_hook: "", post_hook: "", priority: "medium" },
      { name: "Same", action: "log", parameters: {}, depends_on: [], pre_hook: "", post_hook: "", priority: "medium" },
    ];
    const errors = validateForm("WF", "", tasks);
    expect(errors.taskErrors?.[1]?.name).toContain("Duplicate");
  });

  it("flags invalid action name", () => {
    const tasks: TaskFormEntry[] = [
      { name: "Step", action: "bad_action" as TaskFormEntry["action"], parameters: {}, depends_on: [], pre_hook: "", post_hook: "", priority: "medium" },
    ];
    const errors = validateForm("WF", "", tasks);
    expect(errors.taskErrors?.[0]?.action).toBeDefined();
  });

  it("flags unknown dependency", () => {
    const tasks: TaskFormEntry[] = [
      { name: "A", action: "log", parameters: {}, depends_on: ["NonExistent"], pre_hook: "", post_hook: "", priority: "medium" },
    ];
    const errors = validateForm("WF", "", tasks);
    expect(errors.taskErrors?.[0]?.depends_on).toContain("NonExistent");
  });

  it("accepts valid dependency references", () => {
    const tasks: TaskFormEntry[] = [
      { name: "A", action: "log", parameters: {}, depends_on: [], pre_hook: "", post_hook: "", priority: "medium" },
      { name: "B", action: "log", parameters: {}, depends_on: ["A"], pre_hook: "", post_hook: "", priority: "medium" },
    ];
    const errors = validateForm("WF", "", tasks);
    expect(errors.taskErrors).toBeUndefined();
  });

  it("returns no errors for zero tasks", () => {
    const errors = validateForm("WF", "", []);
    expect(errors.taskErrors).toBeUndefined();
  });
});

// ===========================================================================
// Component rendering tests
// ===========================================================================

describe("WorkflowForm component", () => {
  it("renders create mode heading", () => {
    render(<WorkflowForm onSuccess={onSuccess} onCancel={onCancel} />);
    expect(screen.getByText("New Pipeline")).toBeDefined();
  });

  it("renders edit mode heading when workflow provided", () => {
    render(
      <WorkflowForm
        workflow={sampleWorkflow}
        onSuccess={onSuccess}
        onCancel={onCancel}
      />,
    );
    expect(screen.getByText("Edit Pipeline")).toBeDefined();
  });

  it("pre-fills name in edit mode", () => {
    render(
      <WorkflowForm
        workflow={sampleWorkflow}
        onSuccess={onSuccess}
        onCancel={onCancel}
      />,
    );
    const input = screen.getByLabelText("Workflow name") as HTMLInputElement;
    expect(input.value).toBe("Existing Pipeline");
  });

  it("pre-fills description in edit mode", () => {
    render(
      <WorkflowForm
        workflow={sampleWorkflow}
        onSuccess={onSuccess}
        onCancel={onCancel}
      />,
    );
    const textarea = screen.getByLabelText("Workflow description") as HTMLTextAreaElement;
    expect(textarea.value).toBe("A test pipeline");
  });

  it("pre-fills tags as comma-separated string", () => {
    render(
      <WorkflowForm
        workflow={sampleWorkflow}
        onSuccess={onSuccess}
        onCancel={onCancel}
      />,
    );
    const input = screen.getByLabelText("Tags") as HTMLInputElement;
    expect(input.value).toBe("prod, etl");
  });

  it("pre-fills task entries in edit mode", () => {
    render(
      <WorkflowForm
        workflow={sampleWorkflow}
        onSuccess={onSuccess}
        onCancel={onCancel}
      />,
    );
    expect(screen.getByText("Task 1")).toBeDefined();
    const nameInput = screen.getByLabelText("Task 1 name") as HTMLInputElement;
    expect(nameInput.value).toBe("Log Step");
  });

  it("shows validation error for empty name on submit", async () => {
    render(<WorkflowForm onSuccess={onSuccess} onCancel={onCancel} />);
    fireEvent.click(screen.getByText("Create Pipeline"));
    await waitFor(() => {
      expect(screen.getByText("Workflow name is required.")).toBeDefined();
    });
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it("calls onCancel when cancel button is clicked", () => {
    render(<WorkflowForm onSuccess={onSuccess} onCancel={onCancel} />);
    fireEvent.click(screen.getByText("Cancel"));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("adds a new task entry when Add Task is clicked", () => {
    render(<WorkflowForm onSuccess={onSuccess} onCancel={onCancel} />);
    fireEvent.click(screen.getByText("+ Add Task"));
    expect(screen.getByText("Task 1")).toBeDefined();
  });

  it("removes a task entry when Remove is clicked", () => {
    render(<WorkflowForm onSuccess={onSuccess} onCancel={onCancel} />);
    fireEvent.click(screen.getByText("+ Add Task"));
    expect(screen.getByText("Task 1")).toBeDefined();
    fireEvent.click(screen.getByLabelText("Remove task 1"));
    expect(screen.queryByText("Task 1")).toBeNull();
  });

  it("submits create form with valid data", async () => {
    render(<WorkflowForm onSuccess={onSuccess} onCancel={onCancel} />);
    fireEvent.change(screen.getByLabelText("Workflow name"), {
      target: { value: "New Pipeline" },
    });
    fireEvent.click(screen.getByText("Create Pipeline"));
    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledTimes(1);
    });
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("submits update form in edit mode", async () => {
    render(
      <WorkflowForm
        workflow={sampleWorkflow}
        onSuccess={onSuccess}
        onCancel={onCancel}
      />,
    );
    fireEvent.change(screen.getByLabelText("Workflow name"), {
      target: { value: "Renamed" },
    });
    fireEvent.click(screen.getByText("Update Pipeline"));
    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledTimes(1);
    });
    expect(mockUpdate.mock.calls[0][0]).toBe("wf-1");
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("shows submit error when API call fails", async () => {
    mockCreate.mockRejectedValueOnce(new Error("Network error"));
    render(<WorkflowForm onSuccess={onSuccess} onCancel={onCancel} />);
    fireEvent.change(screen.getByLabelText("Workflow name"), {
      target: { value: "Fail" },
    });
    fireEvent.click(screen.getByText("Create Pipeline"));
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeDefined();
    });
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("renders tag chips from comma-separated input", () => {
    render(<WorkflowForm onSuccess={onSuccess} onCancel={onCancel} />);
    fireEvent.change(screen.getByLabelText("Tags"), {
      target: { value: "alpha, beta, gamma" },
    });
    expect(screen.getByText("alpha")).toBeDefined();
    expect(screen.getByText("beta")).toBeDefined();
    expect(screen.getByText("gamma")).toBeDefined();
  });

  it("validates task name is required on submit", async () => {
    render(<WorkflowForm onSuccess={onSuccess} onCancel={onCancel} />);
    fireEvent.change(screen.getByLabelText("Workflow name"), {
      target: { value: "Valid WF" },
    });
    fireEvent.click(screen.getByText("+ Add Task"));
    fireEvent.click(screen.getByText("Create Pipeline"));
    await waitFor(() => {
      expect(screen.getByText("Task name is required.")).toBeDefined();
    });
    expect(mockCreate).not.toHaveBeenCalled();
  });
});
