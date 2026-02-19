import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../services/api";
import type { WorkflowExecution } from "../types";

interface UseExecutionPollingResult {
  execution: WorkflowExecution | null;
  loading: boolean;
  error: string | null;
  isPolling: boolean;
  stop: () => void;
  restart: () => void;
}

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);

/**
 * Polls a single execution until it reaches a terminal status.
 * Automatically stops when the execution completes, fails, or is cancelled.
 */
export function useExecutionPolling(
  executionId: string | null,
  intervalMs = 2000,
): UseExecutionPollingResult {
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stoppedRef = useRef(false);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    stoppedRef.current = true;
    setIsPolling(false);
    clearTimer();
  }, [clearTimer]);

  const poll = useCallback(async () => {
    if (!executionId || stoppedRef.current) return;
    try {
      const result = await api.getExecution(executionId);
      setExecution(result);
      setError(null);
      if (TERMINAL_STATUSES.has(result.status)) {
        stop();
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Polling failed");
      stop();
    }
  }, [executionId, stop]);

  const startPolling = useCallback(() => {
    if (!executionId) return;
    stoppedRef.current = false;
    setIsPolling(true);
    setLoading(true);
    setError(null);

    poll().finally(() => setLoading(false));

    clearTimer();
    timerRef.current = setInterval(poll, intervalMs);
  }, [executionId, intervalMs, poll, clearTimer]);

  const restart = useCallback(() => {
    stop();
    startPolling();
  }, [stop, startPolling]);

  useEffect(() => {
    if (executionId) {
      startPolling();
    }
    return () => {
      clearTimer();
    };
  }, [executionId, startPolling, clearTimer]);

  return { execution, loading, error, isPolling, stop, restart };
}
