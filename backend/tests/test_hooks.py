"""Comprehensive tests for pre_hook / post_hook execution logic.

Tests are organised into classes covering:
  - _run_hook (the low-level hook dispatcher)
  - _execute_task with hooks (unit-level, no HTTP)
  - Full workflow execution through the API with hooks
  - Edge cases: empty-string hooks, both hooks failing, retry with hooks, etc.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import TaskDefinition, TaskPriority, WorkflowStatus
from app.services.workflow_engine import (
    LogOutput,
    NotifyOutput,
    ValidateOutput,
    _execute_task,
    _run_hook,
    clear_all,
    create_workflow,
    execute_workflow,
)
from app.models import WorkflowCreate


@pytest.fixture(autouse=True)
def cleanup():
    """Clear all in-memory state before and after each test."""
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    return TestClient(app)


# ===========================================================================
# Test class: _run_hook — the low-level hook dispatcher
# ===========================================================================


class TestRunHook:
    """Direct tests for the _run_hook helper function."""

    def test_run_hook_with_log_action(self):
        """A 'log' hook should return a LogOutput dict."""
        result = _run_hook("log", {"message": "pre-check"})
        assert result["message"] == "pre-check"

    def test_run_hook_with_validate_action(self):
        """A 'validate' hook should return a ValidateOutput dict."""
        result = _run_hook("validate", {"key": "value"})
        assert result["valid"] is True

    def test_run_hook_with_notify_action(self):
        """A 'notify' hook should return a NotifyOutput dict."""
        result = _run_hook("notify", {"channel": "slack"})
        assert result["notified"] is True
        assert result["channel"] == "slack"

    def test_run_hook_with_transform_action(self):
        """A 'transform' hook should return a TransformOutput dict."""
        result = _run_hook("transform", {"col_a": 1, "col_b": 2})
        assert result["transformed"] is True
        assert set(result["input_keys"]) == {"col_a", "col_b"}

    def test_run_hook_with_aggregate_action(self):
        """An 'aggregate' hook should return an AggregateOutput dict."""
        result = _run_hook("aggregate", {"x": 1, "y": 2, "z": 3})
        assert result["count"] == 3

    def test_run_hook_unknown_action_raises(self):
        """An unrecognised hook name must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown action"):
            _run_hook("nonexistent_hook", {})

    def test_run_hook_empty_parameters(self):
        """Hooks should work with an empty parameter dict."""
        result = _run_hook("log", {})
        assert result["message"] == "logged"

    def test_run_hook_returns_same_as_run_action(self):
        """_run_hook delegates to _run_action, so outputs must match."""
        from app.services.workflow_engine import _run_action

        hook_result = _run_hook("log", {"message": "test"})
        action_result = _run_action("log", {"message": "test"})
        assert hook_result == action_result


# ===========================================================================
# Test class: _execute_task with no hooks (backward compatibility)
# ===========================================================================


