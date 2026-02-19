"""Tests for the TTL-based analytics cache.

Covers: cache hit returns same result, cache invalidation works,
TTL expiry returns fresh data, concurrent access safety, and
interaction with workflow operations.
"""

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate
from app.services import analytics_service
from app.services.analytics_service import (
    DEFAULT_CACHE_TTL,
    clear_cache,
    get_cache_ttl,
    get_summary,
    get_workflow_stats,
    invalidate_cache,
    set_cache_ttl,
)
from app.services.workflow_engine import clear_all, create_workflow, execute_workflow


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    clear_cache()
    set_cache_ttl(DEFAULT_CACHE_TTL)
    yield
    clear_all()
    clear_cache()
    set_cache_ttl(DEFAULT_CACHE_TTL)


@pytest.fixture
def client():
    return TestClient(app)


def _create_and_execute(name: str = "WF") -> str:
    wf = create_workflow(WorkflowCreate(
        name=name,
        tasks=[{"name": "Step", "action": "log", "parameters": {"message": "ok"}}],
    ))
    execute_workflow(wf.id)
    return wf.id


class TestCacheHit:
    """Verify that repeated calls return cached results."""

    def test_summary_cached_on_second_call(self):
        _create_and_execute()
        clear_cache()
        result1 = get_summary(days=30)
        result2 = get_summary(days=30)
        assert result1.total_executions == result2.total_executions
        assert result1 is result2

    def test_workflow_stats_cached(self):
        wf_id = _create_and_execute()
        clear_cache()
        result1 = get_workflow_stats(wf_id)
        result2 = get_workflow_stats(wf_id)
        assert result1 is result2

    def test_different_days_produce_different_cache_keys(self):
        _create_and_execute()
        clear_cache()
        result1 = get_summary(days=30)
        result2 = get_summary(days=7)
        assert result1 is not result2


class TestCacheInvalidation:
    """Verify that invalidation clears cached data."""

    def test_invalidate_clears_summary(self):
        _create_and_execute()
        clear_cache()
        result1 = get_summary(days=30)
        invalidate_cache()
        _create_and_execute("WF2")
        result2 = get_summary(days=30)
        assert result2.total_executions > result1.total_executions

    def test_clear_cache_forces_recompute(self):
        _create_and_execute()
        result1 = get_summary(days=30)
        clear_cache()
        result2 = get_summary(days=30)
        assert result1 is not result2

    def test_invalidate_clears_workflow_stats(self):
        wf_id = _create_and_execute()
        clear_cache()
        result1 = get_workflow_stats(wf_id)
        invalidate_cache()
        execute_workflow(wf_id)
        result2 = get_workflow_stats(wf_id)
        assert result2["total_executions"] > result1["total_executions"]


class TestCacheTTLExpiry:
    """Verify that expired entries are not returned."""

    def test_expired_entry_returns_fresh_data(self):
        set_cache_ttl(0.01)
        _create_and_execute()
        result1 = get_summary(days=30)
        time.sleep(0.02)
        _create_and_execute("WF2")
        result2 = get_summary(days=30)
        assert result2.total_executions > result1.total_executions

    def test_non_expired_entry_returns_cached(self):
        set_cache_ttl(60)
        _create_and_execute()
        result1 = get_summary(days=30)
        result2 = get_summary(days=30)
        assert result1 is result2

    def test_ttl_configuration(self):
        set_cache_ttl(42.0)
        assert get_cache_ttl() == 42.0

    def test_default_ttl(self):
        assert DEFAULT_CACHE_TTL == 30.0


class TestCacheConcurrency:
    """Verify thread-safety of cache operations."""

    def test_concurrent_reads_do_not_crash(self):
        import threading

        _create_and_execute()
        clear_cache()
        errors = []

        def reader():
            try:
                for _ in range(10):
                    get_summary(days=30)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []

    def test_concurrent_write_and_read(self):
        import threading

        _create_and_execute()
        errors = []

        def writer():
            try:
                for _ in range(10):
                    invalidate_cache()
            except Exception as exc:
                errors.append(exc)

        def reader():
            try:
                for _ in range(10):
                    get_summary(days=30)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []


class TestCacheViaAPI:
    """Verify caching behaviour through the HTTP API."""

    def test_summary_endpoint_uses_cache(self, client):
        client.post("/api/workflows/", json={"name": "WF", "tasks": [
            {"name": "S", "action": "log", "parameters": {"message": "ok"}}
        ]})
        wf_id = client.get("/api/workflows/").json()[0]["id"]
        client.post(f"/api/workflows/{wf_id}/execute")
        clear_cache()

        resp1 = client.get("/api/analytics/summary")
        resp2 = client.get("/api/analytics/summary")
        assert resp1.json()["total_executions"] == resp2.json()["total_executions"]

    def test_timeline_endpoint_returns_data(self, client):
        resp = client.get("/api/analytics/timeline", params={"hours": 1, "bucket_minutes": 15})
        assert resp.status_code == 200

    def test_workflow_stats_via_api(self, client):
        client.post("/api/workflows/", json={"name": "WF", "tasks": [
            {"name": "S", "action": "log", "parameters": {"message": "ok"}}
        ]})
        wf_id = client.get("/api/workflows/").json()[0]["id"]
        client.post(f"/api/workflows/{wf_id}/execute")
        clear_cache()
        resp = client.get(f"/api/analytics/workflows/{wf_id}/stats")
        assert resp.status_code == 200
        assert resp.json()["total_executions"] == 1


class TestCacheEdgeCases:
    """Additional edge case tests for the analytics cache."""

    def test_cache_returns_stale_data_within_ttl(self):
        """Data created after cache fill should not appear until TTL expires."""
        set_cache_ttl(60)
        _create_and_execute("WF1")
        clear_cache()
        result1 = get_summary(days=30)
        assert result1.total_executions == 1
        _create_and_execute("WF2")
        result2 = get_summary(days=30)
        assert result2.total_executions == 1
        assert result1 is result2

    def test_different_workflow_ids_produce_different_cache_entries(self):
        wf1_id = _create_and_execute("WF1")
        wf2_id = _create_and_execute("WF2")
        clear_cache()
        stats1 = get_workflow_stats(wf1_id)
        stats2 = get_workflow_stats(wf2_id)
        assert stats1["workflow_id"] != stats2["workflow_id"]

    def test_cache_survives_empty_state(self):
        """Cache should work even when there are no executions."""
        clear_cache()
        result = get_summary(days=30)
        assert result.total_executions == 0
        result2 = get_summary(days=30)
        assert result is result2

    def test_set_ttl_to_zero_disables_caching(self):
        """With TTL=0, every call should recompute."""
        set_cache_ttl(0)
        _create_and_execute()
        result1 = get_summary(days=30)
        result2 = get_summary(days=30)
        assert result1 is not result2

    def test_invalidate_is_idempotent(self):
        """Calling invalidate_cache multiple times should not error."""
        invalidate_cache()
        invalidate_cache()
        invalidate_cache()
        result = get_summary(days=30)
        assert result.total_executions == 0

    def test_cache_key_includes_days_parameter(self):
        """Different days parameters should produce different cache entries."""
        _create_and_execute()
        clear_cache()
        r7 = get_summary(days=7)
        r30 = get_summary(days=30)
        assert r7 is not r30
