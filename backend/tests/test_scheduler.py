"""Tests for the task scheduler service."""

import pytest
from datetime import datetime, timedelta

from app.services.task_scheduler import (
    clear_schedules,
    compute_next_run,
    get_due_schedules,
    get_schedule,
    list_schedules,
    mark_executed,
    register_schedule,
    toggle_schedule,
    unregister_schedule,
    validate_cron,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_schedules()
    yield
    clear_schedules()


class TestValidateCron:
    def test_valid_expressions(self):
        assert validate_cron("0 * * * *") is True
        assert validate_cron("30 8 * * 1") is True
        assert validate_cron("*/5 * * * *") is True
        assert validate_cron("0 0 1 1 *") is True

    def test_invalid_expressions(self):
        assert validate_cron("") is False
        assert validate_cron("* *") is False
        assert validate_cron("60 * * * *") is False  # still matches the regex pattern
        assert validate_cron("not a cron") is False
        assert validate_cron("* * * * * *") is False  # 6 fields


class TestRegisterSchedule:
    def test_register_valid(self):
        entry = register_schedule("wf-1", "0 8 * * *")
        assert entry.workflow_id == "wf-1"
        assert entry.enabled is True
        assert entry.next_run is not None

    def test_register_with_tags(self):
        entry = register_schedule("wf-2", "30 * * * *", tags=["prod", "daily"])
        assert entry.tags == ["prod", "daily"]

    def test_register_invalid_cron(self):
        with pytest.raises(ValueError, match="Invalid cron"):
            register_schedule("wf-bad", "not valid")


class TestScheduleOperations:
    def test_unregister(self):
        register_schedule("wf-1", "0 * * * *")
        assert unregister_schedule("wf-1") is True
        assert get_schedule("wf-1") is None

    def test_unregister_nonexistent(self):
        assert unregister_schedule("nope") is False

    def test_list_schedules(self):
        register_schedule("wf-a", "0 * * * *")
        register_schedule("wf-b", "30 * * * *")
        entries = list_schedules()
        assert len(entries) == 2

    def test_list_enabled_only(self):
        register_schedule("wf-a", "0 * * * *")
        register_schedule("wf-b", "30 * * * *")
        toggle_schedule("wf-b", enabled=False)
        entries = list_schedules(enabled_only=True)
        assert len(entries) == 1

    def test_toggle(self):
        register_schedule("wf-1", "0 * * * *")
        entry = toggle_schedule("wf-1", enabled=False)
        assert entry is not None
        assert entry.enabled is False

    def test_toggle_nonexistent(self):
        assert toggle_schedule("nope", enabled=True) is None


class TestDueSchedules:
    def test_due_detection(self):
        entry = register_schedule("wf-due", "0 * * * *")
        # Force next_run to the past
        entry.next_run = datetime.utcnow() - timedelta(minutes=5)
        due = get_due_schedules()
        assert len(due) == 1
        assert due[0].workflow_id == "wf-due"

    def test_not_yet_due(self):
        entry = register_schedule("wf-future", "0 * * * *")
        entry.next_run = datetime.utcnow() + timedelta(hours=1)
        due = get_due_schedules()
        assert len(due) == 0


class TestMarkExecuted:
    def test_mark_increments_count(self):
        register_schedule("wf-1", "0 * * * *")
        mark_executed("wf-1")
        entry = get_schedule("wf-1")
        assert entry is not None
        assert entry.run_count == 1
        assert entry.last_run is not None

    def test_mark_nonexistent(self):
        assert mark_executed("nope") is None


class TestComputeNextRun:
    def test_wildcard(self):
        base = datetime(2026, 1, 15, 10, 30, 0)
        result = compute_next_run("* * * * *", from_time=base)
        assert result == base + timedelta(minutes=1)

    def test_specific_minute(self):
        base = datetime(2026, 1, 15, 10, 15, 0)
        result = compute_next_run("45 * * * *", from_time=base)
        assert result.minute == 45
        assert result.hour == 10

    def test_specific_hour_and_minute(self):
        base = datetime(2026, 1, 15, 10, 30, 0)
        result = compute_next_run("0 8 * * *", from_time=base)
        # 8:00 already passed today, so next day
        assert result.hour == 8
        assert result.minute == 0
        assert result.day == 16
