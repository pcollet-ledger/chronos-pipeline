import { useCallback, useMemo } from "react";
import * as api from "../services/api";
import type { AnalyticsSummary, TimelineBucket } from "../types";
import { useApi } from "./useApi";

interface UseAnalyticsResult {
  data: AnalyticsSummary | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useAnalytics(days = 30): UseAnalyticsResult {
  const fetcher = useCallback(() => api.getAnalyticsSummary(days), [days]);
  const { data, loading, error, refetch } = useApi<AnalyticsSummary>(fetcher);

  return useMemo(
    () => ({ data, loading, error, refetch }),
    [data, loading, error, refetch],
  );
}

interface UseTimelineResult {
  data: TimelineBucket[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useTimeline(
  hours = 24,
  bucketMinutes = 60,
): UseTimelineResult {
  const fetcher = useCallback(
    () => api.getTimeline(hours, bucketMinutes),
    [hours, bucketMinutes],
  );
  const { data, loading, error, refetch } =
    useApi<TimelineBucket[]>(fetcher);

  return useMemo(
    () => ({ data, loading, error, refetch }),
    [data, loading, error, refetch],
  );
}
