import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  listWorkflows,
  getWorkflow,
  createWorkflow,
  updateWorkflow,
  deleteWorkflow,
  bulkDeleteWorkflows,
  executeWorkflow,
  dryRunWorkflow,
  addTags,
  removeTag,
  getWorkflowHistory,
  getWorkflowVersion,
  cloneWorkflow,
  listExecutions,
  getExecution,
  retryExecution,
  cancelExecution,
  compareExecutions,
  getAnalyticsSummary,
  listWorkflowExecutions,
} from "../services/api";

const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

function jsonResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  };
}

function noContentResponse() {
  return { ok: true, status: 204, json: () => Promise.resolve(undefined), text: () => Promise.resolve("") };
}

describe("api", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("listWorkflows calls correct URL", async () => {
    mockFetch.mockResolvedValue(jsonResponse([]));
    await listWorkflows();
    expect(mockFetch).toHaveBeenCalledWith("/api/workflows/", expect.any(Object));
  });

  it("listWorkflows with search param", async () => {
    mockFetch.mockResolvedValue(jsonResponse([]));
    await listWorkflows({ search: "test" });
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("search=test");
  });

  it("listWorkflows with tag param", async () => {
    mockFetch.mockResolvedValue(jsonResponse([]));
    await listWorkflows({ tag: "prod" });
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("tag=prod");
  });

  it("getWorkflow calls correct URL", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "wf-1" }));
    await getWorkflow("wf-1");
    expect(mockFetch).toHaveBeenCalledWith("/api/workflows/wf-1", expect.any(Object));
  });

  it("createWorkflow sends POST", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "wf-new" }));
    await createWorkflow({ name: "New WF" });
    const opts = mockFetch.mock.calls[0]?.[1] as RequestInit;
    expect(opts.method).toBe("POST");
  });

  it("updateWorkflow sends PATCH", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "wf-1" }));
    await updateWorkflow("wf-1", { name: "Updated" });
    const opts = mockFetch.mock.calls[0]?.[1] as RequestInit;
    expect(opts.method).toBe("PATCH");
  });

  it("deleteWorkflow sends DELETE", async () => {
    mockFetch.mockResolvedValue(noContentResponse());
    await deleteWorkflow("wf-1");
    const opts = mockFetch.mock.calls[0]?.[1] as RequestInit;
    expect(opts.method).toBe("DELETE");
  });

  it("bulkDeleteWorkflows sends POST with ids", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ deleted: 2 }));
    await bulkDeleteWorkflows(["a", "b"]);
    const opts = mockFetch.mock.calls[0]?.[1] as RequestInit;
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body as string)).toEqual({ ids: ["a", "b"] });
  });

  it("executeWorkflow sends POST", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "exec-1" }));
    await executeWorkflow("wf-1");
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("/execute");
  });

  it("dryRunWorkflow sends POST", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "dry-1" }));
    await dryRunWorkflow("wf-1");
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("/dry-run");
  });

  it("addTags sends POST with tags body", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "wf-1" }));
    await addTags("wf-1", ["a", "b"]);
    const opts = mockFetch.mock.calls[0]?.[1] as RequestInit;
    expect(JSON.parse(opts.body as string)).toEqual({ tags: ["a", "b"] });
  });

  it("removeTag sends DELETE", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "wf-1" }));
    await removeTag("wf-1", "old");
    const opts = mockFetch.mock.calls[0]?.[1] as RequestInit;
    expect(opts.method).toBe("DELETE");
  });

  it("getWorkflowHistory calls correct URL", async () => {
    mockFetch.mockResolvedValue(jsonResponse([]));
    await getWorkflowHistory("wf-1");
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("/history");
  });

  it("getWorkflowVersion calls correct URL", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "wf-1" }));
    await getWorkflowVersion("wf-1", 2);
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("/history/2");
  });

  it("cloneWorkflow sends POST", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "wf-clone" }));
    await cloneWorkflow("wf-1");
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("/clone");
  });

  it("listExecutions calls tasks endpoint", async () => {
    mockFetch.mockResolvedValue(jsonResponse([]));
    await listExecutions();
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("/tasks/executions");
  });

  it("getExecution calls correct URL", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "exec-1" }));
    await getExecution("exec-1");
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("/tasks/executions/exec-1");
  });

  it("retryExecution sends POST", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "exec-1" }));
    await retryExecution("exec-1");
    const opts = mockFetch.mock.calls[0]?.[1] as RequestInit;
    expect(opts.method).toBe("POST");
  });

  it("cancelExecution sends POST", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "exec-1" }));
    await cancelExecution("exec-1");
    const opts = mockFetch.mock.calls[0]?.[1] as RequestInit;
    expect(opts.method).toBe("POST");
  });

  it("compareExecutions calls correct URL with ids", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ workflow_id: "wf-1" }));
    await compareExecutions("a", "b");
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("compare");
    expect(url).toContain("a%2Cb");
  });

  it("getAnalyticsSummary calls correct URL", async () => {
    mockFetch.mockResolvedValue(jsonResponse({}));
    await getAnalyticsSummary(7);
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("days=7");
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ detail: "Not found" }, 404));
    await expect(getWorkflow("bad")).rejects.toThrow("API error 404");
  });

  it("listWorkflowExecutions calls correct URL", async () => {
    mockFetch.mockResolvedValue(jsonResponse([]));
    await listWorkflowExecutions("wf-1", 10);
    const url = mockFetch.mock.calls[0]?.[0] as string;
    expect(url).toContain("/workflows/wf-1/executions?limit=10");
  });
});
