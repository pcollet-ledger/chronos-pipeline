import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { useWorkflows } from "../hooks/useWorkflows";
import type { Workflow } from "../types";

const mockWorkflows: Workflow[] = [
  {
    id: "wf-1",
    name: "Pipeline A",
    description: "Test pipeline",
    tasks: [],
    schedule: null,
    tags: ["prod"],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

const mockListWorkflows = vi.fn();

vi.mock("../services/api", () => ({
  listWorkflows: (...args: unknown[]) => mockListWorkflows(...args),
}));

function TestComponent({ tag, search }: { tag?: string; search?: string }) {
  const { data, loading, error, refetch } = useWorkflows({ tag, search });
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="error">{error ?? "none"}</span>
      <span data-testid="count">{data.length}</span>
      <span data-testid="names">{data.map((w) => w.name).join(",")}</span>
      <button data-testid="refetch" onClick={refetch}>
        Refetch
      </button>
    </div>
  );
}

describe("useWorkflows", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListWorkflows.mockResolvedValue(mockWorkflows);
  });

  it("starts in loading state", () => {
    render(<TestComponent />);
    expect(screen.getByTestId("loading").textContent).toBe("true");
  });

  it("loads workflows on mount", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(screen.getByTestId("count").textContent).toBe("1");
  });

  it("returns workflow data", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("names").textContent).toBe("Pipeline A"),
    );
  });

  it("calls listWorkflows with params", async () => {
    render(<TestComponent tag="prod" search="test" />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(mockListWorkflows).toHaveBeenCalledWith({
      tag: "prod",
      search: "test",
    });
  });

  it("handles API error", async () => {
    mockListWorkflows.mockRejectedValue(new Error("Network error"));
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe("Network error"),
    );
  });

  it("handles non-Error rejection", async () => {
    mockListWorkflows.mockRejectedValue("string error");
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe(
        "Failed to load workflows",
      ),
    );
  });

  it("refetch reloads data", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(mockListWorkflows).toHaveBeenCalledTimes(1);
    await act(async () => {
      screen.getByTestId("refetch").click();
    });
    await waitFor(() =>
      expect(mockListWorkflows).toHaveBeenCalledTimes(2),
    );
  });

  it("returns empty array initially", () => {
    mockListWorkflows.mockImplementation(
      () => new Promise(() => {}), // never resolves
    );
    render(<TestComponent />);
    expect(screen.getByTestId("count").textContent).toBe("0");
  });

  it("clears error on successful refetch", async () => {
    mockListWorkflows.mockRejectedValueOnce(new Error("fail"));
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe("fail"),
    );
    mockListWorkflows.mockResolvedValueOnce(mockWorkflows);
    await act(async () => {
      screen.getByTestId("refetch").click();
    });
    await waitFor(() =>
      expect(screen.getByTestId("error").textContent).toBe("none"),
    );
  });

  it("passes empty params when none provided", async () => {
    render(<TestComponent />);
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(mockListWorkflows).toHaveBeenCalledWith({
      tag: undefined,
      search: undefined,
    });
  });
});
