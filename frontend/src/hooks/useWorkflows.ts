import { useCallback, useEffect, useState } from "react";
import type { Workflow } from "../types";
import { listWorkflows } from "../services/api";

interface UseWorkflowsOptions {
  tag?: string;
  search?: string;
}

interface UseWorkflowsReturn {
  workflows: Workflow[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useWorkflows(
  options: UseWorkflowsOptions = {},
): UseWorkflowsReturn {
  const { tag, search } = options;
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listWorkflows(tag, search);
      setWorkflows(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workflows");
    } finally {
      setLoading(false);
    }
  }, [tag, search]);

  useEffect(() => {
    void load();
  }, [load]);

  return { workflows, loading, error, refresh: () => void load() };
}
