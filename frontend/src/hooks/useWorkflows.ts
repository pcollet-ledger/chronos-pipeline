import { useCallback, useMemo } from "react";
import * as api from "../services/api";
import type { Workflow, WorkflowCreatePayload } from "../types";
import { useApi } from "./useApi";

interface UseWorkflowsOptions {
  tag?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

interface UseWorkflowsResult {
  data: Workflow[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  createWorkflow: (payload: WorkflowCreatePayload) => Promise<Workflow>;
  deleteWorkflow: (id: string) => Promise<void>;
  cloneWorkflow: (id: string) => Promise<Workflow>;
}

export function useWorkflows(
  options: UseWorkflowsOptions = {},
): UseWorkflowsResult {
  const { tag, search, limit, offset } = options;

  const fetcher = useCallback(
    () => api.listWorkflows(tag, search, limit, offset),
    [tag, search, limit, offset],
  );

  const { data, loading, error, refetch } = useApi<Workflow[]>(fetcher);

  const createWorkflow = useCallback(
    async (payload: WorkflowCreatePayload): Promise<Workflow> => {
      const result = await api.createWorkflow(payload);
      refetch();
      return result;
    },
    [refetch],
  );

  const deleteWorkflow = useCallback(
    async (id: string): Promise<void> => {
      await api.deleteWorkflow(id);
      refetch();
    },
    [refetch],
  );

  const cloneWorkflow = useCallback(
    async (id: string): Promise<Workflow> => {
      const result = await api.cloneWorkflow(id);
      refetch();
      return result;
    },
    [refetch],
  );

  return useMemo(
    () => ({ data, loading, error, refetch, createWorkflow, deleteWorkflow, cloneWorkflow }),
    [data, loading, error, refetch, createWorkflow, deleteWorkflow, cloneWorkflow],
  );
}
