import { useCallback, useEffect, useState } from "react";
import type { AnalyticsSummary, TimelineBucket } from "../types";
import * as api from "../services/api";

interface UseAnalyticsResult {
  summary: AnalyticsSummary | null;
  timeline: TimelineBucket[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useAnalytics(days = 30, hours = 24, bucketMinutes = 60): UseAnalyticsResult {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [timeline, setTimeline] = useState<TimelineBucket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getAnalyticsSummary(days),
      api.getTimeline(hours, bucketMinutes),
    ])
      .then(([s, t]) => {
        setSummary(s);
        setTimeline(t);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [days, hours, bucketMinutes]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { summary, timeline, loading, error, refresh };
}
