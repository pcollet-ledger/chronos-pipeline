import { useCallback, useEffect, useRef, useState } from "react";
import type { WorkflowExecution } from "../types";
import * as api from "../services/api";

interface UseExecutionPollingResult {
  execution: WorkflowExecution | null;
  loading: boolean;
  error: string | null;
  stop: () => void;
}

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);

export function useExecutionPolling(
  executionId: string | null,
  intervalMs = 2000,
): UseExecutionPollingResult {
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!executionId) {
      setExecution(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    const poll = () => {
      api
        .getExecution(executionId)
        .then((exec) => {
          if (cancelled) return;
          setExecution(exec);
          setLoading(false);
          if (TERMINAL_STATUSES.has(exec.status)) {
            stop();
          }
        })
        .catch((err: Error) => {
          if (cancelled) return;
          setError(err.message);
          setLoading(false);
          stop();
        });
    };

    poll();
    timerRef.current = setInterval(poll, intervalMs);

    return () => {
      cancelled = true;
      stop();
    };
  }, [executionId, intervalMs, stop]);

  return { execution, loading, error, stop };
}
