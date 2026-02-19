import { useCallback, useEffect, useRef, useState } from "react";
import type { WorkflowExecution } from "../types";
import { getExecution } from "../services/api";

interface UseExecutionPollingOptions {
  executionId: string | null;
  intervalMs?: number;
  enabled?: boolean;
}

interface UseExecutionPollingReturn {
  execution: WorkflowExecution | null;
  loading: boolean;
  error: string | null;
  stop: () => void;
}

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);

export function useExecutionPolling({
  executionId,
  intervalMs = 2000,
  enabled = true,
}: UseExecutionPollingOptions): UseExecutionPollingReturn {
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const stopped = useRef(false);

  const stop = useCallback(() => {
    stopped.current = true;
  }, []);

  useEffect(() => {
    stopped.current = false;
    setExecution(null);
    setError(null);

    if (!executionId || !enabled) return;

    let timer: ReturnType<typeof setTimeout> | null = null;

    const poll = async () => {
      if (stopped.current) return;
      try {
        setLoading(true);
        const data = await getExecution(executionId);
        if (stopped.current) return;
        setExecution(data);
        setError(null);

        if (!TERMINAL_STATUSES.has(data.status)) {
          timer = setTimeout(() => void poll(), intervalMs);
        }
      } catch (err) {
        if (stopped.current) return;
        setError(
          err instanceof Error ? err.message : "Failed to poll execution",
        );
      } finally {
        setLoading(false);
      }
    };

    void poll();

    return () => {
      stopped.current = true;
      if (timer) clearTimeout(timer);
    };
  }, [executionId, intervalMs, enabled]);

  return { execution, loading, error, stop };
}
