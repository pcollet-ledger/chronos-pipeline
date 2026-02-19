"""Comprehensive tests for POST /api/tasks/executions/{execution_id}/retry.

This endpoint re-runs only the failed (or never-executed) tasks from a previous
execution while carrying forward the successful task results.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import TaskPriority, WorkflowStatus
from app.services.workflow_engine import (
    _executions,
    _workflows,
    clear_all,
    execute_workflow,
    create_workflow,
    get_execution,
)
from app.models import WorkflowCreate, WorkflowExecution


@pytest.fixture(autouse=True)
def cleanup():
    """Clear state before and after each test."""
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_good_workflow(client) -> str:
    """Create a workflow whose tasks all succeed. Returns workflow ID."""
    payload = {
        "name": "All-good",
        "tasks": [
            {"name": "Log", "action": "log", "parameters": {"message": "hi"}},
            {"name": "Validate", "action": "validate", "parameters": {"key": "v"}},
        ],
    }
    return client.post("/api/workflows/", json=payload).json()["id"]


def _create_failing_workflow(client) -> str:
    """Create a workflow where the second task fails. Returns workflow ID."""
    payload = {
        "name": "Partial-fail",
        "tasks": [
            {"name": "Log", "action": "log", "parameters": {"message": "ok"}},
            {"name": "Bad", "action": "unknown_action", "parameters": {}},
        ],
    }
    return client.post("/api/workflows/", json=payload).json()["id"]


def _create_all_failing_workflow(client) -> str:
    """Create a workflow where the very first task fails. Returns workflow ID."""
    payload = {
        "name": "All-fail",
        "tasks": [
            {"name": "Bad1", "action": "unknown_action", "parameters": {}},
            {"name": "Bad2", "action": "unknown_action", "parameters": {}},
        ],
    }
    return client.post("/api/workflows/", json=payload).json()["id"]


def _execute(client, workflow_id: str) -> dict:
    """Execute a workflow and return the execution response body."""
    return client.post(f"/api/workflows/{workflow_id}/execute").json()


# ===========================================================================
# Test class: Basic retry happy-path
# ===========================================================================


class TestRetryHappyPath:
    """Retry a failed execution and verify it completes."""

    def test_retry_re_executes_failed_task(self, client):
        """When the failing action is fixed, retry should succeed."""
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)
        assert exec_data["status"] == "failed"

        # Patch the action registry so that the unknown action now succeeds
        from app.services.workflow_engine import _run_action, LogOutput

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["trigger"] == "retry"
        assert data["metadata"]["retried_from"] == exec_data["id"]

    def test_retry_preserves_successful_results(self, client):
        """Successful task results from the original run are carried forward."""
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)
        original_success = exec_data["task_results"][0]
        assert original_success["status"] == "completed"

        from app.services.workflow_engine import LogOutput

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")

        retry_data = resp.json()
        # First task result should be identical to the original
        assert retry_data["task_results"][0]["task_id"] == original_success["task_id"]
        assert retry_data["task_results"][0]["status"] == "completed"
        assert retry_data["task_results"][0]["output"] == original_success["output"]

    def test_retry_creates_new_execution_id(self, client):
        """Retry should produce a new execution with a different ID."""
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)

        from app.services.workflow_engine import LogOutput

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="ok"),
        ):
            resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")

        assert resp.json()["id"] != exec_data["id"]

    def test_retry_new_execution_is_retrievable(self, client):
        """The new execution should be stored and retrievable via GET."""
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)

        from app.services.workflow_engine import LogOutput

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="ok"),
        ):
            retry_resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")

        new_id = retry_resp.json()["id"]
        get_resp = client.get(f"/api/tasks/executions/{new_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == new_id


# ===========================================================================
# Test class: Retry still fails
# ===========================================================================


class TestRetryStillFails:
    """When the underlying issue is not fixed, retry should also fail."""

    def test_retry_fails_again(self, client):
        """Retrying without fixing the action still produces a failed execution."""
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)
        assert exec_data["status"] == "failed"

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert data["trigger"] == "retry"
        # The first task should still be carried over as completed
        assert data["task_results"][0]["status"] == "completed"
        # The second task should still be failed
        assert data["task_results"][1]["status"] == "failed"

    def test_retry_of_retry(self, client):
        """A failed retry can itself be retried (chaining)."""
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)

        # First retry (still fails)
        resp1 = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp1.json()["status"] == "failed"

        # Retry the retry (still fails)
        resp2 = client.post(f"/api/tasks/executions/{resp1.json()['id']}/retry")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "failed"
        assert resp2.json()["metadata"]["retried_from"] == resp1.json()["id"]


# ===========================================================================
# Test class: Error handling & validation
# ===========================================================================


class TestRetryErrorHandling:
    """Edge cases and error responses for the retry endpoint."""

    def test_retry_nonexistent_execution(self, client):
        """404 when execution ID does not exist."""
        resp = client.post("/api/tasks/executions/no-such-id/retry")
        assert resp.status_code == 404
        assert "Execution not found" in resp.json()["detail"]

    def test_retry_completed_execution_returns_409(self, client):
        """409 when trying to retry a successful execution."""
        wf_id = _create_good_workflow(client)
        exec_data = _execute(client, wf_id)
        assert exec_data["status"] == "completed"

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp.status_code == 409
        assert "Only failed executions" in resp.json()["detail"]

    def test_retry_pending_execution_returns_409(self, client):
        """409 when trying to retry a PENDING execution."""
        # Manually create a pending execution in the store
        wf_id = _create_good_workflow(client)
        pending_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.PENDING,
        )
        _executions[pending_exec.id] = pending_exec

        resp = client.post(f"/api/tasks/executions/{pending_exec.id}/retry")
        assert resp.status_code == 409

    def test_retry_running_execution_returns_409(self, client):
        """409 when trying to retry a RUNNING execution."""
        wf_id = _create_good_workflow(client)
        running_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[running_exec.id] = running_exec

        resp = client.post(f"/api/tasks/executions/{running_exec.id}/retry")
        assert resp.status_code == 409

    def test_retry_cancelled_execution_returns_409(self, client):
        """409 when trying to retry a CANCELLED execution."""
        wf_id = _create_good_workflow(client)
        cancelled_exec = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.CANCELLED,
        )
        _executions[cancelled_exec.id] = cancelled_exec

        resp = client.post(f"/api/tasks/executions/{cancelled_exec.id}/retry")
        assert resp.status_code == 409

    def test_retry_when_workflow_deleted_returns_409(self, client):
        """409 when the parent workflow was deleted after the execution."""
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)
        assert exec_data["status"] == "failed"

        # Delete the parent workflow
        client.delete(f"/api/workflows/{wf_id}")

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp.status_code == 409
        assert "no longer exists" in resp.json()["detail"]


# ===========================================================================
# Test class: All tasks fail
# ===========================================================================


class TestRetryAllTasksFail:
    """Retry when the very first task fails (no successful results to carry)."""

    def test_first_task_fails_retry(self, client):
        """When the first task fails, retry re-executes it."""
        wf_id = _create_all_failing_workflow(client)
        exec_data = _execute(client, wf_id)
        assert exec_data["status"] == "failed"
        # Only one task result (execution stops at first failure)
        assert len(exec_data["task_results"]) == 1

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        # Should have re-run the first task (which still fails)
        assert data["task_results"][0]["status"] == "failed"

    def test_first_task_fixed_retry_succeeds(self, client):
        """When the first task is fixed, retry should attempt remaining tasks."""
        wf_id = _create_all_failing_workflow(client)
        exec_data = _execute(client, wf_id)

        from app.services.workflow_engine import LogOutput

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["task_results"]) == 2
        assert all(tr["status"] == "completed" for tr in data["task_results"])


# ===========================================================================
# Test class: Workflow with dependencies
# ===========================================================================


class TestRetryWithDependencies:
    """Retry behaviour with tasks that have depends_on relationships."""

    def test_retry_respects_task_order(self, client):
        """Tasks should be retried in topological order."""
        payload = {
            "name": "Dep-WF",
            "tasks": [
                {
                    "id": "step-a",
                    "name": "Step A",
                    "action": "log",
                    "parameters": {"message": "a"},
                },
                {
                    "id": "step-b",
                    "name": "Step B",
                    "action": "unknown_action",
                    "parameters": {},
                    "depends_on": ["step-a"],
                },
            ],
        }
        wf_id = client.post("/api/workflows/", json=payload).json()["id"]
        exec_data = _execute(client, wf_id)
        assert exec_data["status"] == "failed"

        from app.services.workflow_engine import LogOutput

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="ok"),
        ):
            resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")

        data = resp.json()
        assert data["status"] == "completed"
        # step-a should be carried from original, step-b re-executed
        assert data["task_results"][0]["task_id"] == "step-a"
        assert data["task_results"][1]["task_id"] == "step-b"

    def test_retry_with_diamond_dependency(self, client):
        """Diamond: A -> B, A -> C, B+C -> D — D fails, retry only D."""
        payload = {
            "name": "Diamond-WF",
            "tasks": [
                {"id": "A", "name": "A", "action": "log", "parameters": {"message": "a"}},
                {"id": "B", "name": "B", "action": "log", "parameters": {"message": "b"}, "depends_on": ["A"]},
                {"id": "C", "name": "C", "action": "log", "parameters": {"message": "c"}, "depends_on": ["A"]},
                {
                    "id": "D",
                    "name": "D",
                    "action": "unknown_action",
                    "parameters": {},
                    "depends_on": ["B", "C"],
                },
            ],
        }
        wf_id = client.post("/api/workflows/", json=payload).json()["id"]
        exec_data = _execute(client, wf_id)
        assert exec_data["status"] == "failed"
        # A, B, C should succeed; D should fail
        statuses = {tr["task_id"]: tr["status"] for tr in exec_data["task_results"]}
        assert statuses["A"] == "completed"
        assert statuses["B"] == "completed"
        assert statuses["C"] == "completed"
        assert statuses["D"] == "failed"

        from app.services.workflow_engine import LogOutput

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="ok"),
        ):
            resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")

        data = resp.json()
        assert data["status"] == "completed"
        # All four results should now be completed
        assert len(data["task_results"]) == 4
        assert all(tr["status"] == "completed" for tr in data["task_results"])


# ===========================================================================
# Test class: Metadata & bookkeeping
# ===========================================================================


class TestRetryMetadata:
    """Verify metadata, trigger field, and timestamps on retried executions."""

    def test_trigger_is_retry(self, client):
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp.json()["trigger"] == "retry"

    def test_metadata_contains_retried_from(self, client):
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp.json()["metadata"]["retried_from"] == exec_data["id"]

    def test_retry_has_started_at(self, client):
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp.json()["started_at"] is not None

    def test_retry_has_completed_at(self, client):
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp.json()["completed_at"] is not None

    def test_retry_workflow_id_matches_original(self, client):
        wf_id = _create_failing_workflow(client)
        exec_data = _execute(client, wf_id)

        resp = client.post(f"/api/tasks/executions/{exec_data['id']}/retry")
        assert resp.json()["workflow_id"] == exec_data["workflow_id"]


# ===========================================================================
# Test class: Service-layer unit tests (no HTTP)
# ===========================================================================


class TestRetryServiceLayer:
    """Direct tests against workflow_engine.retry_execution."""

    def test_retry_returns_none_for_missing_id(self):
        from app.services.workflow_engine import retry_execution

        assert retry_execution("nonexistent") is None

    def test_retry_raises_for_non_failed(self):
        from app.services.workflow_engine import retry_execution

        wf = create_workflow(WorkflowCreate(name="Good", tasks=[]))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED

        with pytest.raises(ValueError, match="Only failed executions"):
            retry_execution(ex.id)

    def test_retry_raises_when_workflow_deleted(self):
        from app.services.workflow_engine import retry_execution, delete_workflow

        wf = create_workflow(
            WorkflowCreate(
                name="DeleteMe",
                tasks=[
                    {"name": "Bad", "action": "unknown_action", "parameters": {}},
                ],
            )
        )
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.FAILED

        delete_workflow(wf.id)
        with pytest.raises(ValueError, match="no longer exists"):
            retry_execution(ex.id)

    def test_retry_stores_execution_in_registry(self):
        from app.services.workflow_engine import retry_execution

        wf = create_workflow(
            WorkflowCreate(
                name="Stored",
                tasks=[
                    {"name": "Bad", "action": "unknown_action", "parameters": {}},
                ],
            )
        )
        ex = execute_workflow(wf.id)
        retry_ex = retry_execution(ex.id)
        assert retry_ex is not None
        assert get_execution(retry_ex.id) is not None

    def test_retry_listed_in_executions(self):
        from app.services.workflow_engine import retry_execution, list_executions

        wf = create_workflow(
            WorkflowCreate(
                name="Listed",
                tasks=[
                    {"name": "Bad", "action": "unknown_action", "parameters": {}},
                ],
            )
        )
        ex = execute_workflow(wf.id)
        retry_execution(ex.id)
        execs = list_executions(workflow_id=wf.id)
        assert len(execs) == 2  # original + retry
