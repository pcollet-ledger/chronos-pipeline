"""Parametrized tests for backend functions.

Uses @pytest.mark.parametrize for at least 5 functions to cover
a wide range of inputs systematically.
"""

import pytest

from app.models import WorkflowCreate, WorkflowStatus
from app.services.task_scheduler import compute_next_run, validate_cron
from app.services.workflow_engine import (
    _run_action,
    clear_all,
    create_workflow,
    execute_workflow,
    list_workflows,
)
from app.utils.formatters import format_duration
from app.utils.helpers import (
    clamp,
    generate_slug,
)
from app.utils.validators import (
    validate_action_name,
    validate_limit,
    validate_workflow_name,
)
from datetime import datetime


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    yield
    clear_all()


class TestParametrizedSlug:
    @pytest.mark.parametrize("input_name,expected", [
        ("Hello World", "hello-world"),
        ("already-a-slug", "already-a-slug"),
        ("UPPER CASE", "upper-case"),
        ("too   many   spaces", "too-many-spaces"),
        ("My Workflow! (v2)", "my-workflow-v2"),
        ("  leading trailing  ", "leading-trailing"),
        ("under_scores_here", "under-scores-here"),
        ("a", "a"),
        ("123", "123"),
        ("mix-of_everything! 2", "mix-of-everything-2"),
    ])
    def test_generate_slug(self, input_name: str, expected: str):
        assert generate_slug(input_name) == expected


class TestParametrizedFormatDuration:
    @pytest.mark.parametrize("ms,expected", [
        (0, "0ms"),
        (500, "500ms"),
        (999, "999ms"),
        (1000, "1.0s"),
        (5000, "5.0s"),
        (59999, "60.0s"),
        (60000, "1.0m"),
        (120000, "2.0m"),
        (3600000, "1.0h"),
        (7200000, "2.0h"),
    ])
    def test_format_duration(self, ms: float, expected: str):
        assert format_duration(ms) == expected


class TestParametrizedClamp:
    @pytest.mark.parametrize("value,min_val,max_val,expected", [
        (5, 0, 10, 5),
        (-5, 0, 10, 0),
        (15, 0, 10, 10),
        (0, 0, 10, 0),
        (10, 0, 10, 10),
        (0.5, 0, 1, 0.5),
        (-100, -50, 50, -50),
        (100, -50, 50, 50),
        (0, 0, 0, 0),
        (5, 5, 5, 5),
    ])
    def test_clamp(self, value, min_val, max_val, expected):
        assert clamp(value, min_val, max_val) == expected


class TestParametrizedValidateCron:
    @pytest.mark.parametrize("expression,expected", [
        ("* * * * *", True),
        ("0 * * * *", True),
        ("30 8 * * 1", True),
        ("*/5 * * * *", True),
        ("0 0 1 1 *", True),
        ("59 23 31 12 6", True),
        ("", False),
        ("* *", False),
        ("not a cron", False),
        ("* * * * * *", False),
        ("0,15,30,45 * * * *", True),
        ("0-30 * * * *", True),
    ])
    def test_validate_cron(self, expression: str, expected: bool):
        assert validate_cron(expression) is expected


class TestParametrizedRunAction:
    @pytest.mark.parametrize("action,params,expected_key", [
        ("log", {"message": "hi"}, "message"),
        ("log", {}, "message"),
        ("transform", {"a": 1}, "transformed"),
        ("validate", {"key": "val"}, "valid"),
        ("notify", {"channel": "slack"}, "notified"),
        ("aggregate", {"x": 1, "y": 2}, "count"),
    ])
    def test_run_action_returns_expected_key(self, action, params, expected_key):
        result = _run_action(action, params)
        assert expected_key in result

    @pytest.mark.parametrize("action", [
        "unknown",
        "INVALID",
        "",
        "log ",
        " log",
    ])
    def test_run_action_raises_for_invalid(self, action):
        with pytest.raises(ValueError, match="Unknown action"):
            _run_action(action, {})


class TestParametrizedValidateWorkflowName:
    @pytest.mark.parametrize("name,is_valid", [
        ("Valid Name", True),
        ("", False),
        ("   ", False),
        ("A" * 200, True),
        ("A" * 201, False),
        ("X", True),
        ("Unicode 工作流程", True),
    ])
    def test_validate_name(self, name: str, is_valid: bool):
        result = validate_workflow_name(name)
        if is_valid:
            assert result is None
        else:
            assert result is not None


class TestParametrizedValidateActionName:
    @pytest.mark.parametrize("action,is_valid", [
        ("log", True),
        ("transform", True),
        ("validate", True),
        ("notify", True),
        ("aggregate", True),
        ("unknown", False),
        ("", False),
        ("Log", False),
    ])
    def test_validate_action(self, action: str, is_valid: bool):
        result = validate_action_name(action)
        if is_valid:
            assert result is None
        else:
            assert result is not None


class TestParametrizedValidateLimit:
    @pytest.mark.parametrize("limit,is_valid", [
        (1, True),
        (50, True),
        (1000, True),
        (0, False),
        (-1, False),
        (1001, False),
    ])
    def test_validate_limit(self, limit: int, is_valid: bool):
        result = validate_limit(limit)
        if is_valid:
            assert result is None
        else:
            assert result is not None


class TestParametrizedWorkflowExecution:
    @pytest.mark.parametrize("action,expected_status", [
        ("log", "completed"),
        ("validate", "completed"),
        ("transform", "completed"),
        ("notify", "completed"),
        ("aggregate", "completed"),
        ("unknown_action", "failed"),
    ])
    def test_execute_with_different_actions(self, action: str, expected_status: str):
        wf = create_workflow(WorkflowCreate(
            name=f"WF-{action}",
            tasks=[{"name": "S", "action": action, "parameters": {"message": "ok", "channel": "test"}}],
        ))
        ex = execute_workflow(wf.id)
        assert ex.status.value == expected_status
