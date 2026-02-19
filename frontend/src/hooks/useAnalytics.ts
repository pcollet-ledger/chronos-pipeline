import { useCallback, useEffect, useState } from "react";
import type { AnalyticsSummary } from "../types";
import { getAnalyticsSummary } from "../services/api";

interface UseAnalyticsResult {
  analytics: AnalyticsSummary | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useAnalytics(days = 30): UseAnalyticsResult {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await getAnalyticsSummary(days);
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { analytics, loading, error, refresh };
}
