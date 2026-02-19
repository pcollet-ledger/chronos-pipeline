import { useCallback, useEffect, useState } from "react";
import type { WorkflowExecution } from "../types";
import { getExecution, listExecutions, listWorkflowExecutions } from "../services/api";

interface UseExecutionsResult {
  data: WorkflowExecution[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useExecutions(status?: string): UseExecutionsResult {
  const [data, setData] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);
    listExecutions(status)
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load executions");
      })
      .finally(() => setLoading(false));
  }, [status]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

interface UseWorkflowExecutionsResult {
  data: WorkflowExecution[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useWorkflowExecutions(workflowId: string): UseWorkflowExecutionsResult {
  const [data, setData] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);
    listWorkflowExecutions(workflowId)
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load executions");
      })
      .finally(() => setLoading(false));
  }, [workflowId]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

interface UseSingleExecutionResult {
  data: WorkflowExecution | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useExecution(executionId: string): UseSingleExecutionResult {
  const [data, setData] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);
    getExecution(executionId)
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load execution");
      })
      .finally(() => setLoading(false));
  }, [executionId]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}
