"""Tests for Pydantic model validators on TaskDefinition, WorkflowCreate, and WorkflowUpdate."""

import pytest
from pydantic import ValidationError

from app.models import (
    TaskDefinition,
    WorkflowCreate,
    WorkflowUpdate,
    validate_cron_expression,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _task(*, name="step", action="log", **overrides):
    """Build a minimal valid TaskDefinition with optional overrides."""
    return TaskDefinition(name=name, action=action, **overrides)


def _workflow(*, name="My Workflow", **overrides):
    """Build a minimal valid WorkflowCreate with optional overrides."""
    return WorkflowCreate(name=name, **overrides)


# ===========================================================================
# TaskDefinition.name validation
# ===========================================================================

class TestTaskDefinitionName:
    def test_valid_short_name(self):
        t = _task(name="a")
        assert t.name == "a"

    def test_valid_name_at_max_length(self):
        name = "x" * 200
        t = _task(name=name)
        assert t.name == name

    def test_whitespace_is_stripped(self):
        t = _task(name="  hello  ")
        assert t.name == "hello"

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            _task(name="")

    def test_whitespace_only_name_rejected(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            _task(name="   ")

    def test_name_exceeding_max_length_rejected(self):
        with pytest.raises(ValidationError, match="at most 200"):
            _task(name="a" * 201)

    def test_name_with_unicode(self):
        t = _task(name="étape-données")
        assert t.name == "étape-données"

    def test_name_with_special_characters(self):
        t = _task(name="step #1 (retry)")
        assert t.name == "step #1 (retry)"


# ===========================================================================
# TaskDefinition.action validation
# ===========================================================================

class TestTaskDefinitionAction:
    def test_valid_simple_action(self):
        t = _task(action="log")
        assert t.action == "log"

    def test_valid_action_with_underscores(self):
        t = _task(action="send_email")
        assert t.action == "send_email"

    def test_valid_action_with_hyphens(self):
        t = _task(action="run-pipeline")
        assert t.action == "run-pipeline"

    def test_valid_action_with_dots(self):
        t = _task(action="data.transform.v2")
        assert t.action == "data.transform.v2"

    def test_valid_action_with_mixed_chars(self):
        t = _task(action="myOrg.run_task-v3")
        assert t.action == "myOrg.run_task-v3"

    def test_action_stripped_of_whitespace(self):
        t = _task(action="  log  ")
        assert t.action == "log"

    def test_empty_action_rejected(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            _task(action="")

    def test_whitespace_only_action_rejected(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            _task(action="   ")

    def test_action_starting_with_digit_rejected(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            _task(action="1bad")

    def test_action_with_spaces_rejected(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            _task(action="my action")

    def test_action_with_special_chars_rejected(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            _task(action="run@home")

    def test_action_starting_with_underscore_rejected(self):
        with pytest.raises(ValidationError, match="invalid characters"):
            _task(action="_private")


# ===========================================================================
# TaskDefinition.timeout_seconds validation
# ===========================================================================

class TestTaskDefinitionTimeout:
    def test_default_timeout(self):
        t = _task()
        assert t.timeout_seconds == 300

    def test_valid_positive_timeout(self):
        t = _task(timeout_seconds=60)
        assert t.timeout_seconds == 60

    def test_timeout_of_one(self):
        t = _task(timeout_seconds=1)
        assert t.timeout_seconds == 1

    def test_large_timeout(self):
        t = _task(timeout_seconds=86400)
        assert t.timeout_seconds == 86400

    def test_zero_timeout_rejected(self):
        with pytest.raises(ValidationError, match="must be positive"):
            _task(timeout_seconds=0)

    def test_negative_timeout_rejected(self):
        with pytest.raises(ValidationError, match="must be positive"):
            _task(timeout_seconds=-10)


# ===========================================================================
# TaskDefinition.retry_count validation
# ===========================================================================

class TestTaskDefinitionRetryCount:
    def test_default_retry_count(self):
        t = _task()
        assert t.retry_count == 0

    def test_zero_retries(self):
        t = _task(retry_count=0)
        assert t.retry_count == 0

    def test_max_retries(self):
        t = _task(retry_count=10)
        assert t.retry_count == 10

    def test_mid_range_retries(self):
        t = _task(retry_count=5)
        assert t.retry_count == 5

    def test_negative_retry_rejected(self):
        with pytest.raises(ValidationError, match="between 0 and 10"):
            _task(retry_count=-1)

    def test_retry_above_max_rejected(self):
        with pytest.raises(ValidationError, match="between 0 and 10"):
            _task(retry_count=11)

    def test_retry_far_above_max_rejected(self):
        with pytest.raises(ValidationError, match="between 0 and 10"):
            _task(retry_count=100)


# ===========================================================================
# WorkflowCreate.name validation
# ===========================================================================

class TestWorkflowCreateName:
    def test_valid_name(self):
        wf = _workflow(name="Daily ETL")
        assert wf.name == "Daily ETL"

    def test_name_stripped(self):
        wf = _workflow(name="  padded  ")
        assert wf.name == "padded"

    def test_name_at_max_length(self):
        name = "w" * 200
        wf = _workflow(name=name)
        assert wf.name == name

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            _workflow(name="")

    def test_whitespace_only_name_rejected(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            _workflow(name="\t\n ")

    def test_name_over_max_rejected(self):
        with pytest.raises(ValidationError, match="at most 200"):
            _workflow(name="n" * 201)


# ===========================================================================
# WorkflowCreate.schedule (cron) validation
# ===========================================================================

class TestWorkflowCreateSchedule:
    def test_none_schedule_allowed(self):
        wf = _workflow(schedule=None)
        assert wf.schedule is None

    def test_valid_every_minute(self):
        wf = _workflow(schedule="* * * * *")
        assert wf.schedule == "* * * * *"

    def test_valid_hourly(self):
        wf = _workflow(schedule="0 * * * *")
        assert wf.schedule == "0 * * * *"

    def test_valid_daily_at_8am(self):
        wf = _workflow(schedule="0 8 * * *")
        assert wf.schedule == "0 8 * * *"

    def test_valid_with_step(self):
        wf = _workflow(schedule="*/5 * * * *")
        assert wf.schedule == "*/5 * * * *"

    def test_valid_weekday_only(self):
        wf = _workflow(schedule="30 9 * * 1-5")
        assert wf.schedule == "30 9 * * 1-5"

    def test_schedule_stripped(self):
        wf = _workflow(schedule="  0 * * * *  ")
        assert wf.schedule == "0 * * * *"

    def test_empty_string_becomes_none(self):
        wf = _workflow(schedule="")
        assert wf.schedule is None

    def test_whitespace_only_becomes_none(self):
        wf = _workflow(schedule="   ")
        assert wf.schedule is None

    def test_invalid_too_few_fields(self):
        with pytest.raises(ValidationError, match="Invalid cron"):
            _workflow(schedule="* *")

    def test_invalid_too_many_fields(self):
        with pytest.raises(ValidationError, match="Invalid cron"):
            _workflow(schedule="* * * * * *")

    def test_invalid_text(self):
        with pytest.raises(ValidationError, match="Invalid cron"):
            _workflow(schedule="every day at noon")

    def test_invalid_weekday_value(self):
        with pytest.raises(ValidationError, match="Invalid cron"):
            _workflow(schedule="0 0 * * 8")


# ===========================================================================
# WorkflowUpdate validators
# ===========================================================================

class TestWorkflowUpdateName:
    def test_none_name_allowed(self):
        wu = WorkflowUpdate(name=None)
        assert wu.name is None

    def test_valid_name(self):
        wu = WorkflowUpdate(name="Updated Pipeline")
        assert wu.name == "Updated Pipeline"

    def test_name_stripped(self):
        wu = WorkflowUpdate(name="  trimmed  ")
        assert wu.name == "trimmed"

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            WorkflowUpdate(name="")

    def test_whitespace_only_rejected(self):
        with pytest.raises(ValidationError, match="must not be empty"):
            WorkflowUpdate(name="   ")

    def test_over_max_length_rejected(self):
        with pytest.raises(ValidationError, match="at most 200"):
            WorkflowUpdate(name="z" * 201)


class TestWorkflowUpdateSchedule:
    def test_none_schedule_allowed(self):
        wu = WorkflowUpdate(schedule=None)
        assert wu.schedule is None

    def test_valid_schedule(self):
        wu = WorkflowUpdate(schedule="30 8 * * 1")
        assert wu.schedule == "30 8 * * 1"

    def test_empty_becomes_none(self):
        wu = WorkflowUpdate(schedule="")
        assert wu.schedule is None

    def test_invalid_schedule_rejected(self):
        with pytest.raises(ValidationError, match="Invalid cron"):
            WorkflowUpdate(schedule="bad cron")

    def test_schedule_stripped(self):
        wu = WorkflowUpdate(schedule="  */10 * * * *  ")
        assert wu.schedule == "*/10 * * * *"


# ===========================================================================
# validate_cron_expression standalone function
# ===========================================================================

class TestValidateCronExpression:
    def test_every_minute(self):
        assert validate_cron_expression("* * * * *") is True

    def test_specific_minute_and_hour(self):
        assert validate_cron_expression("30 8 * * *") is True

    def test_step_expression(self):
        assert validate_cron_expression("*/15 * * * *") is True

    def test_range_expression(self):
        assert validate_cron_expression("0 9-17 * * *") is True

    def test_day_of_week_range(self):
        assert validate_cron_expression("0 0 * * 1-5") is True

    def test_empty_string(self):
        assert validate_cron_expression("") is False

    def test_too_few_fields(self):
        assert validate_cron_expression("* *") is False

    def test_too_many_fields(self):
        assert validate_cron_expression("* * * * * *") is False

    def test_non_numeric(self):
        assert validate_cron_expression("foo bar baz qux quux") is False

    def test_invalid_weekday_8(self):
        assert validate_cron_expression("0 0 * * 8") is False
