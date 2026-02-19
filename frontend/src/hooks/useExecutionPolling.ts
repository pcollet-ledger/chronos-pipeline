/**
 * Polls a single execution by ID at a configurable interval.
 * Stops polling automatically when execution reaches a terminal state.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import type { WorkflowExecution } from "../types";
import { getExecution } from "../services/api";

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);

interface UseExecutionPollingResult {
  execution: WorkflowExecution | null;
  loading: boolean;
  error: string | null;
  stop: () => void;
  restart: () => void;
}

export function useExecutionPolling(
  executionId: string | null,
  intervalMs = 2000,
): UseExecutionPollingResult {
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const poll = useCallback(async () => {
    if (!executionId) return;
    try {
      const result = await getExecution(executionId);
      setExecution(result);
      setError(null);
      if (TERMINAL_STATUSES.has(result.status)) {
        setActive(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Polling failed");
    }
  }, [executionId]);

  useEffect(() => {
    clearTimer();
    if (!executionId || !active) return;

    setLoading(true);
    void poll().finally(() => setLoading(false));

    timerRef.current = setInterval(() => void poll(), intervalMs);
    return clearTimer;
  }, [executionId, active, intervalMs, poll, clearTimer]);

  const stop = useCallback(() => {
    setActive(false);
    clearTimer();
  }, [clearTimer]);

  const restart = useCallback(() => {
    setActive(true);
  }, []);

  return { execution, loading, error, stop, restart };
}
