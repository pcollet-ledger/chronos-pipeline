import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as api from "../services/api";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  });
}

function noContentResponse() {
  return Promise.resolve({
    ok: true,
    status: 204,
    json: () => Promise.resolve(undefined),
    text: () => Promise.resolve(""),
  });
}

function errorResponse(status: number, body: string) {
  return Promise.resolve({
    ok: false,
    status,
    text: () => Promise.resolve(body),
    json: () => Promise.resolve({ detail: body }),
  });
}

describe("api service", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("listWorkflows", () => {
    it("fetches workflows without filters", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse([]));
      const result = await api.listWorkflows();
      expect(result).toEqual([]);
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/", expect.objectContaining({
        headers: { "Content-Type": "application/json" },
      }));
    });

    it("includes tag query parameter", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse([]));
      await api.listWorkflows("etl");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("tag=etl");
    });

    it("includes search query parameter", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse([]));
      await api.listWorkflows(undefined, "test");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("search=test");
    });

    it("includes both tag and search", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse([]));
      await api.listWorkflows("prod", "daily");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("tag=prod");
      expect(url).toContain("search=daily");
    });
  });

  describe("getWorkflow", () => {
    it("fetches a single workflow by ID", async () => {
      const wf = { id: "abc", name: "Test" };
      mockFetch.mockReturnValueOnce(jsonResponse(wf));
      const result = await api.getWorkflow("abc");
      expect(result).toEqual(wf);
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toBe("/api/workflows/abc");
    });
  });

  describe("createWorkflow", () => {
    it("sends POST with workflow data", async () => {
      const payload = { name: "New WF" };
      const created = { id: "123", name: "New WF" };
      mockFetch.mockReturnValueOnce(jsonResponse(created));
      const result = await api.createWorkflow(payload);
      expect(result).toEqual(created);
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/", expect.objectContaining({
        method: "POST",
        body: JSON.stringify(payload),
      }));
    });
  });

  describe("updateWorkflow", () => {
    it("sends PATCH with partial data", async () => {
      const updated = { id: "abc", name: "Updated" };
      mockFetch.mockReturnValueOnce(jsonResponse(updated));
      const result = await api.updateWorkflow("abc", { name: "Updated" });
      expect(result).toEqual(updated);
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/abc", expect.objectContaining({
        method: "PATCH",
      }));
    });
  });

  describe("deleteWorkflow", () => {
    it("sends DELETE and handles 204", async () => {
      mockFetch.mockReturnValueOnce(noContentResponse());
      await api.deleteWorkflow("abc");
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/abc", expect.objectContaining({
        method: "DELETE",
      }));
    });
  });

  describe("bulkDeleteWorkflows", () => {
    it("sends POST with list of IDs", async () => {
      const resp = { deleted: 2, not_found: 0, deleted_ids: ["a", "b"], not_found_ids: [] };
      mockFetch.mockReturnValueOnce(jsonResponse(resp));
      const result = await api.bulkDeleteWorkflows(["a", "b"]);
      expect(result.deleted).toBe(2);
    });
  });

  describe("executeWorkflow", () => {
    it("sends POST to execute endpoint", async () => {
      const exec = { id: "e1", status: "completed" };
      mockFetch.mockReturnValueOnce(jsonResponse(exec));
      const result = await api.executeWorkflow("wf1");
      expect(result).toEqual(exec);
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/workflows/wf1/execute");
      expect(url).toContain("trigger=manual");
    });

    it("passes custom trigger", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ id: "e2" }));
      await api.executeWorkflow("wf1", "scheduled");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("trigger=scheduled");
    });
  });

  describe("listWorkflowExecutions", () => {
    it("fetches executions for a workflow", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse([]));
      await api.listWorkflowExecutions("wf1", 10);
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/workflows/wf1/executions");
      expect(url).toContain("limit=10");
    });
  });

  describe("listExecutions", () => {
    it("fetches all executions without filter", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse([]));
      await api.listExecutions();
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toBe("/api/tasks/executions");
    });

    it("includes status filter", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse([]));
      await api.listExecutions("failed");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("status=failed");
    });
  });

  describe("getExecution", () => {
    it("fetches a single execution", async () => {
      const exec = { id: "e1" };
      mockFetch.mockReturnValueOnce(jsonResponse(exec));
      const result = await api.getExecution("e1");
      expect(result).toEqual(exec);
    });
  });

  describe("retryExecution", () => {
    it("sends POST to retry endpoint", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ id: "e2" }));
      await api.retryExecution("e1");
      expect(mockFetch).toHaveBeenCalledWith("/api/tasks/executions/e1/retry", expect.objectContaining({
        method: "POST",
      }));
    });
  });

  describe("cancelExecution", () => {
    it("sends POST to cancel endpoint", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ id: "e1", status: "cancelled" }));
      await api.cancelExecution("e1");
      expect(mockFetch).toHaveBeenCalledWith("/api/tasks/executions/e1/cancel", expect.objectContaining({
        method: "POST",
      }));
    });
  });

  describe("analytics", () => {
    it("getAnalyticsSummary fetches with days param", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ total_workflows: 5 }));
      await api.getAnalyticsSummary(7);
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("days=7");
    });

    it("getWorkflowStats fetches stats for a workflow", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ workflow_id: "wf1" }));
      await api.getWorkflowStats("wf1");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/analytics/workflows/wf1/stats");
    });

    it("getTimeline fetches with hours and bucket params", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse([]));
      await api.getTimeline(12, 30);
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("hours=12");
      expect(url).toContain("bucket_minutes=30");
    });
  });

  describe("versioning", () => {
    it("getWorkflowHistory fetches version history", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse([]));
      await api.getWorkflowHistory("wf1");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/workflows/wf1/history");
    });

    it("getWorkflowVersion fetches specific version", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ version: 2 }));
      await api.getWorkflowVersion("wf1", 2);
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/workflows/wf1/history/2");
    });
  });

  describe("cloneWorkflow", () => {
    it("sends POST to clone endpoint", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ id: "cloned" }));
      await api.cloneWorkflow("wf1");
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/wf1/clone", expect.objectContaining({
        method: "POST",
      }));
    });
  });

  describe("dryRunWorkflow", () => {
    it("sends POST to dry-run endpoint", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ id: "dr1" }));
      await api.dryRunWorkflow("wf1");
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/wf1/dry-run", expect.objectContaining({
        method: "POST",
      }));
    });
  });

  describe("tags", () => {
    it("addTags sends POST with tags array", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ id: "wf1", tags: ["a", "b"] }));
      await api.addTags("wf1", ["a", "b"]);
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/wf1/tags", expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ tags: ["a", "b"] }),
      }));
    });

    it("removeTag sends DELETE for specific tag", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ id: "wf1", tags: [] }));
      await api.removeTag("wf1", "old-tag");
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/wf1/tags/old-tag", expect.objectContaining({
        method: "DELETE",
      }));
    });
  });

  describe("compareExecutions", () => {
    it("sends GET with comma-separated IDs", async () => {
      mockFetch.mockReturnValueOnce(jsonResponse({ workflow_id: "wf1" }));
      await api.compareExecutions("e1", "e2");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("ids=e1");
      expect(url).toContain("e2");
    });
  });

  describe("error handling", () => {
    it("throws on non-ok response", async () => {
      mockFetch.mockReturnValueOnce(errorResponse(404, "Not found"));
      await expect(api.getWorkflow("bad-id")).rejects.toThrow("API error 404");
    });

    it("throws on 500 response", async () => {
      mockFetch.mockReturnValueOnce(errorResponse(500, "Internal error"));
      await expect(api.listWorkflows()).rejects.toThrow("API error 500");
    });

    it("includes response body in error message", async () => {
      mockFetch.mockReturnValueOnce(errorResponse(400, "Bad request body"));
      await expect(api.createWorkflow({ name: "" })).rejects.toThrow("Bad request body");
    });
  });
});
