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
        assert validate_cron("60 * * * *") is False
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


class TestOverlappingSchedules:
    """Multiple schedules whose next_run times coincide."""

    def test_multiple_due_at_same_time(self):
        """All schedules targeting the same minute should all appear as due."""
        now = datetime.utcnow()
        past = now - timedelta(minutes=1)

        entry_a = register_schedule("wf-overlap-a", "0 * * * *")
        entry_b = register_schedule("wf-overlap-b", "0 * * * *")
        entry_c = register_schedule("wf-overlap-c", "0 * * * *")

        entry_a.next_run = past
        entry_b.next_run = past
        entry_c.next_run = past

        due = get_due_schedules()
        due_ids = {e.workflow_id for e in due}
        assert due_ids == {"wf-overlap-a", "wf-overlap-b", "wf-overlap-c"}

    def test_mixed_due_and_pending(self):
        """Only past-due schedules should be returned, not future ones."""
        now = datetime.utcnow()

        entry_due = register_schedule("wf-due-now", "0 * * * *")
        entry_future = register_schedule("wf-later", "30 * * * *")

        entry_due.next_run = now - timedelta(minutes=2)
        entry_future.next_run = now + timedelta(hours=1)

        due = get_due_schedules()
        assert len(due) == 1
        assert due[0].workflow_id == "wf-due-now"

    def test_overlapping_list_order(self):
        """Schedules with the same next_run should all appear in list_schedules."""
        shared_time = datetime(2026, 6, 1, 12, 0, 0)

        for i in range(5):
            entry = register_schedule(f"wf-ov-{i}", "0 12 * * *")
            entry.next_run = shared_time

        entries = list_schedules()
        assert len(entries) == 5


class TestReRegistration:
    """Re-registering the same workflow_id should overwrite the previous entry."""

    def test_reregister_overwrites_entry(self):
        original = register_schedule("wf-dup", "0 * * * *", tags=["v1"])
        mark_executed("wf-dup")
        assert get_schedule("wf-dup").run_count == 1

        replacement = register_schedule("wf-dup", "30 * * * *", tags=["v2"])
        entry = get_schedule("wf-dup")
        assert entry.cron_expression == "30 * * * *"
        assert entry.tags == ["v2"]
        assert entry.run_count == 0, "Re-registration should reset run_count"

    def test_reregister_preserves_single_entry(self):
        register_schedule("wf-dup", "0 * * * *")
        register_schedule("wf-dup", "15 * * * *")
        assert len(list_schedules()) == 1

    def test_reregister_updates_next_run(self):
        base = datetime(2026, 3, 10, 10, 0, 0)
        register_schedule("wf-dup", "0 * * * *")
        replacement = register_schedule("wf-dup", "45 * * * *")
        assert replacement.next_run is not None
        assert replacement.next_run.minute == 45


class TestBoundaryCronMinutes:
    """Boundary values for the minute field: 0 and 59."""

    def test_minute_zero(self):
        base = datetime(2026, 1, 15, 10, 1, 0)
        result = compute_next_run("0 * * * *", from_time=base)
        assert result.minute == 0
        assert result.hour == 11, "Minute 0 already passed this hour, advance to next"

    def test_minute_zero_exact(self):
        base = datetime(2026, 1, 15, 10, 0, 0)
        result = compute_next_run("0 * * * *", from_time=base)
        assert result.minute == 0
        assert result.hour == 11, "Exact match should still advance"

    def test_minute_59(self):
        base = datetime(2026, 1, 15, 10, 30, 0)
        result = compute_next_run("59 * * * *", from_time=base)
        assert result.minute == 59
        assert result.hour == 10, "Minute 59 hasn't passed yet this hour"

    def test_minute_59_after_passing(self):
        base = datetime(2026, 1, 15, 10, 59, 0)
        result = compute_next_run("59 * * * *", from_time=base)
        assert result.minute == 59
        assert result.hour == 11, "Minute 59 is current, should advance to next hour"

    def test_validate_cron_minute_0(self):
        assert validate_cron("0 * * * *") is True

    def test_validate_cron_minute_59(self):
        assert validate_cron("59 * * * *") is True

    def test_register_boundary_minutes(self):
        entry_0 = register_schedule("wf-min0", "0 * * * *")
        entry_59 = register_schedule("wf-min59", "59 * * * *")
        assert entry_0.next_run.minute == 0
        assert entry_59.next_run.minute == 59


class TestDayBoundaryScheduling:
    """Scheduling across day boundaries (23:xx -> 00:xx next day)."""

    def test_next_run_crosses_midnight(self):
        base = datetime(2026, 1, 15, 23, 30, 0)
        result = compute_next_run("0 8 * * *", from_time=base)
        assert result.day == 16
        assert result.hour == 8
        assert result.minute == 0

    def test_minute_rollover_at_2359(self):
        base = datetime(2026, 1, 15, 23, 59, 0)
        result = compute_next_run("* * * * *", from_time=base)
        assert result == datetime(2026, 1, 16, 0, 0, 0)

    def test_specific_minute_crosses_midnight(self):
        base = datetime(2026, 1, 15, 23, 50, 0)
        result = compute_next_run("15 * * * *", from_time=base)
        assert result.day == 16
        assert result.hour == 0
        assert result.minute == 15

    def test_month_boundary(self):
        base = datetime(2026, 1, 31, 23, 30, 0)
        result = compute_next_run("0 8 * * *", from_time=base)
        assert result.month == 2
        assert result.day == 1
        assert result.hour == 8

    def test_due_detection_across_midnight(self):
        """A schedule due at 23:55 should be detected as due after midnight."""
        entry = register_schedule("wf-night", "55 23 * * *")
        entry.next_run = datetime(2026, 1, 15, 23, 55, 0)

        check_time = datetime(2026, 1, 16, 0, 5, 0)
        due = get_due_schedules(now=check_time)
        assert len(due) == 1
        assert due[0].workflow_id == "wf-night"

    def test_mark_executed_recomputes_next_day(self):
        entry = register_schedule("wf-daily", "0 6 * * *")
        entry.next_run = datetime(2026, 1, 15, 6, 0, 0)
        mark_executed("wf-daily")
        updated = get_schedule("wf-daily")
        assert updated.next_run > datetime(2026, 1, 15, 6, 0, 0)