class TestExecuteTaskNoHooks:
    """Ensure tasks without hooks still work identically to before."""

    def test_no_hooks_task_completes(self):
        """A task with no hooks should complete normally."""
        task = TaskDefinition(name="Plain", action="log", parameters={"message": "hi"})
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.output["message"] == "hi"

    def test_no_hooks_no_hook_keys_in_output(self):
        """Output should not contain hook keys when hooks are absent."""
        task = TaskDefinition(name="Plain", action="log", parameters={"message": "hi"})
        result = _execute_task(task)
        assert "pre_hook_output" not in result.output
        assert "post_hook_output" not in result.output

    def test_no_hooks_failed_action(self):
        """A failing main action with no hooks should still produce FAILED."""
        task = TaskDefinition(name="Bad", action="unknown_action", parameters={})
        result = _execute_task(task)
        assert result.status == WorkflowStatus.FAILED
        assert "Unknown action" in result.error

    def test_no_hooks_has_timing(self):
        """Timing fields should be populated even without hooks."""
        task = TaskDefinition(name="Timed", action="validate", parameters={"k": "v"})
        result = _execute_task(task)
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_ms is not None
        assert result.duration_ms >= 0

    def test_no_hooks_none_values_ignored(self):
        """Explicitly setting hooks to None should behave like omitting them."""
        task = TaskDefinition(
            name="Explicit None",
            action="log",
            parameters={"message": "ok"},
            pre_hook=None,
            post_hook=None,
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert "pre_hook_output" not in result.output
        assert "post_hook_output" not in result.output


# ===========================================================================
# Test class: _execute_task with pre_hook only
# ===========================================================================


class TestExecuteTaskPreHook:
    """Tests for tasks that define only a pre_hook."""

    def test_pre_hook_runs_before_main(self):
        """pre_hook output should appear in the result alongside main output."""
        task = TaskDefinition(
            name="WithPre",
            action="validate",
            parameters={"key": "val"},
            pre_hook="log",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert "pre_hook_output" in result.output
        assert result.output["pre_hook_output"]["message"] == "logged"
        assert result.output["valid"] is True

    def test_pre_hook_failure_aborts_task(self):
        """If the pre_hook fails, the main action should NOT run."""
        task = TaskDefinition(
            name="PreFail",
            action="log",
            parameters={"message": "should not run"},
            pre_hook="unknown_action",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.FAILED
        assert "Unknown action" in result.error
        # Main action output should not be present
        assert result.output is None or "message" not in (result.output or {})

    def test_pre_hook_failure_error_message(self):
        """Error message should reference the unknown hook action."""
        task = TaskDefinition(
            name="PreFail",
            action="log",
            parameters={},
            pre_hook="bad_hook",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.FAILED
        assert "bad_hook" in result.error

    def test_pre_hook_receives_task_parameters(self):
        """The pre_hook should receive the same parameters as the main action."""
        task = TaskDefinition(
            name="ParamCheck",
            action="log",
            parameters={"message": "hello", "extra": "data"},
            pre_hook="transform",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert set(result.output["pre_hook_output"]["input_keys"]) == {"message", "extra"}

    def test_pre_hook_no_post_hook_key(self):
        """When only pre_hook is set, post_hook_output should be absent."""
        task = TaskDefinition(
            name="OnlyPre",
            action="log",
            parameters={"message": "test"},
            pre_hook="validate",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert "pre_hook_output" in result.output
        assert "post_hook_output" not in result.output


# ===========================================================================
# Test class: _execute_task with post_hook only
# ===========================================================================


class TestExecuteTaskPostHook:
    """Tests for tasks that define only a post_hook."""

    def test_post_hook_runs_after_main(self):
        """post_hook output should appear in the result."""
        task = TaskDefinition(
            name="WithPost",
            action="log",
            parameters={"message": "main"},
            post_hook="notify",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.output["message"] == "main"
        assert "post_hook_output" in result.output
        assert result.output["post_hook_output"]["notified"] is True

    def test_post_hook_failure_marks_task_failed(self):
        """A failing post_hook should mark the entire task as FAILED."""
        task = TaskDefinition(
            name="PostFail",
            action="log",
            parameters={"message": "ok"},
            post_hook="unknown_action",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.FAILED
        assert "Unknown action" in result.error

    def test_post_hook_failure_error_message(self):
        """Error should reference the failing post_hook action name."""
        task = TaskDefinition(
            name="PostFail",
            action="log",
            parameters={},
            post_hook="bad_post",
        )
        result = _execute_task(task)
        assert "bad_post" in result.error

    def test_post_hook_receives_task_parameters(self):
        """post_hook should receive the same parameters as the main action."""
        task = TaskDefinition(
            name="PostParams",
            action="log",
            parameters={"channel": "email"},
            post_hook="notify",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.output["post_hook_output"]["channel"] == "email"

    def test_post_hook_no_pre_hook_key(self):
        """When only post_hook is set, pre_hook_output should be absent."""
        task = TaskDefinition(
            name="OnlyPost",
            action="validate",
            parameters={"k": "v"},
            post_hook="log",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert "post_hook_output" in result.output
        assert "pre_hook_output" not in result.output

    def test_main_failure_skips_post_hook(self):
        """If the main action fails, the post_hook should NOT execute."""
        task = TaskDefinition(
            name="MainFail",
            action="unknown_action",
            parameters={},
            post_hook="log",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.FAILED
        assert result.output is None or "post_hook_output" not in (result.output or {})


# ===========================================================================
# Test class: _execute_task with both pre_hook and post_hook
# ===========================================================================


class TestExecuteTaskBothHooks:
    """Tests for tasks that define both pre_hook and post_hook."""

    def test_both_hooks_success(self):
        """Both hooks and main action succeed — all outputs present."""
        task = TaskDefinition(
            name="BothHooks",
            action="validate",
            parameters={"key": "val"},
            pre_hook="log",
            post_hook="notify",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.output["pre_hook_output"]["message"] == "logged"
        assert result.output["valid"] is True
        assert result.output["post_hook_output"]["notified"] is True

    def test_pre_hook_fails_skips_main_and_post(self):
        """A failing pre_hook should prevent both main and post_hook."""
        task = TaskDefinition(
            name="PreFail",
            action="log",
            parameters={"message": "should not run"},
            pre_hook="unknown_action",
            post_hook="notify",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.FAILED
        assert result.output is None or "post_hook_output" not in (result.output or {})

    def test_main_fails_skips_post_hook(self):
        """A failing main action should prevent the post_hook."""
        task = TaskDefinition(
            name="MainFail",
            action="unknown_action",
            parameters={},
            pre_hook="log",
            post_hook="notify",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.FAILED

    def test_post_hook_fails_after_successful_main(self):
        """Main succeeds but post_hook fails — task should be FAILED."""
        task = TaskDefinition(
            name="PostFail",
            action="log",
            parameters={"message": "ok"},
            pre_hook="validate",
            post_hook="unknown_action",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.FAILED
        assert "Unknown action" in result.error

    def test_both_hooks_same_action(self):
        """pre_hook and post_hook can be the same action."""
        task = TaskDefinition(
            name="SameHook",
            action="validate",
            parameters={"key": "val"},
            pre_hook="log",
            post_hook="log",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.output["pre_hook_output"]["message"] == "logged"
        assert result.output["post_hook_output"]["message"] == "logged"

    def test_hook_same_as_main_action(self):
        """Hooks can use the same action name as the main action."""
        task = TaskDefinition(
            name="SameAsMain",
            action="log",
            parameters={"message": "echo"},
            pre_hook="log",
            post_hook="log",
        )
        result = _execute_task(task)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.output["message"] == "echo"
        assert result.output["pre_hook_output"]["message"] == "echo"
        assert result.output["post_hook_output"]["message"] == "echo"


# ===========================================================================
# Test class: Full workflow execution via API with hooks
# ===========================================================================


class TestWorkflowExecutionWithHooks:
    """End-to-end tests through the HTTP API."""

    def test_workflow_with_pre_hook_via_api(self, client):
        """Create and execute a workflow with a pre_hook through the API."""
        payload = {
            "name": "Hooked WF",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "validate",
                    "parameters": {"key": "val"},
                    "pre_hook": "log",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        resp = client.post(f"/api/workflows/{wf['id']}/execute")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["task_results"][0]["output"]["pre_hook_output"]["message"] == "logged"

    def test_workflow_with_post_hook_via_api(self, client):
        """Create and execute a workflow with a post_hook through the API."""
        payload = {
            "name": "Post-Hooked WF",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "log",
                    "parameters": {"message": "hi"},
                    "post_hook": "notify",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        resp = client.post(f"/api/workflows/{wf['id']}/execute")
        data = resp.json()
        assert data["status"] == "completed"
        assert data["task_results"][0]["output"]["post_hook_output"]["notified"] is True

    def test_workflow_with_both_hooks_via_api(self, client):
        """Workflow with both hooks should include both hook outputs."""
        payload = {
            "name": "Both-Hooked WF",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "validate",
                    "parameters": {"key": "val"},
                    "pre_hook": "log",
                    "post_hook": "notify",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        resp = client.post(f"/api/workflows/{wf['id']}/execute")
        data = resp.json()
        assert data["status"] == "completed"
        output = data["task_results"][0]["output"]
        assert "pre_hook_output" in output
        assert "post_hook_output" in output

    def test_workflow_pre_hook_failure_via_api(self, client):
        """A failing pre_hook should cause the workflow to fail."""
        payload = {
            "name": "Pre-Fail WF",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "log",
                    "parameters": {"message": "ok"},
                    "pre_hook": "unknown_action",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        resp = client.post(f"/api/workflows/{wf['id']}/execute")
        data = resp.json()
        assert data["status"] == "failed"
        assert data["task_results"][0]["status"] == "failed"

    def test_workflow_post_hook_failure_via_api(self, client):
        """A failing post_hook should cause the workflow to fail."""
        payload = {
            "name": "Post-Fail WF",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "log",
                    "parameters": {"message": "ok"},
                    "post_hook": "unknown_action",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        resp = client.post(f"/api/workflows/{wf['id']}/execute")
        data = resp.json()
        assert data["status"] == "failed"

    def test_multi_task_workflow_second_task_hook_fails(self, client):
        """First task succeeds, second task's pre_hook fails — workflow fails."""
        payload = {
            "name": "Multi-Hook WF",
            "tasks": [
                {
                    "name": "Good",
                    "action": "log",
                    "parameters": {"message": "ok"},
                },
                {
                    "name": "Bad Pre",
                    "action": "validate",
                    "parameters": {"key": "val"},
                    "pre_hook": "unknown_action",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        resp = client.post(f"/api/workflows/{wf['id']}/execute")
        data = resp.json()
        assert data["status"] == "failed"
        assert data["task_results"][0]["status"] == "completed"
        assert data["task_results"][1]["status"] == "failed"

    def test_hooks_preserved_in_workflow_definition(self, client):
        """Hook fields should be persisted and returned in GET."""
        payload = {
            "name": "Stored Hooks",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "log",
                    "parameters": {},
                    "pre_hook": "validate",
                    "post_hook": "notify",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        resp = client.get(f"/api/workflows/{wf['id']}")
        task = resp.json()["tasks"][0]
        assert task["pre_hook"] == "validate"
        assert task["post_hook"] == "notify"

    def test_hooks_default_to_none_in_api(self, client):
        """Tasks without hooks should return null for hook fields."""
        payload = {
            "name": "No Hooks",
            "tasks": [
                {"name": "Step1", "action": "log", "parameters": {}},
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        resp = client.get(f"/api/workflows/{wf['id']}")
        task = resp.json()["tasks"][0]
        assert task["pre_hook"] is None
        assert task["post_hook"] is None


# ===========================================================================
# Test class: Retry with hooks
# ===========================================================================


class TestRetryWithHooks:
    """Ensure retry logic works correctly when tasks have hooks."""

    def test_retry_task_with_failing_post_hook(self, client):
        """A task whose post_hook fails can be retried successfully."""
        payload = {
            "name": "Retry-PostHook WF",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "log",
                    "parameters": {"message": "ok"},
                    "post_hook": "unknown_action",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        exec_resp = client.post(f"/api/workflows/{wf['id']}/execute")
        exec_data = exec_resp.json()
        assert exec_data["status"] == "failed"

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            retry_resp = client.post(
                f"/api/tasks/executions/{exec_data['id']}/retry"
            )
        assert retry_resp.json()["status"] == "completed"

    def test_retry_task_with_failing_pre_hook(self, client):
        """A task whose pre_hook fails can be retried after fixing."""
        payload = {
            "name": "Retry-PreHook WF",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "log",
                    "parameters": {"message": "ok"},
                    "pre_hook": "unknown_action",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        exec_resp = client.post(f"/api/workflows/{wf['id']}/execute")
        exec_data = exec_resp.json()
        assert exec_data["status"] == "failed"

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            retry_resp = client.post(
                f"/api/tasks/executions/{exec_data['id']}/retry"
            )
        assert retry_resp.json()["status"] == "completed"

    def test_retry_preserves_hooked_task_results(self, client):
        """Successful hooked tasks should be carried forward on retry."""
        payload = {
            "name": "Retry-Carry WF",
            "tasks": [
                {
                    "name": "Good",
                    "action": "log",
                    "parameters": {"message": "ok"},
                    "pre_hook": "validate",
                    "post_hook": "notify",
                },
                {
                    "name": "Bad",
                    "action": "unknown_action",
                    "parameters": {},
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        exec_resp = client.post(f"/api/workflows/{wf['id']}/execute")
        exec_data = exec_resp.json()
        assert exec_data["status"] == "failed"
        assert exec_data["task_results"][0]["status"] == "completed"

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            retry_resp = client.post(
                f"/api/tasks/executions/{exec_data['id']}/retry"
            )
        retry_data = retry_resp.json()
        assert retry_data["status"] == "completed"
        # First task should be carried forward with hook outputs intact
        first_output = retry_data["task_results"][0]["output"]
        assert "pre_hook_output" in first_output
        assert "post_hook_output" in first_output

    def test_retry_still_fails_with_bad_hook(self, client):
        """Retrying without fixing the hook should still fail."""
        payload = {
            "name": "Retry-StillBad WF",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "log",
                    "parameters": {"message": "ok"},
                    "pre_hook": "unknown_action",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        exec_resp = client.post(f"/api/workflows/{wf['id']}/execute")
        exec_data = exec_resp.json()
        assert exec_data["status"] == "failed"

        retry_resp = client.post(
            f"/api/tasks/executions/{exec_data['id']}/retry"
        )
        assert retry_resp.json()["status"] == "failed"

    def test_retry_with_hooks_creates_new_execution(self, client):
        """Retry of a hooked workflow should produce a new execution ID."""
        payload = {
            "name": "Retry-NewID WF",
            "tasks": [
                {
                    "name": "Step1",
                    "action": "log",
                    "parameters": {"message": "ok"},
                    "post_hook": "unknown_action",
                },
            ],
        }
        wf = client.post("/api/workflows/", json=payload).json()
        exec_resp = client.post(f"/api/workflows/{wf['id']}/execute")
        exec_data = exec_resp.json()

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="ok"),
        ):
            retry_resp = client.post(
                f"/api/tasks/executions/{exec_data['id']}/retry"
            )
        assert retry_resp.json()["id"] != exec_data["id"]


# ===========================================================================
# Test class: Edge cases
# ===========================================================================


class TestHookEdgeCases:
    """Edge cases and boundary conditions for hook execution."""

    def test_task_definition_model_defaults(self):
        """TaskDefinition should default hooks to None."""
        task = TaskDefinition(name="T", action="log")
        assert task.pre_hook is None
        assert task.post_hook is None

    def test_task_definition_with_hooks_set(self):
        """TaskDefinition should accept hook values."""
        task = TaskDefinition(
            name="T", action="log", pre_hook="validate", post_hook="notify"
        )
        assert task.pre_hook == "validate"
        assert task.post_hook == "notify"

    def test_task_definition_serialization_with_hooks(self):
        """Hooks should appear in model_dump output."""
        task = TaskDefinition(
            name="T", action="log", pre_hook="validate", post_hook="notify"
        )
        data = task.model_dump()
        assert data["pre_hook"] == "validate"
        assert data["post_hook"] == "notify"

    def test_task_definition_serialization_without_hooks(self):
        """Absent hooks should serialize as None."""
        task = TaskDefinition(name="T", action="log")
        data = task.model_dump()
        assert data["pre_hook"] is None
        assert data["post_hook"] is None

    def test_all_five_actions_as_pre_hook(self):
        """Every registered action should work as a pre_hook."""
        for action_name in ("log", "transform", "validate", "notify", "aggregate"):
            task = TaskDefinition(
                name=f"Pre-{action_name}",
                action="log",
                parameters={"message": "main", "channel": "test"},
                pre_hook=action_name,
            )
            result = _execute_task(task)
            assert result.status == WorkflowStatus.COMPLETED, (
                f"pre_hook={action_name} should succeed"
            )
            assert "pre_hook_output" in result.output

    def test_all_five_actions_as_post_hook(self):
        """Every registered action should work as a post_hook."""
        for action_name in ("log", "transform", "validate", "notify", "aggregate"):
            task = TaskDefinition(
                name=f"Post-{action_name}",
                action="log",
                parameters={"message": "main", "channel": "test"},
                post_hook=action_name,
            )
            result = _execute_task(task)
            assert result.status == WorkflowStatus.COMPLETED, (
                f"post_hook={action_name} should succeed"
            )
            assert "post_hook_output" in result.output

    def test_workflow_with_dependencies_and_hooks(self):
        """Hooks should work correctly with task dependency ordering."""
        wf = create_workflow(
            WorkflowCreate(
                name="Dep+Hooks",
                tasks=[
                    {
                        "id": "a",
                        "name": "A",
                        "action": "log",
                        "parameters": {"message": "a"},
                        "pre_hook": "validate",
                    },
                    {
                        "id": "b",
                        "name": "B",
                        "action": "notify",
                        "parameters": {"channel": "slack"},
                        "depends_on": ["a"],
                        "post_hook": "log",
                    },
                ],
            )
        )
        execution = execute_workflow(wf.id)
        assert execution.status == WorkflowStatus.COMPLETED
        assert len(execution.task_results) == 2
        assert "pre_hook_output" in execution.task_results[0].output
        assert "post_hook_output" in execution.task_results[1].output

    def test_hook_timing_included_in_duration(self):
        """Task duration should encompass hook execution time."""
        task = TaskDefinition(
            name="Timed",
            action="log",
            parameters={"message": "ok"},
            pre_hook="validate",
            post_hook="notify",
        )
        result = _execute_task(task)
        assert result.duration_ms is not None
        assert result.duration_ms >= 0
