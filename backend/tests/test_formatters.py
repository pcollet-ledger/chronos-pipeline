"""Tests for backend/app/utils/formatters.py.

Covers all public functions with >=10 cases each, including edge cases,
boundary values, and None handling.
"""

from datetime import datetime

import pytest

from app.models import (
    TaskResult,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStatus,
    TaskDefinition,
)
from app.utils.formatters import (
    format_duration,
    format_execution_report,
    format_status_badge,
    format_task_summary,
    format_timestamp,
    format_workflow_tree,
)


# ---------------------------------------------------------------------------
# format_duration
# ---------------------------------------------------------------------------

class TestFormatDuration:
    """Tests for format_duration."""

    def test_none_returns_dash(self):
        assert format_duration(None) == "—"

    def test_zero_ms(self):
        assert format_duration(0) == "0ms"

    def test_sub_second(self):
        assert format_duration(500) == "500ms"

    def test_exactly_one_second(self):
        assert format_duration(1000) == "1.0s"

    def test_seconds_range(self):
        assert format_duration(3500) == "3.5s"

    def test_boundary_just_under_minute(self):
        assert format_duration(59_999) == "60.0s"

    def test_exactly_one_minute(self):
        assert format_duration(60_000) == "1.0m"

    def test_minutes_range(self):
        assert format_duration(150_000) == "2.5m"

    def test_exactly_one_hour(self):
        assert format_duration(3_600_000) == "1.0h"

    def test_large_duration(self):
        assert format_duration(7_200_000) == "2.0h"

    def test_small_fractional_ms(self):
        assert format_duration(1) == "1ms"

    def test_999_ms(self):
        assert format_duration(999) == "999ms"


# ---------------------------------------------------------------------------
# format_timestamp
# ---------------------------------------------------------------------------

class TestFormatTimestamp:
    """Tests for format_timestamp."""

    def test_none_returns_dash(self):
        assert format_timestamp(None) == "—"

    def test_default_format(self):
        dt = datetime(2025, 3, 15, 10, 30, 45)
        assert format_timestamp(dt) == "2025-03-15 10:30:45"

    def test_custom_format(self):
        dt = datetime(2025, 3, 15, 10, 30, 45)
        assert format_timestamp(dt, "%d/%m/%Y") == "15/03/2025"

    def test_midnight(self):
        dt = datetime(2025, 1, 1, 0, 0, 0)
        assert format_timestamp(dt) == "2025-01-01 00:00:00"

    def test_end_of_day(self):
        dt = datetime(2025, 12, 31, 23, 59, 59)
        assert format_timestamp(dt) == "2025-12-31 23:59:59"

    def test_iso_format(self):
        dt = datetime(2025, 6, 1, 12, 0, 0)
        assert format_timestamp(dt, "%Y-%m-%dT%H:%M:%S") == "2025-06-01T12:00:00"

    def test_date_only(self):
        dt = datetime(2025, 6, 1, 12, 0, 0)
        assert format_timestamp(dt, "%Y-%m-%d") == "2025-06-01"

    def test_time_only(self):
        dt = datetime(2025, 6, 1, 14, 30, 0)
        assert format_timestamp(dt, "%H:%M") == "14:30"

    def test_leap_year(self):
        dt = datetime(2024, 2, 29, 12, 0, 0)
        assert format_timestamp(dt) == "2024-02-29 12:00:00"

    def test_year_2000(self):
        dt = datetime(2000, 1, 1, 0, 0, 0)
        assert format_timestamp(dt) == "2000-01-01 00:00:00"


# ---------------------------------------------------------------------------
# format_task_summary
# ---------------------------------------------------------------------------

