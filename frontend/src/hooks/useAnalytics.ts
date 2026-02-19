import { useCallback, useEffect, useState } from "react";
import type { AnalyticsSummary, TimelineBucket } from "../types";
import { getAnalyticsSummary, getTimeline } from "../services/api";

interface UseAnalyticsReturn {
  summary: AnalyticsSummary | null;
  timeline: TimelineBucket[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useAnalytics(
  days = 30,
  timelineHours = 24,
): UseAnalyticsReturn {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [timeline, setTimeline] = useState<TimelineBucket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [s, t] = await Promise.all([
        getAnalyticsSummary(days),
        getTimeline(timelineHours),
      ]);
      setSummary(s);
      setTimeline(t);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load analytics",
      );
    } finally {
      setLoading(false);
    }
  }, [days, timelineHours]);

  useEffect(() => {
    void load();
  }, [load]);

  return { summary, timeline, loading, error, refresh: () => void load() };
}
