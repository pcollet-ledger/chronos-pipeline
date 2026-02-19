"""Comprehensive tests for POST /api/tasks/executions/{id}/cancel.

Covers: cancel running, cancel pending, cancel completed (409),
cancel failed (409), cancel already-cancelled (409), cancel not found (404),
verify status and timestamps, service-layer unit tests, and interactions
with other features (retry, analytics).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowExecution, WorkflowStatus
from app.services.workflow_engine import (
    _executions,
    cancel_execution,
    clear_all,
    create_workflow,
    execute_workflow,
    get_execution,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    return TestClient(app)


def _create_good_workflow(client) -> str:
    payload = {
        "name": "Good WF",
        "tasks": [
            {"name": "Log", "action": "log", "parameters": {"message": "hi"}},
        ],
    }
    return client.post("/api/workflows/", json=payload).json()["id"]


class TestCancelRunning:
    """Cancel a RUNNING execution."""

    def test_cancel_running_returns_200(self, client):
        wf_id = _create_good_workflow(client)
        running_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        resp = client.post(f"/api/tasks/executions/{running_exec.id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    def test_cancel_running_sets_cancelled_at(self, client):
        wf_id = _create_good_workflow(client)
        running_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        resp = client.post(f"/api/tasks/executions/{running_exec.id}/cancel")
        assert resp.json()["cancelled_at"] is not None

    def test_cancel_running_sets_completed_at(self, client):
        wf_id = _create_good_workflow(client)
        running_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        resp = client.post(f"/api/tasks/executions/{running_exec.id}/cancel")
        assert resp.json()["completed_at"] is not None


class TestCancelPending:
    """Cancel a PENDING execution."""

    def test_cancel_pending_returns_200(self, client):
        wf_id = _create_good_workflow(client)
        pending_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.PENDING,
        )
        _executions[pending_exec.id] = pending_exec

        resp = client.post(f"/api/tasks/executions/{pending_exec.id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    def test_cancel_pending_sets_timestamps(self, client):
        wf_id = _create_good_workflow(client)
        pending_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.PENDING,
        )
        _executions[pending_exec.id] = pending_exec

        resp = client.post(f"/api/tasks/executions/{pending_exec.id}/cancel")
        data = resp.json()
        assert data["cancelled_at"] is not None
        assert data["completed_at"] is not None


class TestCancelCompleted:
    """Cannot cancel a COMPLETED execution."""

    def test_cancel_completed_returns_409(self, client):
        wf_id = _create_good_workflow(client)
        exec_data = client.post(f"/api/workflows/{wf_id}/execute").json()
        assert exec_data["status"] == "completed"

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/cancel")
        assert resp.status_code == 409
        assert "Only running or pending" in resp.json()["detail"]


class TestCancelFailed:
    """Cannot cancel a FAILED execution."""

    def test_cancel_failed_returns_409(self, client):
        payload = {
            "name": "Fail WF",
            "tasks": [{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        }
        wf_id = client.post("/api/workflows/", json=payload).json()["id"]
        exec_data = client.post(f"/api/workflows/{wf_id}/execute").json()
        assert exec_data["status"] == "failed"

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/cancel")
        assert resp.status_code == 409


class TestCancelAlreadyCancelled:
    """Cannot cancel an already-cancelled execution."""

    def test_cancel_cancelled_returns_409(self, client):
        wf_id = _create_good_workflow(client)
        running_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        resp1 = client.post(f"/api/tasks/executions/{running_exec.id}/cancel")
        assert resp1.status_code == 200

        resp2 = client.post(f"/api/tasks/executions/{running_exec.id}/cancel")
        assert resp2.status_code == 409


class TestCancelNotFound:
    """Cancel a non-existent execution."""

    def test_cancel_not_found_returns_404(self, client):
        resp = client.post("/api/tasks/executions/nonexistent/cancel")
        assert resp.status_code == 404
        assert "Execution not found" in resp.json()["detail"]


class TestCancelServiceLayer:
    """Direct tests against workflow_engine.cancel_execution."""

    def test_cancel_returns_none_for_missing(self):
        assert cancel_execution("nonexistent") is None

    def test_cancel_raises_for_completed(self):
        wf = create_workflow(WorkflowCreate(name="Good", tasks=[]))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED

        with pytest.raises(ValueError, match="Only running or pending"):
            cancel_execution(ex.id)

    def test_cancel_raises_for_failed(self):
        wf = create_workflow(
            WorkflowCreate(
                name="Bad",
                tasks=[{"name": "Bad", "action": "unknown_action", "parameters": {}}],
            )
        )
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.FAILED

        with pytest.raises(ValueError, match="Only running or pending"):
            cancel_execution(ex.id)

    def test_cancel_updates_execution_in_store(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        running_exec = WorkflowExecution(
            workflow_id=wf.id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        cancel_execution(running_exec.id)
        stored = get_execution(running_exec.id)
        assert stored is not None
        assert stored.status == WorkflowStatus.CANCELLED

    def test_cancel_pending_via_service(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        pending_exec = WorkflowExecution(
            workflow_id=wf.id,
            status=WorkflowStatus.PENDING,
        )
        _executions[pending_exec.id] = pending_exec

        result = cancel_execution(pending_exec.id)
        assert result is not None
        assert result.status == WorkflowStatus.CANCELLED
        assert result.cancelled_at is not None

    def test_cancel_preserves_workflow_id(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        running_exec = WorkflowExecution(
            workflow_id=wf.id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        result = cancel_execution(running_exec.id)
        assert result.workflow_id == wf.id

    def test_cancel_preserves_existing_task_results(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        running_exec = WorkflowExecution(
            workflow_id=wf.id,
            status=WorkflowStatus.RUNNING,
            task_results=[],
        )
        _executions[running_exec.id] = running_exec

        result = cancel_execution(running_exec.id)
        assert result.task_results == []

    def test_cancelled_execution_cannot_be_retried(self):
        from app.services.workflow_engine import retry_execution

        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        running_exec = WorkflowExecution(
            workflow_id=wf.id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        cancel_execution(running_exec.id)
        with pytest.raises(ValueError, match="Only failed executions"):
            retry_execution(running_exec.id)

    def test_cancel_idempotent_check(self):
        """Cancelling an already-cancelled execution raises ValueError."""
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        running_exec = WorkflowExecution(
            workflow_id=wf.id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        cancel_execution(running_exec.id)
        with pytest.raises(ValueError, match="Only running or pending"):
            cancel_execution(running_exec.id)

    def test_cancel_completed_at_equals_cancelled_at(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        running_exec = WorkflowExecution(
            workflow_id=wf.id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        result = cancel_execution(running_exec.id)
        assert result.completed_at == result.cancelled_at

    def test_cancel_returns_same_execution_id(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        running_exec = WorkflowExecution(
            workflow_id=wf.id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        result = cancel_execution(running_exec.id)
        assert result.id == running_exec.id

    def test_cancel_via_api_preserves_workflow_id(self, client):
        wf_id = _create_good_workflow(client)
        running_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        resp = client.post(f"/api/tasks/executions/{running_exec.id}/cancel")
        assert resp.json()["workflow_id"] == wf_id

    def test_cancel_error_message_includes_status(self, client):
        """Error message for non-cancellable execution includes current status."""
        wf_id = _create_good_workflow(client)
        exec_data = client.post(f"/api/workflows/{wf_id}/execute").json()
        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/cancel")
        assert resp.status_code == 409
        assert "completed" in resp.json()["detail"]
