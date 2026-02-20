import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import TaskCard from "../components/TaskCard";
import { ThemeProvider } from "../contexts/ThemeContext";
import type { TaskDefinition } from "../types";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
}

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
  pre_hook: null,
  post_hook: null,
};

describe("TaskCard", () => {
  it("renders task name", () => {
    renderWithTheme(<TaskCard task={sampleTask} />);
    expect(screen.getByText("Validate Input")).toBeDefined();
  });

  it("renders action type", () => {
    renderWithTheme(<TaskCard task={sampleTask} />);
    expect(screen.getByText("validate")).toBeDefined();
  });

  it("renders priority", () => {
    renderWithTheme(<TaskCard task={sampleTask} />);
    expect(screen.getByText("high")).toBeDefined();
  });

  it("shows dependency count when present", () => {
    const taskWithDeps = { ...sampleTask, depends_on: ["dep-1", "dep-2"] };
    renderWithTheme(<TaskCard task={taskWithDeps} />);
    expect(screen.getByText("Deps: 2")).toBeDefined();
  });

  it("hides dependency count when empty", () => {
    renderWithTheme(<TaskCard task={sampleTask} />);
    expect(screen.queryByText(/Deps:/)).toBeNull();
  });

  it("shows pre-hook when set", () => {
    const taskWithPreHook = { ...sampleTask, pre_hook: "log" };
    renderWithTheme(<TaskCard task={taskWithPreHook} />);
    expect(screen.getByText("log")).toBeDefined();
    expect(screen.getByText(/Pre-hook:/)).toBeDefined();
  });

  it("shows post-hook when set", () => {
    const taskWithPostHook = { ...sampleTask, post_hook: "notify" };
    renderWithTheme(<TaskCard task={taskWithPostHook} />);
    expect(screen.getByText("notify")).toBeDefined();
    expect(screen.getByText(/Post-hook:/)).toBeDefined();
  });

  it("hides hook labels when hooks are null", () => {
    renderWithTheme(<TaskCard task={sampleTask} />);
    expect(screen.queryByText(/Pre-hook:/)).toBeNull();
    expect(screen.queryByText(/Post-hook:/)).toBeNull();
  });

  it("renders with low priority", () => {
    const lowTask = { ...sampleTask, priority: "low" as const };
    renderWithTheme(<TaskCard task={lowTask} />);
    expect(screen.getByText("low")).toBeDefined();
  });

  it("renders with critical priority", () => {
    const criticalTask = { ...sampleTask, priority: "critical" as const };
    renderWithTheme(<TaskCard task={criticalTask} />);
    expect(screen.getByText("critical")).toBeDefined();
  });

  it("renders with medium priority", () => {
    const medTask = { ...sampleTask, priority: "medium" as const };
    renderWithTheme(<TaskCard task={medTask} />);
    expect(screen.getByText("medium")).toBeDefined();
  });

  it("renders with both hooks set", () => {
    const taskBothHooks = { ...sampleTask, pre_hook: "validate", post_hook: "notify" };
    renderWithTheme(<TaskCard task={taskBothHooks} />);
    expect(screen.getByText(/Pre-hook:/)).toBeDefined();
    expect(screen.getByText(/Post-hook:/)).toBeDefined();
  });

  it("handles task with empty description", () => {
    const taskNoDesc = { ...sampleTask, description: "" };
    renderWithTheme(<TaskCard task={taskNoDesc} />);
    expect(screen.getByText("Validate Input")).toBeDefined();
  });

  it("handles task with many dependencies", () => {
    const taskManyDeps = { ...sampleTask, depends_on: ["a", "b", "c", "d", "e"] };
    renderWithTheme(<TaskCard task={taskManyDeps} />);
    expect(screen.getByText("Deps: 5")).toBeDefined();
  });

  it("renders with empty parameters", () => {
    const taskNoParams = { ...sampleTask, parameters: {} };
    renderWithTheme(<TaskCard task={taskNoParams} />);
    expect(screen.getByText("Validate Input")).toBeDefined();
  });

  it("renders with single dependency", () => {
    const taskOneDep = { ...sampleTask, depends_on: ["dep-1"] };
    renderWithTheme(<TaskCard task={taskOneDep} />);
    expect(screen.getByText("Deps: 1")).toBeDefined();
  });
});
