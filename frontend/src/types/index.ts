export interface TaskDefinition {
  id: string;
  name: string;
  description: string;
  action: string;
  parameters: Record<string, unknown>;
  depends_on: string[];
  timeout_seconds: number;
  retry_count: number;
  priority: "low" | "medium" | "high" | "critical";
  /** Action name executed before the main action. `null` means no pre-hook. */
  pre_hook: string | null;
  /** Action name executed after the main action. `null` means no post-hook. */
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

export type WorkflowStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface Workflow {
  id: string;
  name: string;
  description: string;
  tasks: TaskDefinition[];
  schedule: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: WorkflowStatus;
  started_at: string | null;
  completed_at: string | null;
  task_results: TaskResult[];
  trigger: string;
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
