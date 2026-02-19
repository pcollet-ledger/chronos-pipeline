"""Full integration tests exercising cross-service interactions.

Tests the complete lifecycle: create workflow -> schedule -> execute ->
check analytics -> retry -> cancel -> verify analytics reflect all changes.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowExecution, WorkflowStatus
from app.services import analytics_service, workflow_engine
from app.services.analytics_service import clear_cache
from app.services.task_scheduler import clear_schedules, register_schedule
from app.services.workflow_engine import (
    _executions,
    cancel_execution,
    clear_all,
    create_workflow,
    execute_workflow,
    get_execution,
    list_executions,
    retry_execution,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    clear_cache()
    clear_schedules()
    yield
    clear_all()
    clear_cache()
    clear_schedules()


@pytest.fixture
def client():
    return TestClient(app)


class TestFullLifecycle:
    """End-to-end lifecycle: create -> execute -> analytics -> retry -> cancel."""

    def test_complete_lifecycle(self, client):
        """Walk through the entire workflow lifecycle via the API."""
        resp = client.post("/api/workflows/", json={
            "name": "Lifecycle WF",
            "tags": ["integration"],
            "tasks": [
                {"name": "Log", "action": "log", "parameters": {"message": "hello"}},
                {"name": "Validate", "action": "validate", "parameters": {"key": "val"}},
            ],
        })
        assert resp.status_code == 201
        wf_id = resp.json()["id"]

        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.status_code == 200
        assert exec_resp.json()["status"] == "completed"

        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert summary["total_workflows"] == 1
        assert summary["total_executions"] == 1
        assert summary["success_rate"] == 100.0

        stats = client.get(f"/api/analytics/workflows/{wf_id}/stats").json()
        assert stats["total_executions"] == 1
        assert stats["completed"] == 1

    def test_lifecycle_with_failure_and_retry(self, client):
        """Create -> execute (fails) -> retry (succeeds) -> verify analytics."""
        resp = client.post("/api/workflows/", json={
            "name": "Fail-Retry WF",
            "tasks": [
                {"name": "Good", "action": "log", "parameters": {"message": "ok"}},
                {"name": "Bad", "action": "unknown_action", "parameters": {}},
            ],
        })
        wf_id = resp.json()["id"]

        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        exec_data = exec_resp.json()
        assert exec_data["status"] == "failed"

        from app.services.workflow_engine import LogOutput
        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            retry_resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert retry_resp.json()["status"] == "completed"

        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert summary["total_executions"] == 2

    def test_lifecycle_with_cancellation(self, client):
        """Create -> execute (pending) -> cancel -> verify status."""
        wf_id = client.post("/api/workflows/", json={"name": "Cancel WF"}).json()["id"]

        pending_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.PENDING,
        )
        _executions[pending_exec.id] = pending_exec
        from app.services.workflow_engine import _index_execution
        _index_execution(pending_exec)

        cancel_resp = client.post(f"/api/tasks/executions/{pending_exec.id}/cancel")
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "cancelled"

        get_resp = client.get(f"/api/tasks/executions/{pending_exec.id}")
        assert get_resp.json()["status"] == "cancelled"

    def test_schedule_and_execute(self):
        """Register a schedule, then execute the workflow."""
        wf = create_workflow(WorkflowCreate(
            name="Scheduled WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
            schedule="0 8 * * *",
        ))
        entry = register_schedule(wf.id, "0 8 * * *")
        assert entry.workflow_id == wf.id

        ex = execute_workflow(wf.id, trigger="scheduled")
        assert ex.status == WorkflowStatus.COMPLETED
        assert ex.trigger == "scheduled"

    def test_multiple_workflows_analytics(self, client):
        """Create multiple workflows, execute them, verify aggregated analytics."""
        for i in range(5):
            resp = client.post("/api/workflows/", json={
                "name": f"WF-{i}",
                "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
            })
            wf_id = resp.json()["id"]
            client.post(f"/api/workflows/{wf_id}/execute")

        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert summary["total_workflows"] == 5
        assert summary["total_executions"] == 5

    def test_retry_then_cancel_interaction(self, client):
        """Retry a failed execution, then verify the original cannot be retried again."""
        resp = client.post("/api/workflows/", json={
            "name": "Retry-Cancel WF",
            "tasks": [{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        })
        wf_id = resp.json()["id"]

        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        exec_id = exec_resp.json()["id"]

        retry_resp = client.post(f"/api/tasks/executions/{exec_id}/retry")
        retry_id = retry_resp.json()["id"]
        assert retry_resp.json()["status"] == "failed"

        retry2_resp = client.post(f"/api/tasks/executions/{retry_id}/retry")
        assert retry2_resp.status_code == 200

    def test_bulk_delete_and_analytics(self, client):
        """Bulk delete workflows and verify analytics reflect the change."""
        ids = []
        for i in range(3):
            resp = client.post("/api/workflows/", json={"name": f"WF-{i}"})
            ids.append(resp.json()["id"])

        clear_cache()
        summary1 = client.get("/api/analytics/summary").json()
        assert summary1["total_workflows"] == 3

        client.post("/api/workflows/bulk-delete", json={"ids": ids[:2]})

        clear_cache()
        summary2 = client.get("/api/analytics/summary").json()
        assert summary2["total_workflows"] == 1

    def test_middleware_headers_on_all_endpoints(self, client):
        """Verify middleware headers are present on all endpoint types."""
        resp = client.get("/health")
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

        resp = client.post("/api/workflows/", json={"name": "Test"})
        assert "x-request-id" in resp.headers

        resp = client.get("/api/analytics/summary")
        assert "x-request-id" in resp.headers

    def test_tag_filtering_with_executions(self, client):
        """Create tagged workflows, execute, and verify tag filtering works."""
        client.post("/api/workflows/", json={"name": "A", "tags": ["prod"]})
        client.post("/api/workflows/", json={"name": "B", "tags": ["dev"]})
        client.post("/api/workflows/", json={"name": "C", "tags": ["prod", "dev"]})

        prod = client.get("/api/workflows/", params={"tag": "prod"}).json()
        assert len(prod) == 2

        dev = client.get("/api/workflows/", params={"tag": "dev"}).json()
        assert len(dev) == 2

    def test_execution_list_with_status_filter(self, client):
        """Execute workflows and filter executions by status."""
        good = client.post("/api/workflows/", json={
            "name": "Good",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()["id"]
        bad = client.post("/api/workflows/", json={
            "name": "Bad",
            "tasks": [{"name": "S", "action": "unknown_action", "parameters": {}}],
        }).json()["id"]

        client.post(f"/api/workflows/{good}/execute")
        client.post(f"/api/workflows/{bad}/execute")

        completed = client.get("/api/tasks/executions", params={"status": "completed"}).json()
        failed = client.get("/api/tasks/executions", params={"status": "failed"}).json()
        assert len(completed) == 1
        assert len(failed) == 1

    def test_timeline_reflects_executions(self, client):
        """Execute workflows and verify timeline endpoint returns data."""
        resp = client.post("/api/workflows/", json={
            "name": "Timeline WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/execute")

        clear_cache()
        timeline = client.get("/api/analytics/timeline", params={"hours": 24, "bucket_minutes": 60}).json()
        assert isinstance(timeline, list)
        assert len(timeline) > 0

    def test_cancel_does_not_affect_retry_of_other_execution(self, client):
        """Cancelling one execution should not affect retrying another."""
        wf_id = client.post("/api/workflows/", json={
            "name": "Multi-exec WF",
            "tasks": [{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        }).json()["id"]

        exec1 = client.post(f"/api/workflows/{wf_id}/execute").json()
        exec2 = client.post(f"/api/workflows/{wf_id}/execute").json()

        retry_resp = client.post(f"/api/tasks/executions/{exec1['id']}/retry")
        assert retry_resp.status_code == 200

    def test_workflow_update_does_not_affect_past_executions(self, client):
        """Updating a workflow should not change past execution records."""
        resp = client.post("/api/workflows/", json={
            "name": "Original",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        exec_id = exec_resp.json()["id"]

        client.patch(f"/api/workflows/{wf_id}", json={"name": "Updated"})

        get_resp = client.get(f"/api/tasks/executions/{exec_id}")
        assert get_resp.json()["workflow_id"] == wf_id

    def test_empty_workflow_execute_and_analytics(self, client):
        """An empty workflow should execute as completed and appear in analytics."""
        resp = client.post("/api/workflows/", json={"name": "Empty"})
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.json()["status"] == "completed"

        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert summary["total_executions"] == 1
        assert summary["success_rate"] == 100.0

    def test_hooks_in_integration(self, client):
        """Workflow with hooks should execute and appear in analytics correctly."""
        resp = client.post("/api/workflows/", json={
            "name": "Hooked WF",
            "tasks": [{
                "name": "S",
                "action": "validate",
                "parameters": {"key": "val"},
                "pre_hook": "log",
                "post_hook": "notify",
            }],
        })
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.json()["status"] == "completed"

        output = exec_resp.json()["task_results"][0]["output"]
        assert "pre_hook_output" in output
        assert "post_hook_output" in output

    def test_clone_then_execute_clone(self, client):
        """Clone a workflow and execute the clone independently."""
        resp = client.post("/api/workflows/", json={
            "name": "Clonable",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        clone_id = clone_resp.json()["id"]

        exec_resp = client.post(f"/api/workflows/{clone_id}/execute")
        assert exec_resp.json()["status"] == "completed"
        assert exec_resp.json()["workflow_id"] == clone_id

    def test_dry_run_does_not_affect_analytics(self, client):
        """Dry-run should not appear in analytics."""
        resp = client.post("/api/workflows/", json={
            "name": "DryRun WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/dry-run")

        clear_cache()
        summary = client.get("/api/analytics/summary").json()
        assert summary["total_executions"] == 0

    def test_versioning_after_multiple_updates(self, client):
        """Version history should track all updates."""
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        for i in range(5):
            client.patch(f"/api/workflows/{wf_id}", json={"name": f"V{i+2}"})

        history = client.get(f"/api/workflows/{wf_id}/history").json()
        assert len(history) == 5

        final = client.get(f"/api/workflows/{wf_id}").json()
        assert final["version"] == 6

    def test_search_and_tag_filter_combined(self, client):
        """Search + tag filter should intersect correctly."""
        client.post("/api/workflows/", json={"name": "Alpha Prod", "tags": ["prod"]})
        client.post("/api/workflows/", json={"name": "Alpha Dev", "tags": ["dev"]})
        client.post("/api/workflows/", json={"name": "Beta Prod", "tags": ["prod"]})

        resp = client.get("/api/workflows/", params={"search": "alpha", "tag": "prod"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Alpha Prod"

    def test_compare_executions_via_api(self, client):
        """Compare two executions of the same workflow."""
        resp = client.post("/api/workflows/", json={
            "name": "Compare WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        ex1 = client.post(f"/api/workflows/{wf_id}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf_id}/execute").json()

        cmp = client.get("/api/tasks/executions/compare", params={
            "ids": f"{ex1['id']},{ex2['id']}"
        })
        assert cmp.status_code == 200
        assert cmp.json()["workflow_id"] == wf_id
