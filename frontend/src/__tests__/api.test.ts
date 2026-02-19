import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  listWorkflows,
  getWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  bulkDeleteWorkflows,
  executeWorkflow,
  listWorkflowExecutions,
  dryRunWorkflow,
  cloneWorkflow,
  addTags,
  removeTag,
  getWorkflowHistory,
  getWorkflowVersion,
  compareExecutions,
  listExecutions,
  getExecution,
  retryExecution,
  cancelExecution,
  getAnalyticsSummary,
  getWorkflowStats,
  getTimeline,
} from "../services/api";

const mockFetch = vi.fn();

beforeEach(() => {
  globalThis.fetch = mockFetch;
});

afterEach(() => {
  vi.restoreAllMocks();
});

function mockResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  };
}

describe("api service", () => {
  describe("listWorkflows", () => {
    it("calls GET /api/workflows/ with no params", async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await listWorkflows();
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/", expect.any(Object));
    });

    it("passes tag parameter", async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await listWorkflows({ tag: "prod" });
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("tag=prod");
    });

    it("passes search parameter", async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await listWorkflows({ search: "test" });
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("search=test");
    });

    it("passes limit and offset", async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await listWorkflows({ limit: 10, offset: 5 });
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("limit=10");
      expect(url).toContain("offset=5");
    });
  });

  describe("getWorkflow", () => {
    it("calls GET /api/workflows/:id", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "wf-1" }));
      await getWorkflow("wf-1");
      expect(mockFetch).toHaveBeenCalledWith("/api/workflows/wf-1", expect.any(Object));
    });
  });

  describe("createWorkflow", () => {
    it("calls POST /api/workflows/", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "wf-new" }));
      await createWorkflow({ name: "Test" });
      const [, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(opts.method).toBe("POST");
    });
  });

  describe("updateWorkflow", () => {
    it("calls PATCH /api/workflows/:id", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "wf-1" }));
      await updateWorkflow("wf-1", { name: "Updated" });
      const [, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(opts.method).toBe("PATCH");
    });
  });

  describe("deleteWorkflow", () => {
    it("calls DELETE /api/workflows/:id", async () => {
      mockFetch.mockResolvedValue(mockResponse(undefined, 204));
      await deleteWorkflow("wf-1");
      const [, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(opts.method).toBe("DELETE");
    });
  });

  describe("bulkDeleteWorkflows", () => {
    it("calls POST /api/workflows/bulk-delete", async () => {
      mockFetch.mockResolvedValue(mockResponse({ deleted: 2 }));
      await bulkDeleteWorkflows(["a", "b"]);
      const [url, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("bulk-delete");
      expect(opts.method).toBe("POST");
    });
  });

  describe("executeWorkflow", () => {
    it("calls POST with trigger param", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "ex-1" }));
      await executeWorkflow("wf-1", "scheduled");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("trigger=scheduled");
    });
  });

  describe("listWorkflowExecutions", () => {
    it("calls GET with limit", async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await listWorkflowExecutions("wf-1", 10);
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("limit=10");
    });
  });

  describe("dryRunWorkflow", () => {
    it("calls POST /api/workflows/:id/dry-run", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "dry-1" }));
      await dryRunWorkflow("wf-1");
      const [url, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("dry-run");
      expect(opts.method).toBe("POST");
    });
  });

  describe("cloneWorkflow", () => {
    it("calls POST /api/workflows/:id/clone", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "wf-clone" }));
      await cloneWorkflow("wf-1");
      const [url, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("clone");
      expect(opts.method).toBe("POST");
    });
  });

  describe("addTags", () => {
    it("calls POST /api/workflows/:id/tags", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "wf-1" }));
      await addTags("wf-1", ["prod"]);
      const [url, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/tags");
      expect(opts.method).toBe("POST");
    });
  });

  describe("removeTag", () => {
    it("calls DELETE /api/workflows/:id/tags/:tag", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "wf-1" }));
      await removeTag("wf-1", "prod");
      const [url, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/tags/prod");
      expect(opts.method).toBe("DELETE");
    });
  });

  describe("getWorkflowHistory", () => {
    it("calls GET /api/workflows/:id/history", async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await getWorkflowHistory("wf-1");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/history");
    });
  });

  describe("getWorkflowVersion", () => {
    it("calls GET /api/workflows/:id/history/:version", async () => {
      mockFetch.mockResolvedValue(mockResponse({}));
      await getWorkflowVersion("wf-1", 2);
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/history/2");
    });
  });

  describe("compareExecutions", () => {
    it("calls GET /api/tasks/executions/compare", async () => {
      mockFetch.mockResolvedValue(mockResponse({}));
      await compareExecutions("a", "b");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("compare");
      expect(url).toContain("a");
      expect(url).toContain("b");
    });
  });

  describe("listExecutions", () => {
    it("calls GET /api/tasks/executions", async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await listExecutions();
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/tasks/executions");
    });

    it("passes status filter", async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await listExecutions("completed");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("status=completed");
    });
  });

  describe("getExecution", () => {
    it("calls GET /api/tasks/executions/:id", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "ex-1" }));
      await getExecution("ex-1");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/tasks/executions/ex-1");
    });
  });

  describe("retryExecution", () => {
    it("calls POST /api/tasks/executions/:id/retry", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "ex-1" }));
      await retryExecution("ex-1");
      const [url, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/retry");
      expect(opts.method).toBe("POST");
    });
  });

  describe("cancelExecution", () => {
    it("calls POST /api/tasks/executions/:id/cancel", async () => {
      mockFetch.mockResolvedValue(mockResponse({ id: "ex-1" }));
      await cancelExecution("ex-1");
      const [url, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain("/cancel");
      expect(opts.method).toBe("POST");
    });
  });

  describe("getAnalyticsSummary", () => {
    it("calls GET /api/analytics/summary", async () => {
      mockFetch.mockResolvedValue(mockResponse({}));
      await getAnalyticsSummary();
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/analytics/summary");
    });
  });

  describe("getWorkflowStats", () => {
    it("calls GET /api/analytics/workflows/:id/stats", async () => {
      mockFetch.mockResolvedValue(mockResponse({}));
      await getWorkflowStats("wf-1");
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/analytics/workflows/wf-1/stats");
    });
  });

  describe("getTimeline", () => {
    it("calls GET /api/analytics/timeline", async () => {
      mockFetch.mockResolvedValue(mockResponse([]));
      await getTimeline();
      const url = mockFetch.mock.calls[0]?.[0] as string;
      expect(url).toContain("/analytics/timeline");
    });
  });

  describe("error handling", () => {
    it("throws on non-ok response", async () => {
      mockFetch.mockResolvedValue(mockResponse("not found", 404));
      await expect(getWorkflow("bad-id")).rejects.toThrow("API error 404");
    });

    it("throws on 500 response", async () => {
      mockFetch.mockResolvedValue(mockResponse("server error", 500));
      await expect(listWorkflows()).rejects.toThrow("API error 500");
    });
  });
});
