import { useCallback, useEffect, useRef, useState } from "react";
import type { WorkflowExecution } from "../types";
import { getExecution } from "../services/api";

interface UseExecutionPollingResult {
  data: WorkflowExecution | null;
  loading: boolean;
  error: string | null;
  isPolling: boolean;
  startPolling: () => void;
  stopPolling: () => void;
}

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);

export function useExecutionPolling(
  executionId: string,
  intervalMs = 2000,
): UseExecutionPollingResult {
  const [data, setData] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchOnce = useCallback(() => {
    getExecution(executionId)
      .then((execution) => {
        setData(execution);
        setError(null);
        if (TERMINAL_STATUSES.has(execution.status)) {
          setIsPolling(false);
        }
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Polling failed");
      })
      .finally(() => setLoading(false));
  }, [executionId]);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  const startPolling = useCallback(() => {
    setIsPolling(true);
    fetchOnce();
  }, [fetchOnce]);

  useEffect(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (isPolling) {
      timerRef.current = setInterval(fetchOnce, intervalMs);
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isPolling, fetchOnce, intervalMs]);

  return { data, loading, error, isPolling, startPolling, stopPolling };
}
