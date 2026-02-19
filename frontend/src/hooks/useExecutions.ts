import { useCallback, useMemo } from "react";
import * as api from "../services/api";
import type { ExecutionComparison, WorkflowExecution } from "../types";
import { useApi } from "./useApi";

interface UseExecutionsOptions {
  workflowId?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

interface UseExecutionsResult {
  data: WorkflowExecution[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  getExecution: (id: string) => Promise<WorkflowExecution>;
  retryExecution: (id: string) => Promise<WorkflowExecution>;
  cancelExecution: (id: string) => Promise<WorkflowExecution>;
  compareExecutions: (
    idA: string,
    idB: string,
  ) => Promise<ExecutionComparison>;
}

export function useExecutions(
  options: UseExecutionsOptions = {},
): UseExecutionsResult {
  const { workflowId, status, limit, offset } = options;

  const fetcher = useCallback(
    () => api.listExecutions(workflowId, status, limit, offset),
    [workflowId, status, limit, offset],
  );

  const { data, loading, error, refetch } = useApi<WorkflowExecution[]>(fetcher);

  const getExecution = useCallback(
    (id: string) => api.getExecution(id),
    [],
  );

  const retryExecution = useCallback(
    async (id: string): Promise<WorkflowExecution> => {
      const result = await api.retryExecution(id);
      refetch();
      return result;
    },
    [refetch],
  );

  const cancelExecution = useCallback(
    async (id: string): Promise<WorkflowExecution> => {
      const result = await api.cancelExecution(id);
      refetch();
      return result;
    },
    [refetch],
  );

  const compareExecutions = useCallback(
    (idA: string, idB: string) => api.compareExecutions(idA, idB),
    [],
  );

  return useMemo(
    () => ({
      data,
      loading,
      error,
      refetch,
      getExecution,
      retryExecution,
      cancelExecution,
      compareExecutions,
    }),
    [data, loading, error, refetch, getExecution, retryExecution, cancelExecution, compareExecutions],
  );
}
