import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import {
  listWorkflows,
  getWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  executeWorkflow,
  listExecutions,
  getExecution,
  getAnalyticsSummary,
  getTimeline,
} from "../services/api";
import type {
  Workflow,
  WorkflowExecution,
  AnalyticsSummary,
} from "../types";

const mockWorkflow: Workflow = {
  id: "wf-1",
  name: "Test Workflow",
  description: "A test workflow",
  tasks: [],
  schedule: null,
  tags: ["test"],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockExecution: WorkflowExecution = {
  id: "exec-1",
  workflow_id: "wf-1",
  status: "completed",
  started_at: "2026-01-01T00:00:00Z",
  completed_at: "2026-01-01T00:01:00Z",
  task_results: [],
  trigger: "manual",
};

const mockAnalytics: AnalyticsSummary = {
  total_workflows: 5,
  total_executions: 42,
  success_rate: 0.95,
  avg_duration_ms: 1200,
  executions_by_status: { completed: 40, failed: 2 },
  recent_executions: [],
  top_failing_workflows: [],
};

let fetchMock: Mock;

function mockFetchResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  } as Response;
}

function mockFetch204(): Response {
  return {
    ok: true,
    status: 204,
    json: () => Promise.resolve(null),
    text: () => Promise.resolve(""),
  } as Response;
}

function mockFetchError(status: number, message: string): Response {
  return {
    ok: false,
    status,
    text: () => Promise.resolve(message),
  } as Response;
}

