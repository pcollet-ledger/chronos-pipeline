import { useCallback, useEffect, useState } from "react";
import type { WorkflowExecution } from "../types";
import { listExecutions } from "../services/api";

interface UseExecutionsOptions {
  status?: string;
}

interface UseExecutionsReturn {
  executions: WorkflowExecution[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useExecutions(
  options: UseExecutionsOptions = {},
): UseExecutionsReturn {
  const { status } = options;
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listExecutions(status);
      setExecutions(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load executions",
      );
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    void load();
  }, [load]);

  return { executions, loading, error, refresh: () => void load() };
}
