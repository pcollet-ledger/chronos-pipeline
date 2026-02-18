"""Tests for analytics service."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.workflow_engine import clear_all


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    yield
    clear_all()


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
