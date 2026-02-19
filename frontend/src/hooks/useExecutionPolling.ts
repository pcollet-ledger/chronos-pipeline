import { useCallback, useEffect, useRef, useState } from "react";
import type { WorkflowExecution } from "../types";
import { getExecution } from "../services/api";

interface UseExecutionPollingOptions {
  executionId: string | null;
  intervalMs?: number;
  enabled?: boolean;
}

interface UseExecutionPollingResult {
  execution: WorkflowExecution | null;
  loading: boolean;
  error: string | null;
  stop: () => void;
}

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);

/**
 * Polls a single execution until it reaches a terminal status.
 * Automatically stops when the execution completes, fails, or is cancelled.
 */
export function useExecutionPolling(
  options: UseExecutionPollingOptions,
): UseExecutionPollingResult {
  const { executionId, intervalMs = 2000, enabled = true } = options;
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
    if (!executionId || !enabled) {
      stop();
      return;
    }

    let cancelled = false;

    const poll = async () => {
      try {
        setLoading(true);
        const data = await getExecution(executionId);
        if (cancelled) return;
        setExecution(data);
        setError(null);
        if (TERMINAL_STATUSES.has(data.status)) {
          stop();
        }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Polling failed");
        stop();
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void poll();
    timerRef.current = setInterval(() => void poll(), intervalMs);

    return () => {
      cancelled = true;
      stop();
    };
  }, [executionId, intervalMs, enabled, stop]);

  return { execution, loading, error, stop };
}
