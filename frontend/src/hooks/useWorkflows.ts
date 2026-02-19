import { useCallback, useEffect, useState } from "react";
import type { Workflow } from "../types";
import { listWorkflows } from "../services/api";

interface UseWorkflowsResult {
  data: Workflow[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useWorkflows(tag?: string, search?: string): UseWorkflowsResult {
  const [data, setData] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);
    listWorkflows(tag, search)
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load workflows");
      })
      .finally(() => setLoading(false));
  }, [tag, search]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}
