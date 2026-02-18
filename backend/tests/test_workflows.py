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


class TestExportWorkflow:
    def test_export_returns_json(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        resp = client.get(f"/api/workflows/{wf_id}/export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Workflow"
        assert data["version"] == "1.0"
        assert "id" not in data
        assert "created_at" not in data
        assert "updated_at" not in data

    def test_export_tasks_have_no_id(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        resp = client.get(f"/api/workflows/{wf_id}/export")
        data = resp.json()
        for task in data["tasks"]:
            assert "id" not in task

    def test_export_has_content_disposition(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        resp = client.get(f"/api/workflows/{wf_id}/export")
        assert "content-disposition" in resp.headers
        assert f"workflow-{wf_id}.json" in resp.headers["content-disposition"]

    def test_export_not_found(self, client):
        resp = client.get("/api/workflows/nonexistent/export")
        assert resp.status_code == 404


class TestImportWorkflow:
    def test_import_creates_workflow(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        export_resp = client.get(f"/api/workflows/{wf_id}/export")
        exported = export_resp.json()

        resp = client.post("/api/workflows/import", json=exported)
        assert resp.status_code == 201
        imported = resp.json()
        assert imported["name"] == "Test Workflow"
        assert imported["id"] != wf_id
        assert len(imported["tasks"]) == 2

    def test_import_assigns_fresh_ids(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        original_tasks = create_resp.json()["tasks"]

        export_resp = client.get(f"/api/workflows/{wf_id}/export")
        exported = export_resp.json()

        resp = client.post("/api/workflows/import", json=exported)
        imported_tasks = resp.json()["tasks"]
        for orig, imp in zip(original_tasks, imported_tasks):
            assert orig["id"] != imp["id"]

    def test_import_roundtrip_preserves_data(self, client):
        create_resp = client.post("/api/workflows/", json=_sample_workflow_payload())
        wf_id = create_resp.json()["id"]
        export_resp = client.get(f"/api/workflows/{wf_id}/export")
        exported = export_resp.json()

        resp = client.post("/api/workflows/import", json=exported)
        imported = resp.json()
        assert imported["description"] == "A test workflow"
        assert imported["tags"] == ["test", "ci"]
        assert imported["tasks"][0]["action"] == "log"
        assert imported["tasks"][1]["action"] == "validate"

    def test_import_minimal_payload(self, client):
        resp = client.post("/api/workflows/import", json={"name": "Imported Minimal"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "Imported Minimal"
        assert resp.json()["tasks"] == []

    def test_import_validation_error(self, client):
        resp = client.post("/api/workflows/import", json={})
        assert resp.status_code == 422

    def test_imported_workflow_is_listable(self, client):
        resp = client.post("/api/workflows/import", json={"name": "Listed"})
        assert resp.status_code == 201
        list_resp = client.get("/api/workflows/")
        names = [w["name"] for w in list_resp.json()]
        assert "Listed" in names
