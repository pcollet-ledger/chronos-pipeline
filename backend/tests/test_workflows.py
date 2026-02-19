"""Tests for workflow engine and API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import TaskPriority
from app.services.workflow_engine import clear_all


@pytest.fixture(autouse=True)
def cleanup():
    """Clear state before each test."""
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    return TestClient(app)


def _sample_workflow_payload(name="Test Workflow"):
    return {
        "name": name,
        "description": "A test workflow",
        "tasks": [
            {
                "name": "Log Step",
                "action": "log",
                "parameters": {"message": "hello"},
                "priority": TaskPriority.HIGH.value,
            },
            {
                "name": "Validate Step",
                "action": "validate",
                "parameters": {"key": "value"},
            },
        ],
        "tags": ["test", "ci"],
    }


class TestCreateWorkflow:
    def test_create_returns_201(self, client):
        resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Workflow"
        assert len(data["tasks"]) == 2
        assert data["id"]

    def test_create_minimal(self, client):
        resp = client.post("/api/workflows/", json={"name": "Minimal"})
        assert resp.status_code == 201
        assert resp.json()["tasks"] == []


class TestListWorkflows:
    def test_list_empty(self, client):
        resp = client.get("/api/workflows/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_create(self, client):
        client.post("/api/workflows/", json=_sample_workflow_payload("WF1"))
        client.post("/api/workflows/", json=_sample_workflow_payload("WF2"))
        resp = client.get("/api/workflows/")
        assert len(resp.json()) == 2

    def test_list_filter_by_tag(self, client):
        client.post("/api/workflows/", json=_sample_workflow_payload("Tagged"))
        client.post("/api/workflows/", json={"name": "No Tags"})
        resp = client.get("/api/workflows/", params={"tag": "test"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Tagged"


class TestGetWorkflow:
    def test_get_existing(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        resp = client.get(f"/api/workflows/{wf_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == wf_id

    def test_get_not_found(self, client):
        resp = client.get("/api/workflows/nonexistent")
        assert resp.status_code == 404


class TestUpdateWorkflow:
    def test_update_name(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        resp = client.patch(f"/api/workflows/{wf_id}", json={"name": "Updated"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_update_not_found(self, client):
        resp = client.patch("/api/workflows/nope", json={"name": "X"})
        assert resp.status_code == 404


class TestDeleteWorkflow:
    def test_delete_existing(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        resp = client.delete(f"/api/workflows/{wf_id}")
        assert resp.status_code == 204

    def test_delete_not_found(self, client):
        resp = client.delete("/api/workflows/nope")
        assert resp.status_code == 404


class TestExecuteWorkflow:
    def test_execute_success(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["task_results"]) == 2

    def test_execute_not_found(self, client):
        resp = client.post("/api/workflows/nope/execute")
        assert resp.status_code == 404

    def test_execute_with_failing_task(self, client):
        payload = {
            "name": "Failing WF",
            "tasks": [{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        }
        create_resp = client.post("/api/workflows/", json=payload)
        wf_id = create_resp.json()["id"]
        resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert resp.json()["status"] == "failed"

    def test_execute_empty_workflow(self, client):
        resp = client.post("/api/workflows/", json={"name": "Empty"})
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.json()["status"] == "completed"
        assert exec_resp.json()["task_results"] == []

    def test_execute_with_trigger(self, client):
        resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute", params={"trigger": "cron"})
        assert exec_resp.json()["trigger"] == "cron"


class TestWorkflowListPagination:
    def test_limit_parameter(self, client):
        for i in range(5):
            client.post("/api/workflows/", json=_sample_workflow_payload(f"WF-{i}"))
        resp = client.get("/api/workflows/", params={"limit": 2})
        assert len(resp.json()) == 2

    def test_offset_parameter(self, client):
        for i in range(5):
            client.post("/api/workflows/", json=_sample_workflow_payload(f"WF-{i}"))
        resp = client.get("/api/workflows/", params={"offset": 3, "limit": 10})
        assert len(resp.json()) == 2


class TestWorkflowSearchAndFilter:
    """Additional tests for search, filter, and edge cases."""

    def test_search_by_name(self, client):
        client.post("/api/workflows/", json=_sample_workflow_payload("Alpha Pipeline"))
        client.post("/api/workflows/", json=_sample_workflow_payload("Beta Pipeline"))
        client.post("/api/workflows/", json=_sample_workflow_payload("Gamma Job"))
        resp = client.get("/api/workflows/", params={"search": "pipeline"})
        assert len(resp.json()) == 2

    def test_search_case_insensitive(self, client):
        client.post("/api/workflows/", json=_sample_workflow_payload("My Workflow"))
        resp = client.get("/api/workflows/", params={"search": "MY WORKFLOW"})
        assert len(resp.json()) == 1

    def test_list_with_search_and_tag(self, client):
        client.post("/api/workflows/", json={
            "name": "Tagged Search", "tags": ["special"],
        })
        client.post("/api/workflows/", json={
            "name": "Tagged Other", "tags": ["special"],
        })
        client.post("/api/workflows/", json={
            "name": "Search Only",
        })
        resp = client.get("/api/workflows/", params={"search": "Tagged", "tag": "special"})
        assert len(resp.json()) == 2

    def test_update_increments_version(self, client):
        resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = resp.json()["id"]
        assert resp.json()["version"] == 1
        update_resp = client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        assert update_resp.json()["version"] == 2

    def test_create_with_schedule(self, client):
        payload = _sample_workflow_payload("Scheduled")
        payload["schedule"] = "0 8 * * *"
        resp = client.post("/api/workflows/", json=payload)
        assert resp.status_code == 201
        assert resp.json()["schedule"] == "0 8 * * *"

    def test_list_returns_sorted_by_updated_at(self, client):
        """Workflows should be sorted by updated_at descending."""
        r1 = client.post("/api/workflows/", json=_sample_workflow_payload("First"))
        r2 = client.post("/api/workflows/", json=_sample_workflow_payload("Second"))
        wf1_id = r1.json()["id"]
        client.patch(f"/api/workflows/{wf1_id}", json={"name": "First Updated"})
        resp = client.get("/api/workflows/")
        names = [w["name"] for w in resp.json()]
        assert names[0] == "First Updated"

    def test_offset_beyond_total_returns_empty(self, client):
        client.post("/api/workflows/", json=_sample_workflow_payload("Only"))
        resp = client.get("/api/workflows/", params={"offset": 100})
        assert resp.json() == []

    def test_delete_returns_204_no_content(self, client):
        resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}")
        assert del_resp.status_code == 204
        assert del_resp.content == b""
