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

/** Valid action names recognised by the workflow engine. */
export type ActionName = "log" | "transform" | "validate" | "notify" | "aggregate";

/** All valid action names as a runtime array for dropdowns / validation. */
export const ACTION_NAMES: readonly ActionName[] = [
  "log",
  "transform",
  "validate",
  "notify",
  "aggregate",
] as const;

/** Priority options as a runtime array for dropdowns. */
export const PRIORITY_OPTIONS: readonly TaskDefinition["priority"][] = [
  "low",
  "medium",
  "high",
  "critical",
] as const;

/** Shape of a single task entry in the workflow creation form. */
export interface TaskFormEntry {
  name: string;
  action: ActionName;
  parameters: Record<string, string>;
  depends_on: string[];
  pre_hook: string;
  post_hook: string;
  priority: TaskDefinition["priority"];
}

/** Shape of a task as sent to the API (hooks are nullable, not all fields required). */
export interface TaskSubmitEntry {
  name: string;
  action: string;
  parameters: Record<string, string>;
  depends_on: string[];
  priority: TaskDefinition["priority"];
  pre_hook: string | null;
  post_hook: string | null;
}

/** Payload sent to POST /api/workflows/ or PATCH /api/workflows/:id. */
export interface WorkflowFormData {
  name: string;
  description: string;
  tags: string[];
  tasks: TaskSubmitEntry[];
  schedule?: string | null;
}

/** Per-field validation errors surfaced by the form. */
export interface WorkflowFormErrors {
  name?: string;
  description?: string;
  tags?: string;
  tasks?: string;
  taskErrors?: Record<number, TaskFieldErrors>;
}

/** Per-field validation errors for a single task entry. */
export interface TaskFieldErrors {
  name?: string;
  action?: string;
  parameters?: string;
  depends_on?: string;
}
