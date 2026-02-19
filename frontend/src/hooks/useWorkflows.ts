/**
 * Custom hook for workflow API calls with loading/error/data state.
 */

import { useCallback, useEffect, useState } from "react";
import type { Workflow } from "../types";
import { listWorkflows } from "../services/api";

interface UseWorkflowsResult {
  data: Workflow[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useWorkflows(params?: {
  tag?: string;
  search?: string;
}): UseWorkflowsResult {
  const [data, setData] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await listWorkflows(params ?? {});
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workflows");
    } finally {
      setLoading(false);
    }
  }, [params?.tag, params?.search]);

  useEffect(() => {
    void fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}
