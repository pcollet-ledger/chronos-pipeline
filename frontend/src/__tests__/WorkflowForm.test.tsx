import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import WorkflowForm from "../components/WorkflowForm";

describe("WorkflowForm", () => {
  it("renders the form", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    expect(screen.getByTestId("workflow-form")).toBeDefined();
  });

  it("renders name input", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    expect(screen.getByTestId("workflow-name-input")).toBeDefined();
  });

  it("renders description textarea", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    expect(screen.getByTestId("workflow-description-input")).toBeDefined();
  });

  it("renders tags input", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    expect(screen.getByTestId("workflow-tags-input")).toBeDefined();
  });

  it("renders submit button", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    expect(screen.getByTestId("submit-button")).toBeDefined();
  });

  it("shows Create Workflow button text by default", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    expect(screen.getByText("Create Workflow")).toBeDefined();
  });

  it("shows Update Workflow when initialData is provided", () => {
    render(
      <WorkflowForm
        onSubmit={vi.fn()}
        initialData={{ name: "Test", description: "", tags: [], tasks: [] }}
      />,
    );
    expect(screen.getByText("Update Workflow")).toBeDefined();
  });

  it("shows validation error when name is empty", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    fireEvent.click(screen.getByTestId("submit-button"));
    expect(screen.getByTestId("name-error")).toBeDefined();
    expect(screen.getByText("Workflow name is required")).toBeDefined();
  });

  it("calls onSubmit with correct data", () => {
    const onSubmit = vi.fn();
    render(<WorkflowForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByTestId("workflow-name-input"), {
      target: { value: "My Workflow" },
    });
    fireEvent.click(screen.getByTestId("submit-button"));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ name: "My Workflow" }),
    );
  });

  it("does not call onSubmit when validation fails", () => {
    const onSubmit = vi.fn();
    render(<WorkflowForm onSubmit={onSubmit} />);
    fireEvent.click(screen.getByTestId("submit-button"));
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("adds a task when Add Task is clicked", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    fireEvent.click(screen.getByTestId("add-task-button"));
    expect(screen.getByTestId("task-entry-0")).toBeDefined();
  });

  it("removes a task when Remove is clicked", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    fireEvent.click(screen.getByTestId("add-task-button"));
    expect(screen.getByTestId("task-entry-0")).toBeDefined();
    fireEvent.click(screen.getByTestId("remove-task-0"));
    expect(screen.queryByTestId("task-entry-0")).toBeNull();
  });

  it("pre-fills values in edit mode", () => {
    render(
      <WorkflowForm
        onSubmit={vi.fn()}
        initialData={{
          name: "Existing WF",
          description: "A description",
          tags: ["prod", "daily"],
          tasks: [],
        }}
      />,
    );
    const nameInput = screen.getByTestId("workflow-name-input") as HTMLInputElement;
    expect(nameInput.value).toBe("Existing WF");
  });

  it("renders tag chips from comma-separated input", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);
    fireEvent.change(screen.getByTestId("workflow-tags-input"), {
      target: { value: "alpha, beta, gamma" },
    });
    expect(screen.getByText("alpha")).toBeDefined();
    expect(screen.getByText("beta")).toBeDefined();
    expect(screen.getByText("gamma")).toBeDefined();
  });

  it("includes tags in submission", () => {
    const onSubmit = vi.fn();
    render(<WorkflowForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByTestId("workflow-name-input"), {
      target: { value: "Tagged WF" },
    });
    fireEvent.change(screen.getByTestId("workflow-tags-input"), {
      target: { value: "tag1, tag2" },
    });
    fireEvent.click(screen.getByTestId("submit-button"));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ tags: ["tag1", "tag2"] }),
    );
  });

  it("calls onCancel when cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(<WorkflowForm onSubmit={vi.fn()} onCancel={onCancel} />);
    fireEvent.click(screen.getByText("Cancel"));
    expect(onCancel).toHaveBeenCalled();
  });

  it("includes tasks in submission", () => {
    const onSubmit = vi.fn();
    render(<WorkflowForm onSubmit={onSubmit} />);

    fireEvent.change(screen.getByTestId("workflow-name-input"), {
      target: { value: "WF with tasks" },
    });
    fireEvent.click(screen.getByTestId("add-task-button"));
    fireEvent.change(screen.getByTestId("task-name-0"), {
      target: { value: "My Task" },
    });
    fireEvent.click(screen.getByTestId("submit-button"));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        tasks: expect.arrayContaining([
          expect.objectContaining({ name: "My Task", action: "log" }),
        ]),
      }),
    );
  });

  it("shows task validation error for empty task name", () => {
    render(<WorkflowForm onSubmit={vi.fn()} />);

    fireEvent.change(screen.getByTestId("workflow-name-input"), {
      target: { value: "WF" },
    });
    fireEvent.click(screen.getByTestId("add-task-button"));
    fireEvent.click(screen.getByTestId("submit-button"));

    expect(screen.getByText("Task name is required")).toBeDefined();
  });
});
