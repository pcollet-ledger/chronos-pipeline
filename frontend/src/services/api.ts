import type {
  AnalyticsSummary,
  BulkDeleteResponse,
  ExecutionComparison,
  TimelineBucket,
  VersionSnapshot,
  Workflow,
  WorkflowCreatePayload,
  WorkflowExecution,
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

// Workflows
export function listWorkflows(tag?: string, search?: string): Promise<Workflow[]> {
  const params = new URLSearchParams();
  if (tag) params.set("tag", tag);
  if (search) params.set("search", search);
  const qs = params.toString();
  return request<Workflow[]>(`/workflows/${qs ? `?${qs}` : ""}`);
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
  data: Partial<Workflow>,
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

export function cloneWorkflow(id: string): Promise<Workflow> {
  return request<Workflow>(`/workflows/${id}/clone`, { method: "POST" });
}

export function addTags(id: string, tags: string[]): Promise<Workflow> {
  return request<Workflow>(`/workflows/${id}/tags`, {
    method: "POST",
    body: JSON.stringify({ tags }),
  });
}

export function removeTag(id: string, tag: string): Promise<Workflow> {
  return request<Workflow>(
    `/workflows/${id}/tags/${encodeURIComponent(tag)}`,
    { method: "DELETE" },
  );
}

export function getWorkflowHistory(
  id: string,
): Promise<VersionSnapshot[]> {
  return request<VersionSnapshot[]>(`/workflows/${id}/history`);
}

export function getWorkflowVersion(
  id: string,
  version: number,
): Promise<VersionSnapshot> {
  return request<VersionSnapshot>(`/workflows/${id}/history/${version}`);
}

export function compareExecutions(
  idA: string,
  idB: string,
): Promise<ExecutionComparison> {
  return request<ExecutionComparison>(
    `/tasks/executions/compare?ids=${encodeURIComponent(idA)},${encodeURIComponent(idB)}`,
  );
}

// Executions
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

// Analytics
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
