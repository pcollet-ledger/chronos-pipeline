import { useCallback, useEffect, useState } from "react";
import type { WorkflowExecution } from "../types";
import { listExecutions, listWorkflowExecutions } from "../services/api";

interface UseExecutionsOptions {
  workflowId?: string;
  status?: string;
  limit?: number;
  autoFetch?: boolean;
}

interface UseExecutionsResult {
  executions: WorkflowExecution[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useExecutions(options: UseExecutionsOptions = {}): UseExecutionsResult {
  const { workflowId, status, limit = 50, autoFetch = true } = options;
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = workflowId
        ? await listWorkflowExecutions(workflowId, limit)
        : await listExecutions(status);
      setExecutions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load executions");
    } finally {
      setLoading(false);
    }
  }, [workflowId, status, limit]);

  useEffect(() => {
    if (autoFetch) {
      void refresh();
    }
  }, [autoFetch, refresh]);

  return { executions, loading, error, refresh };
}
