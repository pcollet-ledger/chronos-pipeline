import { useCallback, useEffect, useState } from "react";
import type { WorkflowExecution } from "../types";
import * as api from "../services/api";

interface UseExecutionsResult {
  executions: WorkflowExecution[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useExecutions(status?: string): UseExecutionsResult {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .listExecutions(status)
      .then(setExecutions)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [status]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { executions, loading, error, refresh };
}
