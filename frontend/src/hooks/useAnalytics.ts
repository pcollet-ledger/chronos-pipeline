import { useCallback, useEffect, useState } from "react";
import type { AnalyticsSummary } from "../types";
import { getAnalyticsSummary } from "../services/api";

interface UseAnalyticsResult {
  data: AnalyticsSummary | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useAnalytics(days = 30): UseAnalyticsResult {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    setLoading(true);
    setError(null);
    getAnalyticsSummary(days)
      .then(setData)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      })
      .finally(() => setLoading(false));
  }, [days]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}
