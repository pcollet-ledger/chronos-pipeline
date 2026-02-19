import { useCallback, useEffect, useState } from "react";
import type { Workflow } from "../types";
import * as api from "../services/api";

interface UseWorkflowsResult {
  workflows: Workflow[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useWorkflows(tag?: string, search?: string): UseWorkflowsResult {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .listWorkflows(tag, search)
      .then(setWorkflows)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [tag, search]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { workflows, loading, error, refresh };
}
