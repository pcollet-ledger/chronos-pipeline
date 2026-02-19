import type {
  AnalyticsSummary,
  BulkDeleteResponse,
  ErrorResponse,
  Workflow,
  WorkflowExecution,
} from "../types";

const BASE = "/api";

/**
 * Parse a non-OK response into an Error with a descriptive message.
 *
 * Attempts to extract the structured `{detail, code}` body returned by
 * the backend exception handlers.  Falls back to the raw response text
 * when the body is not valid JSON.
 */
async function parseApiError(resp: Response): Promise<Error> {
  let detail: string;
  try {
    const body: ErrorResponse | { detail: string } = await resp.json();
    detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body);
  } catch {
    detail = await resp.text().catch(() => "Unknown error");
  }
  return new Error(`API error ${resp.status}: ${detail}`);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    throw await parseApiError(resp);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

// Workflows
export const listWorkflows = () => request<Workflow[]>("/workflows/");

export const getWorkflow = (id: string) => request<Workflow>(`/workflows/${id}`);

export const createWorkflow = (data: Partial<Workflow>) =>
  request<Workflow>("/workflows/", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateWorkflow = (id: string, data: Partial<Workflow>) =>
  request<Workflow>(`/workflows/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteWorkflow = (id: string) =>
  request<void>(`/workflows/${id}`, { method: "DELETE" });

export const bulkDeleteWorkflows = (ids: string[]) =>
  request<BulkDeleteResponse>("/workflows/bulk-delete", {
    method: "POST",
    body: JSON.stringify({ ids }),
  });

export const executeWorkflow = (id: string) =>
  request<WorkflowExecution>(`/workflows/${id}/execute`, { method: "POST" });

// Executions
export const listExecutions = (status?: string) => {
  const params = status ? `?status=${status}` : "";
  return request<WorkflowExecution[]>(`/tasks/executions${params}`);
};

export const getExecution = (id: string) =>
  request<WorkflowExecution>(`/tasks/executions/${id}`);

export const retryExecution = (id: string) =>
  request<WorkflowExecution>(`/tasks/executions/${id}/retry`, { method: "POST" });

// Analytics
export const getAnalyticsSummary = (days = 30) =>
  request<AnalyticsSummary>(`/analytics/summary?days=${days}`);

export const getTimeline = (hours = 24, bucketMinutes = 60) =>
  request<Array<{ time: string; total: number; completed: number; failed: number }>>(
    `/analytics/timeline?hours=${hours}&bucket_minutes=${bucketMinutes}`
  );
