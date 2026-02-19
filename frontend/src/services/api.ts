import type {
  AnalyticsSummary,
  BulkDeleteResponse,
  Workflow,
  WorkflowExecution,
  WorkflowFormData,
} from "../types";

const BASE = "/api";

/**
 * Generic fetch wrapper that handles JSON serialisation, error mapping, and
 * 204 No Content responses.
 */
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
  return resp.json();
}

// ---- Workflows ------------------------------------------------------------

export const listWorkflows = (): Promise<Workflow[]> =>
  request<Workflow[]>("/workflows/");

export const getWorkflow = (id: string): Promise<Workflow> =>
  request<Workflow>(`/workflows/${id}`);

export const createWorkflow = (data: Partial<Workflow> | WorkflowFormData): Promise<Workflow> =>
  request<Workflow>("/workflows/", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateWorkflow = (
  id: string,
  data: Partial<Workflow> | WorkflowFormData,
): Promise<Workflow> =>
  request<Workflow>(`/workflows/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteWorkflow = (id: string): Promise<void> =>
  request<void>(`/workflows/${id}`, { method: "DELETE" });

export const bulkDeleteWorkflows = (ids: string[]): Promise<BulkDeleteResponse> =>
  request<BulkDeleteResponse>("/workflows/bulk-delete", {
    method: "POST",
    body: JSON.stringify({ ids }),
  });

export const executeWorkflow = (id: string): Promise<WorkflowExecution> =>
  request<WorkflowExecution>(`/workflows/${id}/execute`, { method: "POST" });

// ---- Executions -----------------------------------------------------------

export const listExecutions = (status?: string): Promise<WorkflowExecution[]> => {
  const params = status ? `?status=${status}` : "";
  return request<WorkflowExecution[]>(`/tasks/executions${params}`);
};

export const getExecution = (id: string): Promise<WorkflowExecution> =>
  request<WorkflowExecution>(`/tasks/executions/${id}`);

export const retryExecution = (id: string): Promise<WorkflowExecution> =>
  request<WorkflowExecution>(`/tasks/executions/${id}/retry`, {
    method: "POST",
  });

// ---- Analytics ------------------------------------------------------------

export const getAnalyticsSummary = (days = 30): Promise<AnalyticsSummary> =>
  request<AnalyticsSummary>(`/analytics/summary?days=${days}`);

export const getTimeline = (
  hours = 24,
  bucketMinutes = 60,
): Promise<Array<{ time: string; total: number; completed: number; failed: number }>> =>
  request<Array<{ time: string; total: number; completed: number; failed: number }>>(
    `/analytics/timeline?hours=${hours}&bucket_minutes=${bucketMinutes}`,
  );