class TestFormatTaskSummary:
    """Tests for format_task_summary."""

    def test_completed_task(self):
        tr = TaskResult(task_id="t1", status=WorkflowStatus.COMPLETED, duration_ms=120)
        assert format_task_summary(tr) == "t1: completed (120ms)"

    def test_failed_task_with_error(self):
        tr = TaskResult(
            task_id="t2",
            status=WorkflowStatus.FAILED,
            duration_ms=500,
            error="Timeout exceeded",
        )
        assert format_task_summary(tr) == "t2: failed — Timeout exceeded (500ms)"

    def test_failed_task_without_error(self):
        tr = TaskResult(task_id="t3", status=WorkflowStatus.FAILED, duration_ms=200)
        assert format_task_summary(tr) == "t3: failed (200ms)"

    def test_pending_task(self):
        tr = TaskResult(task_id="t4", status=WorkflowStatus.PENDING)
        assert format_task_summary(tr) == "t4: pending (—)"

    def test_running_task(self):
        tr = TaskResult(task_id="t5", status=WorkflowStatus.RUNNING, duration_ms=1000)
        assert format_task_summary(tr) == "t5: running (1.0s)"

    def test_cancelled_task(self):
        tr = TaskResult(task_id="t6", status=WorkflowStatus.CANCELLED, duration_ms=0)
        assert format_task_summary(tr) == "t6: cancelled (0ms)"

    def test_none_duration(self):
        tr = TaskResult(task_id="t7", status=WorkflowStatus.COMPLETED)
        assert format_task_summary(tr) == "t7: completed (—)"

    def test_large_duration(self):
        tr = TaskResult(
            task_id="t8", status=WorkflowStatus.COMPLETED, duration_ms=3_600_000
        )
        assert format_task_summary(tr) == "t8: completed (1.0h)"

    def test_task_id_with_special_chars(self):
        tr = TaskResult(
            task_id="task-abc-123", status=WorkflowStatus.COMPLETED, duration_ms=50
        )
        assert "task-abc-123" in format_task_summary(tr)

    def test_failed_with_multiline_error(self):
        tr = TaskResult(
            task_id="t9",
            status=WorkflowStatus.FAILED,
            duration_ms=100,
            error="Line 1\nLine 2",
        )
        result = format_task_summary(tr)
        assert "Line 1\nLine 2" in result


# ---------------------------------------------------------------------------
# format_execution_report
# ---------------------------------------------------------------------------

class TestFormatExecutionReport:
    """Tests for format_execution_report."""

    def _make_execution(self, **overrides) -> WorkflowExecution:
        defaults = {
            "id": "exec-1",
            "workflow_id": "wf-1",
            "status": WorkflowStatus.COMPLETED,
            "trigger": "manual",
            "started_at": datetime(2025, 1, 1, 12, 0, 0),
            "completed_at": datetime(2025, 1, 1, 12, 5, 0),
            "task_results": [],
        }
        defaults.update(overrides)
        return WorkflowExecution(**defaults)

    def test_basic_report_structure(self):
        report = format_execution_report(self._make_execution())
        assert "Execution exec-1" in report
        assert "Workflow: wf-1" in report
        assert "Status:   completed" in report

    def test_no_task_results(self):
        report = format_execution_report(self._make_execution())
        assert "Tasks: (none)" in report

    def test_with_task_results(self):
        results = [
            TaskResult(task_id="t1", status=WorkflowStatus.COMPLETED, duration_ms=100),
            TaskResult(task_id="t2", status=WorkflowStatus.FAILED, duration_ms=200, error="oops"),
        ]
        report = format_execution_report(self._make_execution(task_results=results))
        assert "Tasks (2):" in report
        assert "t1: completed" in report
        assert "t2: failed — oops" in report

    def test_trigger_displayed(self):
        report = format_execution_report(self._make_execution(trigger="scheduled"))
        assert "Trigger:  scheduled" in report

    def test_timestamps_formatted(self):
        report = format_execution_report(self._make_execution())
        assert "2025-01-01 12:00:00" in report
        assert "2025-01-01 12:05:00" in report

    def test_none_timestamps(self):
        report = format_execution_report(
            self._make_execution(started_at=None, completed_at=None)
        )
        assert "Started:  —" in report
        assert "Ended:    —" in report

    def test_running_status(self):
        report = format_execution_report(
            self._make_execution(status=WorkflowStatus.RUNNING, completed_at=None)
        )
        assert "Status:   running" in report

    def test_cancelled_status(self):
        report = format_execution_report(
            self._make_execution(status=WorkflowStatus.CANCELLED)
        )
        assert "Status:   cancelled" in report

    def test_multiple_tasks_ordering(self):
        results = [
            TaskResult(task_id="a", status=WorkflowStatus.COMPLETED, duration_ms=10),
            TaskResult(task_id="b", status=WorkflowStatus.COMPLETED, duration_ms=20),
            TaskResult(task_id="c", status=WorkflowStatus.COMPLETED, duration_ms=30),
        ]
        report = format_execution_report(self._make_execution(task_results=results))
        a_pos = report.index("a: completed")
        b_pos = report.index("b: completed")
        c_pos = report.index("c: completed")
        assert a_pos < b_pos < c_pos

    def test_report_is_multiline(self):
        report = format_execution_report(self._make_execution())
        assert report.count("\n") >= 5


# ---------------------------------------------------------------------------
# format_workflow_tree
# ---------------------------------------------------------------------------