describe("api service", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  // ── Workflow CRUD ──────────────────────────────────────────────────

  describe("listWorkflows", () => {
    it("fetches all workflows", async () => {
      const workflows = [mockWorkflow];
      fetchMock.mockResolvedValue(mockFetchResponse(workflows));

      const result = await listWorkflows();

      expect(fetchMock).toHaveBeenCalledWith("/api/workflows/", {
        headers: { "Content-Type": "application/json" },
      });
      expect(result).toEqual(workflows);
    });
  });

  describe("getWorkflow", () => {
    it("fetches a single workflow by id", async () => {
      fetchMock.mockResolvedValue(mockFetchResponse(mockWorkflow));

      const result = await getWorkflow("wf-1");

      expect(fetchMock).toHaveBeenCalledWith("/api/workflows/wf-1", {
        headers: { "Content-Type": "application/json" },
      });
      expect(result).toEqual(mockWorkflow);
    });
  });

  describe("createWorkflow", () => {
    it("sends POST with workflow data", async () => {
      const input = { name: "New Workflow", description: "desc" };
      fetchMock.mockResolvedValue(
        mockFetchResponse({ ...mockWorkflow, ...input }),
      );

      const result = await createWorkflow(input);

      expect(fetchMock).toHaveBeenCalledWith("/api/workflows/", {
        headers: { "Content-Type": "application/json" },
        method: "POST",
        body: JSON.stringify(input),
      });
      expect(result.name).toBe("New Workflow");
    });
  });

  describe("updateWorkflow", () => {
    it("sends PATCH with partial workflow data", async () => {
      const patch = { name: "Updated" };
      const updated = { ...mockWorkflow, ...patch };
      fetchMock.mockResolvedValue(mockFetchResponse(updated));

      const result = await updateWorkflow("wf-1", patch);

      expect(fetchMock).toHaveBeenCalledWith("/api/workflows/wf-1", {
        headers: { "Content-Type": "application/json" },
        method: "PATCH",
        body: JSON.stringify(patch),
      });
      expect(result.name).toBe("Updated");
    });
  });

  describe("deleteWorkflow", () => {
    it("sends DELETE and handles 204 response", async () => {
      fetchMock.mockResolvedValue(mockFetch204());

      const result = await deleteWorkflow("wf-1");

      expect(fetchMock).toHaveBeenCalledWith("/api/workflows/wf-1", {
        headers: { "Content-Type": "application/json" },
        method: "DELETE",
      });
      expect(result).toBeUndefined();
    });
  });

  describe("executeWorkflow", () => {
    it("sends POST to execute endpoint", async () => {
      fetchMock.mockResolvedValue(mockFetchResponse(mockExecution));

      const result = await executeWorkflow("wf-1");

      expect(fetchMock).toHaveBeenCalledWith(
        "/api/workflows/wf-1/execute",
        {
          headers: { "Content-Type": "application/json" },
          method: "POST",
        },
      );
      expect(result).toEqual(mockExecution);
    });
  });

  // ── Executions ─────────────────────────────────────────────────────

  describe("listExecutions", () => {
    it("fetches all executions without filter", async () => {
      const executions = [mockExecution];
      fetchMock.mockResolvedValue(mockFetchResponse(executions));

      const result = await listExecutions();

      expect(fetchMock).toHaveBeenCalledWith("/api/tasks/executions", {
        headers: { "Content-Type": "application/json" },
      });
      expect(result).toEqual(executions);
    });

    it("appends status query parameter when provided", async () => {
      fetchMock.mockResolvedValue(mockFetchResponse([mockExecution]));

      await listExecutions("running");

      expect(fetchMock).toHaveBeenCalledWith(
        "/api/tasks/executions?status=running",
        { headers: { "Content-Type": "application/json" } },
      );
    });
  });

  describe("getExecution", () => {
    it("fetches a single execution by id", async () => {
      fetchMock.mockResolvedValue(mockFetchResponse(mockExecution));

      const result = await getExecution("exec-1");

      expect(fetchMock).toHaveBeenCalledWith(
        "/api/tasks/executions/exec-1",
        { headers: { "Content-Type": "application/json" } },
      );
      expect(result).toEqual(mockExecution);
    });
  });

  // ── Analytics ──────────────────────────────────────────────────────

  describe("getAnalyticsSummary", () => {
    it("fetches analytics with default days", async () => {
      fetchMock.mockResolvedValue(mockFetchResponse(mockAnalytics));

      const result = await getAnalyticsSummary();

      expect(fetchMock).toHaveBeenCalledWith(
        "/api/analytics/summary?days=30",
        { headers: { "Content-Type": "application/json" } },
      );
      expect(result).toEqual(mockAnalytics);
    });

    it("accepts custom days parameter", async () => {
      fetchMock.mockResolvedValue(mockFetchResponse(mockAnalytics));

      await getAnalyticsSummary(7);

      expect(fetchMock).toHaveBeenCalledWith(
        "/api/analytics/summary?days=7",
        { headers: { "Content-Type": "application/json" } },
      );
    });
  });

  describe("getTimeline", () => {
    it("fetches timeline with default parameters", async () => {
      const timeline = [
        { time: "2026-01-01T00:00:00Z", total: 10, completed: 8, failed: 2 },
      ];
      fetchMock.mockResolvedValue(mockFetchResponse(timeline));

      const result = await getTimeline();

      expect(fetchMock).toHaveBeenCalledWith(
        "/api/analytics/timeline?hours=24&bucket_minutes=60",
        { headers: { "Content-Type": "application/json" } },
      );
      expect(result).toEqual(timeline);
    });

    it("accepts custom hours and bucket_minutes", async () => {
      fetchMock.mockResolvedValue(mockFetchResponse([]));

      await getTimeline(48, 30);

      expect(fetchMock).toHaveBeenCalledWith(
        "/api/analytics/timeline?hours=48&bucket_minutes=30",
        { headers: { "Content-Type": "application/json" } },
      );
    });
  });

  // ── Error handling ─────────────────────────────────────────────────

  describe("error handling", () => {
    it("throws on 404 with status and body in message", async () => {
      fetchMock.mockResolvedValue(mockFetchError(404, "Not found"));

      await expect(getWorkflow("missing")).rejects.toThrow(
        "API error 404: Not found",
      );
    });

    it("throws on 500 server error", async () => {
      fetchMock.mockResolvedValue(
        mockFetchError(500, "Internal server error"),
      );

      await expect(listWorkflows()).rejects.toThrow(
        "API error 500: Internal server error",
      );
    });

    it("throws on 422 validation error", async () => {
      fetchMock.mockResolvedValue(
        mockFetchError(422, '{"detail":"validation failed"}'),
      );

      await expect(createWorkflow({ name: "" })).rejects.toThrow(
        'API error 422: {"detail":"validation failed"}',
      );
    });

    it("throws on 401 unauthorized", async () => {
      fetchMock.mockResolvedValue(mockFetchError(401, "Unauthorized"));

      await expect(listWorkflows()).rejects.toThrow(
        "API error 401: Unauthorized",
      );
    });
  });

  // ── 204 handling ───────────────────────────────────────────────────

  describe("204 No Content handling", () => {
    it("returns undefined for 204 responses", async () => {
      fetchMock.mockResolvedValue(mockFetch204());

      const result = await deleteWorkflow("wf-1");

      expect(result).toBeUndefined();
    });

    it("does not attempt to parse JSON for 204 responses", async () => {
      const jsonSpy = vi.fn();
      fetchMock.mockResolvedValue({
        ok: true,
        status: 204,
        json: jsonSpy,
        text: () => Promise.resolve(""),
      } as unknown as Response);

      await deleteWorkflow("wf-1");

      expect(jsonSpy).not.toHaveBeenCalled();
    });
  });
});
