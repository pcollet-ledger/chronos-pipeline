import { useCallback, useEffect, useState } from "react";
import type { Workflow } from "../types";
import { listWorkflows } from "../services/api";

interface UseWorkflowsOptions {
  tag?: string;
  search?: string;
  limit?: number;
  offset?: number;
  autoFetch?: boolean;
}

interface UseWorkflowsResult {
  workflows: Workflow[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useWorkflows(options: UseWorkflowsOptions = {}): UseWorkflowsResult {
  const { tag, search, limit, offset, autoFetch = true } = options;
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await listWorkflows({ tag, search, limit, offset });
      setWorkflows(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workflows");
    } finally {
      setLoading(false);
    }
  }, [tag, search, limit, offset]);

  useEffect(() => {
    if (autoFetch) {
      void refresh();
    }
  }, [autoFetch, refresh]);

  return { workflows, loading, error, refresh };
}