class TestFormatWorkflowTree:
    """Tests for format_workflow_tree."""

    def _make_workflow(self, tasks, **overrides) -> WorkflowDefinition:
        defaults = {
            "name": "test-workflow",
            "tasks": tasks,
            "version": 1,
        }
        defaults.update(overrides)
        return WorkflowDefinition(**defaults)

    def test_single_task(self):
        tasks = [TaskDefinition(id="t1", name="Task One", action="run")]
        tree = format_workflow_tree(self._make_workflow(tasks))
        assert "test-workflow (v1)" in tree
        assert "Task One [run]" in tree

    def test_linear_chain(self):
        tasks = [
            TaskDefinition(id="t1", name="First", action="run"),
            TaskDefinition(id="t2", name="Second", action="run", depends_on=["t1"]),
            TaskDefinition(id="t3", name="Third", action="run", depends_on=["t2"]),
        ]
        tree = format_workflow_tree(self._make_workflow(tasks))
        assert "First" in tree
        assert "Second" in tree
        assert "Third" in tree

    def test_fan_out(self):
        tasks = [
            TaskDefinition(id="root", name="Root", action="run"),
            TaskDefinition(id="a", name="A", action="run", depends_on=["root"]),
            TaskDefinition(id="b", name="B", action="run", depends_on=["root"]),
        ]
        tree = format_workflow_tree(self._make_workflow(tasks))
        assert "Root" in tree
        assert "A" in tree
        assert "B" in tree

    def test_empty_tasks(self):
        tree = format_workflow_tree(self._make_workflow([]))
        assert "test-workflow (v1)" in tree

    def test_version_displayed(self):
        tasks = [TaskDefinition(id="t1", name="T", action="run")]
        tree = format_workflow_tree(self._make_workflow(tasks, version=5))
        assert "(v5)" in tree

    def test_no_dependencies_all_roots(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="run"),
            TaskDefinition(id="b", name="B", action="run"),
        ]
        tree = format_workflow_tree(self._make_workflow(tasks))
        assert "A" in tree
        assert "B" in tree

    def test_diamond_dependency(self):
        tasks = [
            TaskDefinition(id="root", name="Root", action="run"),
            TaskDefinition(id="left", name="Left", action="run", depends_on=["root"]),
            TaskDefinition(id="right", name="Right", action="run", depends_on=["root"]),
            TaskDefinition(id="join", name="Join", action="run", depends_on=["left", "right"]),
        ]
        tree = format_workflow_tree(self._make_workflow(tasks))
        assert "Root" in tree
        assert "Join" in tree

    def test_tree_indentation(self):
        tasks = [
            TaskDefinition(id="root", name="Root", action="run"),
            TaskDefinition(id="child", name="Child", action="run", depends_on=["root"]),
        ]
        tree = format_workflow_tree(self._make_workflow(tasks))
        lines = tree.split("\n")
        root_line = [l for l in lines if "Root" in l][0]
        child_line = [l for l in lines if "Child" in l][0]
        assert len(child_line) - len(child_line.lstrip()) > len(root_line) - len(root_line.lstrip())

    def test_workflow_name_in_header(self):
        tasks = [TaskDefinition(id="t1", name="T", action="run")]
        tree = format_workflow_tree(self._make_workflow(tasks, name="my-pipeline"))
        assert tree.startswith("my-pipeline")

    def test_action_shown_in_brackets(self):
        tasks = [TaskDefinition(id="t1", name="Extract", action="extract_data")]
        tree = format_workflow_tree(self._make_workflow(tasks))
        assert "[extract_data]" in tree


# ---------------------------------------------------------------------------
# format_status_badge
# ---------------------------------------------------------------------------

class TestFormatStatusBadge:
    """Tests for format_status_badge."""

    def test_completed(self):
        assert format_status_badge(WorkflowStatus.COMPLETED) == "✓ completed"

    def test_failed(self):
        assert format_status_badge(WorkflowStatus.FAILED) == "✗ failed"

    def test_running(self):
        assert format_status_badge(WorkflowStatus.RUNNING) == "⏳ running"

    def test_pending(self):
        assert format_status_badge(WorkflowStatus.PENDING) == "○ pending"

    def test_cancelled(self):
        assert format_status_badge(WorkflowStatus.CANCELLED) == "⊘ cancelled"

    def test_all_statuses_covered(self):
        for status in WorkflowStatus:
            badge = format_status_badge(status)
            assert status.value in badge

    def test_completed_has_checkmark(self):
        assert "✓" in format_status_badge(WorkflowStatus.COMPLETED)

    def test_failed_has_cross(self):
        assert "✗" in format_status_badge(WorkflowStatus.FAILED)

    def test_running_has_hourglass(self):
        assert "⏳" in format_status_badge(WorkflowStatus.RUNNING)

    def test_return_type_is_string(self):
        for status in WorkflowStatus:
            assert isinstance(format_status_badge(status), str)
