import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ExecutionComparisonView from "../components/ExecutionComparisonView";

vi.mock("../services/api", () => ({
  compareExecutions: vi.fn().mockResolvedValue({
    workflow_id: "wf-1",
    executions: [],
    task_comparison: [
      {
        task_id: "task-abc-12345678",
        status_a: "completed",
        status_b: "failed",
        duration_diff_ms: 150,
      },
      {
        task_id: "task-def-12345678",
        status_a: "failed",
        status_b: "completed",
        duration_diff_ms: -50,
      },
    ],
    summary: {
      improved_count: 1,
      regressed_count: 1,
      unchanged_count: 0,
    },
  }),
}));

describe("ExecutionComparisonView", () => {
  const onBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders title", () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    expect(screen.getByText("Compare Executions")).toBeDefined();
  });

  it("renders back button", () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    const btn = screen.getByTestId("back-button");
    fireEvent.click(btn);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("renders input fields", () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    expect(screen.getByTestId("id-a-input")).toBeDefined();
    expect(screen.getByTestId("id-b-input")).toBeDefined();
  });

  it("renders compare button", () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    expect(screen.getByTestId("compare-button")).toBeDefined();
  });

  it("shows error when IDs are empty", async () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    fireEvent.click(screen.getByTestId("compare-button"));
    await waitFor(() => {
      expect(screen.getByText("Both execution IDs are required")).toBeDefined();
    });
  });

  it("shows comparison results after submitting", async () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    fireEvent.change(screen.getByTestId("id-a-input"), {
      target: { value: "exec-1" },
    });
    fireEvent.change(screen.getByTestId("id-b-input"), {
      target: { value: "exec-2" },
    });
    fireEvent.click(screen.getByTestId("compare-button"));

    await waitFor(() => {
      expect(screen.getByText("Task Comparison")).toBeDefined();
    });
  });

  it("shows summary cards after comparison", async () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    fireEvent.change(screen.getByTestId("id-a-input"), {
      target: { value: "exec-1" },
    });
    fireEvent.change(screen.getByTestId("id-b-input"), {
      target: { value: "exec-2" },
    });
    fireEvent.click(screen.getByTestId("compare-button"));

    await waitFor(() => {
      expect(screen.getByText("Improved")).toBeDefined();
      expect(screen.getByText("Regressed")).toBeDefined();
      expect(screen.getByText("Unchanged")).toBeDefined();
    });
  });

  it("renders vs separator", () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    expect(screen.getByText("vs")).toBeDefined();
  });

  it("renders with empty initial state (no results)", () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    expect(screen.queryByText("Task Comparison")).toBeNull();
  });

  it("shows error when only first ID is provided", async () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    fireEvent.change(screen.getByTestId("id-a-input"), {
      target: { value: "exec-1" },
    });
    fireEvent.click(screen.getByTestId("compare-button"));
    await waitFor(() => {
      expect(screen.getByText("Both execution IDs are required")).toBeDefined();
    });
  });

  it("shows error when only second ID is provided", async () => {
    render(<ExecutionComparisonView onBack={onBack} />);
    fireEvent.change(screen.getByTestId("id-b-input"), {
      target: { value: "exec-2" },
    });
    fireEvent.click(screen.getByTestId("compare-button"));
    await waitFor(() => {
      expect(screen.getByText("Both execution IDs are required")).toBeDefined();
    });
  });
});
