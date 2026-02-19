import type {
  AnalyticsSummary,
  BulkDeleteResponse,
  ExecutionComparison,
  TagsPayload,
  TimelineBucket,
  Workflow,
  WorkflowCreatePayload,
  WorkflowExecution,
  WorkflowUpdatePayload,
} from "../types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API error ${resp.status}: ${text}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Workflows – CRUD
// ---------------------------------------------------------------------------

export function listWorkflows(params?: {
  tag?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<Workflow[]> {
  const qs = new URLSearchParams();
  if (params?.tag) qs.set("tag", params.tag);
  if (params?.search) qs.set("search", params.search);
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));
  if (params?.offset !== undefined) qs.set("offset", String(params.offset));
  const q = qs.toString();
  return request<Workflow[]>(`/workflows/${q ? `?${q}` : ""}`);
}

export function getWorkflow(id: string): Promise<Workflow> {
  return request<Workflow>(`/workflows/${id}`);
}

export function createWorkflow(data: WorkflowCreatePayload): Promise<Workflow> {
  return request<Workflow>("/workflows/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateWorkflow(
  id: string,
  data: WorkflowUpdatePayload,
): Promise<Workflow> {
  return request<Workflow>(`/workflows/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteWorkflow(id: string): Promise<void> {
  return request<void>(`/workflows/${id}`, { method: "DELETE" });
}

export function bulkDeleteWorkflows(ids: string[]): Promise<BulkDeleteResponse> {
  return request<BulkDeleteResponse>("/workflows/bulk-delete", {
    method: "POST",
    body: JSON.stringify({ ids }),
  });
}

// ---------------------------------------------------------------------------
// Workflows – Execution
// ---------------------------------------------------------------------------

export function executeWorkflow(
  id: string,
  trigger = "manual",
): Promise<WorkflowExecution> {
  return request<WorkflowExecution>(
    `/workflows/${id}/execute?trigger=${encodeURIComponent(trigger)}`,
    { method: "POST" },
  );
}

export function listWorkflowExecutions(
  workflowId: string,
  limit = 50,
): Promise<WorkflowExecution[]> {
  return request<WorkflowExecution[]>(
    `/workflows/${workflowId}/executions?limit=${limit}`,
  );
}

export function dryRunWorkflow(id: string): Promise<WorkflowExecution> {
  return request<WorkflowExecution>(`/workflows/${id}/dry-run`, {
    method: "POST",
  });
}

// ---------------------------------------------------------------------------
// Workflows – Tagging
// ---------------------------------------------------------------------------

export function addTags(workflowId: string, tags: string[]): Promise<Workflow> {
  const body: TagsPayload = { tags };
  return request<Workflow>(`/workflows/${workflowId}/tags`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function removeTag(workflowId: string, tag: string): Promise<Workflow> {
  return request<Workflow>(
    `/workflows/${workflowId}/tags/${encodeURIComponent(tag)}`,
    { method: "DELETE" },
  );
}

// ---------------------------------------------------------------------------
// Workflows – History / Versioning / Cloning
// ---------------------------------------------------------------------------

export function getWorkflowHistory(workflowId: string): Promise<Workflow[]> {
  return request<Workflow[]>(`/workflows/${workflowId}/history`);
}

export function getWorkflowVersion(
  workflowId: string,
  version: number,
): Promise<Workflow> {
  return request<Workflow>(`/workflows/${workflowId}/history/${version}`);
}

export function cloneWorkflow(id: string): Promise<Workflow> {
  return request<Workflow>(`/workflows/${id}/clone`, { method: "POST" });
}

// ---------------------------------------------------------------------------
// Executions (task-level routes)
// ---------------------------------------------------------------------------

export function listExecutions(status?: string): Promise<WorkflowExecution[]> {
  const params = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<WorkflowExecution[]>(`/tasks/executions${params}`);
}

export function getExecution(id: string): Promise<WorkflowExecution> {
  return request<WorkflowExecution>(`/tasks/executions/${id}`);
}

export function retryExecution(id: string): Promise<WorkflowExecution> {
  return request<WorkflowExecution>(`/tasks/executions/${id}/retry`, {
    method: "POST",
  });
}

export function cancelExecution(id: string): Promise<WorkflowExecution> {
  return request<WorkflowExecution>(`/tasks/executions/${id}/cancel`, {
    method: "POST",
  });
}

export function compareExecutions(
  idA: string,
  idB: string,
): Promise<ExecutionComparison> {
  return request<ExecutionComparison>(
    `/tasks/executions/compare?ids=${encodeURIComponent(`${idA},${idB}`)}`,
  );
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export function getAnalyticsSummary(days = 30): Promise<AnalyticsSummary> {
  return request<AnalyticsSummary>(`/analytics/summary?days=${days}`);
}

export function getWorkflowStats(
  workflowId: string,
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(
    `/analytics/workflows/${workflowId}/stats`,
  );
}

export function getTimeline(
  hours = 24,
  bucketMinutes = 60,
): Promise<TimelineBucket[]> {
  return request<TimelineBucket[]>(
    `/analytics/timeline?hours=${hours}&bucket_minutes=${bucketMinutes}`,
  );
}
