/**
 * Custom hook for analytics API calls with loading/error/data state.
 */

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

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getAnalyticsSummary(days);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    void fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}
