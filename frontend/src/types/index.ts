export type TaskPriority = "low" | "medium" | "high" | "critical";

export type WorkflowStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type ValidAction = "log" | "transform" | "validate" | "notify" | "aggregate";

export interface TaskDefinition {
  id: string;
  name: string;
  description: string;
  action: string;
  parameters: Record<string, unknown>;
  depends_on: string[];
  timeout_seconds: number;
  retry_count: number;
  priority: TaskPriority;
  pre_hook: string | null;
  post_hook: string | null;
}

export interface TaskResult {
  task_id: string;
  status: WorkflowStatus;
  started_at: string | null;
  completed_at: string | null;
  output: Record<string, unknown> | null;
  error: string | null;
  duration_ms: number | null;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  tasks: TaskDefinition[];
  schedule: string | null;
  tags: string[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface WorkflowCreatePayload {
  name: string;
  description?: string;
  tasks?: Array<Partial<TaskDefinition> & { name: string; action: string }>;
  schedule?: string | null;
  tags?: string[];
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: WorkflowStatus;
  started_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  task_results: TaskResult[];
  trigger: string;
  metadata: Record<string, unknown>;
}

export interface BulkDeleteResponse {
  deleted: number;
  not_found: number;
  deleted_ids: string[];
  not_found_ids: string[];
}

export interface AnalyticsSummary {
  total_workflows: number;
  total_executions: number;
  success_rate: number;
  avg_duration_ms: number;
  executions_by_status: Record<string, number>;
  recent_executions: WorkflowExecution[];
  top_failing_workflows: Array<{
    workflow_id: string;
    failures: number;
    total: number;
    failure_rate: number;
  }>;
}

export interface TimelineBucket {
  time: string;
  total: number;
  completed: number;
  failed: number;
}

export interface ExecutionComparison {
  workflow_id: string;
  executions: [WorkflowExecution, WorkflowExecution];
  task_comparison: Array<{
    task_id: string;
    status_a: string;
    status_b: string;
    duration_diff_ms: number;
  }>;
  summary: {
    improved_count: number;
    regressed_count: number;
    unchanged_count: number;
  };
}

export interface WorkflowStats {
  workflow_id: string;
  total_executions: number;
  completed: number;
  failed: number;
  success_rate: number;
  avg_duration_ms: number;
  min_duration_ms: number;
  max_duration_ms: number;
}
