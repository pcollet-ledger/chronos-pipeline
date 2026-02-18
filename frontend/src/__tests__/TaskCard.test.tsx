import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import TaskCard from "../components/TaskCard";
import type { TaskDefinition } from "../types";

const sampleTask: TaskDefinition = {
  id: "task-1",
  name: "Validate Input",
  description: "Validates user input data",
  action: "validate",
  parameters: { strict: true },
  depends_on: [],
  timeout_seconds: 300,
  retry_count: 0,
  priority: "high",
};

describe("TaskCard", () => {
  it("renders task name", () => {
    render(<TaskCard task={sampleTask} />);
    expect(screen.getByText("Validate Input")).toBeDefined();
  });

  it("renders action type", () => {
    render(<TaskCard task={sampleTask} />);
    expect(screen.getByText("validate")).toBeDefined();
  });

  it("renders priority", () => {
    render(<TaskCard task={sampleTask} />);
    expect(screen.getByText("high")).toBeDefined();
  });

  it("shows dependency count when present", () => {
    const taskWithDeps = { ...sampleTask, depends_on: ["dep-1", "dep-2"] };
    render(<TaskCard task={taskWithDeps} />);
    expect(screen.getByText("Deps: 2")).toBeDefined();
  });

  it("hides dependency count when empty", () => {
    render(<TaskCard task={sampleTask} />);
    expect(screen.queryByText(/Deps:/)).toBeNull();
  });
});
