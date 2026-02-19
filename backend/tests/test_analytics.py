"""Tests for analytics service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.analytics_service import clear_cache
from app.services.workflow_engine import clear_all


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    clear_cache()
    yield
    clear_all()
    clear_cache()


@pytest.fixture
def client():
    return TestClient(app)


def _create_and_execute(client, name="WF"):
    payload = {
        "name": name,
        "tasks": [
            {"name": "Step", "action": "log", "parameters": {"message": "ok"}},
        ],
    }
    resp = client.post("/api/workflows/", json=payload)
    wf_id = resp.json()["id"]
    client.post(f"/api/workflows/{wf_id}/execute")
    return wf_id


class TestAnalyticsSummary:
    def test_empty_summary(self, client):
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_workflows"] == 0
        assert data["total_executions"] == 0

    def test_summary_after_executions(self, client):
        _create_and_execute(client, "WF1")
        _create_and_execute(client, "WF2")
        resp = client.get("/api/analytics/summary")
        data = resp.json()
        assert data["total_workflows"] == 2
        assert data["total_executions"] == 2
        assert data["success_rate"] == 100.0


class TestWorkflowStats:
    def test_stats_for_workflow(self, client):
        wf_id = _create_and_execute(client, "StatsWF")
        # Execute again
        client.post(f"/api/workflows/{wf_id}/execute")
        resp = client.get(f"/api/analytics/workflows/{wf_id}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_executions"] == 2
        assert data["completed"] == 2


class TestTimeline:
    def test_timeline_structure(self, client):
        _create_and_execute(client)
        resp = client.get("/api/analytics/timeline", params={"hours": 1, "bucket_minutes": 15})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert all("time" in entry and "total" in entry for entry in data)

    def test_timeline_empty(self, client):
        resp = client.get("/api/analytics/timeline", params={"hours": 1, "bucket_minutes": 15})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_timeline_default_params(self, client):
        resp = client.get("/api/analytics/timeline")
        assert resp.status_code == 200


class TestAnalyticsEdgeCases:
    def test_summary_with_failed_executions(self, client):
        payload = {
            "name": "Fail WF",
            "tasks": [{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        }
        resp = client.post("/api/workflows/", json=payload)
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/execute")
        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert summary["total_executions"] == 1
        assert summary["success_rate"] == 0.0

    def test_summary_mixed_statuses(self, client):
        _create_and_execute(client, "Good")
        payload = {
            "name": "Bad",
            "tasks": [{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        }
        resp = client.post("/api/workflows/", json=payload)
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/execute")
        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert summary["total_executions"] == 2
        assert summary["success_rate"] == 50.0

    def test_workflow_stats_multiple_executions(self, client):
        wf_id = _create_and_execute(client, "Multi")
        client.post(f"/api/workflows/{wf_id}/execute")
        client.post(f"/api/workflows/{wf_id}/execute")
        clear_cache()
        stats = client.get(f"/api/analytics/workflows/{wf_id}/stats").json()
        assert stats["total_executions"] == 3
        assert stats["completed"] == 3

    def test_workflow_stats_nonexistent(self, client):
        resp = client.get("/api/analytics/workflows/nonexistent/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_executions"] == 0

    def test_summary_top_failing_workflows(self, client):
        payload = {
            "name": "Fail WF",
            "tasks": [{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        }
        resp = client.post("/api/workflows/", json=payload)
        wf_id = resp.json()["id"]
        for _ in range(3):
            client.post(f"/api/workflows/{wf_id}/execute")
        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert len(summary["top_failing_workflows"]) >= 1

    def test_summary_with_zero_days(self, client):
        _create_and_execute(client)
        clear_cache()
        resp = client.get("/api/analytics/summary", params={"days": 0})
        assert resp.status_code == 200
        assert resp.json()["total_executions"] == 0

    def test_summary_with_large_days(self, client):
        _create_and_execute(client)
        clear_cache()
        resp = client.get("/api/analytics/summary", params={"days": 9999})
        assert resp.status_code == 200
        assert resp.json()["total_executions"] == 1

    def test_summary_avg_duration_is_non_negative(self, client):
        _create_and_execute(client)
        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert summary["avg_duration_ms"] >= 0

    def test_summary_recent_executions_limited(self, client):
        """Recent executions should be limited to 10."""
        for i in range(12):
            _create_and_execute(client, f"WF-{i}")
        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert len(summary["recent_executions"]) <= 10


class TestAnalyticsWorkflowStatsEdgeCases:
    """Additional edge case tests for workflow stats."""

    def test_stats_empty_workflow_id(self, client):
        """Stats for a workflow with no executions should return zeros."""
        resp = client.post("/api/workflows/", json={"name": "No Execs"})
        wf_id = resp.json()["id"]
        clear_cache()
        stats = client.get(f"/api/analytics/workflows/{wf_id}/stats").json()
        assert stats["total_executions"] == 0
        assert stats["success_rate"] == 0

    def test_stats_after_failed_execution(self, client):
        payload = {
            "name": "Fail Stats",
            "tasks": [{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        }
        resp = client.post("/api/workflows/", json=payload)
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/execute")
        clear_cache()
        stats = client.get(f"/api/analytics/workflows/{wf_id}/stats").json()
        assert stats["failed"] == 1
        assert stats["completed"] == 0
        assert stats["success_rate"] == 0.0

    def test_stats_duration_fields(self, client):
        wf_id = _create_and_execute(client, "Duration Stats")
        clear_cache()
        stats = client.get(f"/api/analytics/workflows/{wf_id}/stats").json()
        assert "avg_duration_ms" in stats
        assert "min_duration_ms" in stats
        assert "max_duration_ms" in stats
        assert stats["avg_duration_ms"] >= 0

    def test_summary_executions_by_status_keys(self, client):
        _create_and_execute(client, "Status Keys")
        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert "completed" in summary["executions_by_status"]

    def test_timeline_bucket_count(self, client):
        """Timeline with 1 hour and 15-minute buckets should have ~4 buckets."""
        _create_and_execute(client)
        clear_cache()
        resp = client.get("/api/analytics/timeline", params={"hours": 1, "bucket_minutes": 15})
        data = resp.json()
        assert len(data) >= 4

    def test_summary_after_delete_reflects_fewer_workflows(self, client):
        wf_id = _create_and_execute(client, "Delete Me")
        _create_and_execute(client, "Keep Me")
        clear_cache()
        summary1 = client.get("/api/analytics/summary").json()
        assert summary1["total_workflows"] == 2

        client.delete(f"/api/workflows/{wf_id}")
        clear_cache()
        summary2 = client.get("/api/analytics/summary").json()
        assert summary2["total_workflows"] == 1
