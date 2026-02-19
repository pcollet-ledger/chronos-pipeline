/**
 * Integration tests verifying that Task A (theme module) and Task B
 * (WorkflowForm) work correctly together.
 *
 * jsdom normalises inline hex colours to rgb() notation, so we compare
 * against the rgb equivalent using a small converter helper.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import WorkflowForm from "../components/WorkflowForm";
import TaskCard from "../components/TaskCard";
import Dashboard from "../components/Dashboard";
import { colors, priorityColors, statusColors } from "../styles/theme";
import type { TaskDefinition, AnalyticsSummary } from "../types";

vi.mock("../services/api", () => ({
  createWorkflow: vi.fn().mockResolvedValue({ id: "int-id", name: "Int" }),
  updateWorkflow: vi.fn().mockResolvedValue({ id: "int-id", name: "Int" }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

/** Convert a hex colour like "#1e293b" to "rgb(30, 41, 59)". */
function hexToRgb(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgb(${r}, ${g}, ${b})`;
}

describe("Theme + WorkflowForm integration", () => {
  it("form container uses theme neutral-800 background", () => {
    const { container } = render(
      <WorkflowForm onSuccess={vi.fn()} onCancel={vi.fn()} />,
    );
    const formDiv = container.firstChild as HTMLElement;
    expect(formDiv.style.background).toBe(hexToRgb(colors.neutral[800]));
  });

  it("form heading uses theme neutral-200 colour", () => {
    render(<WorkflowForm onSuccess={vi.fn()} onCancel={vi.fn()} />);
    const heading = screen.getByText("New Pipeline");
    expect(heading.style.color).toBe(hexToRgb(colors.neutral[200]));
  });

  it("error messages use theme error colour", async () => {
    render(<WorkflowForm onSuccess={vi.fn()} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByText("Create Pipeline"));
    await waitFor(() => {
      const errorEl = screen.getByText("Workflow name is required.");
      expect(errorEl.style.color).toBe(hexToRgb(colors.error.main));
    });
  });

  it("tag chips use theme neutral-700 background", () => {
    render(<WorkflowForm onSuccess={vi.fn()} onCancel={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("Tags"), {
      target: { value: "test-tag" },
    });
    const chip = screen.getByText("test-tag");
    expect(chip.style.background).toBe(hexToRgb(colors.neutral[700]));
  });

  it("task entry uses theme primary-light border colour", () => {
    render(<WorkflowForm onSuccess={vi.fn()} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByText("+ Add Task"));
    const entry = screen.getByTestId("task-entry-0");
    expect(entry.style.borderLeft).toContain(hexToRgb(colors.primary.light));
  });

  it("form and TaskCard share the same neutral palette", () => {
    const task: TaskDefinition = {
      id: "t-1",
      name: "Shared",
      description: "",
      action: "log",
      parameters: {},
      depends_on: [],
      timeout_seconds: 300,
      retry_count: 0,
      priority: "high",
      pre_hook: null,
      post_hook: null,
    };
    const { container } = render(<TaskCard task={task} />);
    const card = container.firstChild as HTMLElement;
    expect(card.style.background).toBe(hexToRgb(colors.neutral[900]));
  });
});

describe("Theme + TaskCard integration", () => {
  it("uses priorityColors from theme for border", () => {
    const task: TaskDefinition = {
      id: "t-1",
      name: "Critical",
      description: "",
      action: "validate",
      parameters: {},
      depends_on: [],
      timeout_seconds: 300,
      retry_count: 0,
      priority: "critical",
      pre_hook: null,
      post_hook: null,
    };
    const { container } = render(<TaskCard task={task} />);
    const card = container.firstChild as HTMLElement;
    expect(card.style.borderLeft).toContain(hexToRgb(priorityColors.critical));
  });

  it("low priority uses neutral-500 from theme", () => {
    const task: TaskDefinition = {
      id: "t-2",
      name: "Low",
      description: "",
      action: "log",
      parameters: {},
      depends_on: [],
      timeout_seconds: 300,
      retry_count: 0,
      priority: "low",
      pre_hook: null,
      post_hook: null,
    };
    const { container } = render(<TaskCard task={task} />);
    const card = container.firstChild as HTMLElement;
    expect(card.style.borderLeft).toContain(hexToRgb(priorityColors.low));
  });
});

describe("Theme + Dashboard integration", () => {
  const analytics: AnalyticsSummary = {
    total_workflows: 5,
    total_executions: 20,
    success_rate: 95.0,
    avg_duration_ms: 1234,
    executions_by_status: { completed: 19, failed: 1 },
    recent_executions: [],
    top_failing_workflows: [],
  };

  it("stat cards use theme neutral-800 background", () => {
    const { container } = render(<Dashboard analytics={analytics} />);
    const statCards = container.querySelectorAll("div");
    const rgbValue = hexToRgb(colors.neutral[800]);
    const card = Array.from(statCards).find(
      (el) => (el as HTMLElement).style.background === rgbValue,
    );
    expect(card).toBeDefined();
  });

  it("statusColors are consistent between Dashboard and theme", () => {
    expect(statusColors.completed).toBe(colors.success.main);
    expect(statusColors.failed).toBe(colors.error.main);
  });

  it("loading state uses theme neutral-500 colour", () => {
    render(<Dashboard analytics={null} />);
    const loading = screen.getByText("Loading analytics...");
    expect(loading.style.color).toBe(hexToRgb(colors.neutral[500]));
  });
});
