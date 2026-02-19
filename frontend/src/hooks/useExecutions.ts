/**
 * Custom hook for execution API calls with loading/error/data state.
 */

import { useCallback, useEffect, useState } from "react";
import type { WorkflowExecution } from "../types";
import { listExecutions } from "../services/api";

interface UseExecutionsResult {
  data: WorkflowExecution[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useExecutions(params?: {
  workflowId?: string;
  status?: string;
}): UseExecutionsResult {
  const [data, setData] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await listExecutions(params ?? {});
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load executions");
    } finally {
      setLoading(false);
    }
  }, [params?.workflowId, params?.status]);

  useEffect(() => {
    void fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}
