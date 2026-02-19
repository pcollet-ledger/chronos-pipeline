"""Tests for backend/app/utils/formatters.py.

Covers format_duration, format_timestamp, format_task_summary,
format_task_result_line, format_execution_report, and format_workflow_tree
with happy paths, edge cases, and boundary values.
"""

from datetime import datetime

import pytest

from app.models import (
    TaskDefinition,
    TaskPriority,
    TaskResult,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStatus,
)
from app.utils.formatters import (
    format_duration,
    format_execution_report,
    format_task_result_line,
    format_task_summary,
    format_timestamp,
    format_workflow_tree,
)


class TestFormatDuration:
    def test_none_returns_na(self):
        assert format_duration(None) == "N/A"

    def test_zero_ms(self):
        assert format_duration(0) == "0ms"

    def test_sub_second(self):
        assert format_duration(42) == "42ms"

    def test_exactly_one_second(self):
        assert format_duration(1000) == "1.0s"

    def test_seconds_range(self):
        assert format_duration(1500) == "1.5s"

    def test_exactly_one_minute(self):
        assert format_duration(60_000) == "1.0m"

    def test_minutes_range(self):
        assert format_duration(90_000) == "1.5m"

    def test_exactly_one_hour(self):
        assert format_duration(3_600_000) == "1.0h"

    def test_hours_range(self):
        assert format_duration(7_200_000) == "2.0h"

    def test_negative_returns_zero(self):
        assert format_duration(-100) == "0ms"

    def test_very_small_positive(self):
        assert format_duration(0.5) == "0ms"

    def test_boundary_999ms(self):
        assert format_duration(999) == "999ms"

    def test_boundary_59_9s(self):
        result = format_duration(59_900)
        assert result.endswith("s")


class TestFormatTimestamp:
    def test_none_returns_na(self):
        assert format_timestamp(None) == "N/A"

    def test_default_format(self):
        dt = datetime(2025, 1, 15, 10, 30, 45)
        assert format_timestamp(dt) == "2025-01-15 10:30:45"

    def test_custom_format(self):
        dt = datetime(2025, 6, 1, 8, 0, 0)
        assert format_timestamp(dt, "%Y/%m/%d") == "2025/06/01"

    def test_midnight(self):
        dt = datetime(2025, 1, 1, 0, 0, 0)
        assert format_timestamp(dt) == "2025-01-01 00:00:00"

    def test_end_of_day(self):
        dt = datetime(2025, 12, 31, 23, 59, 59)
        assert format_timestamp(dt) == "2025-12-31 23:59:59"

    def test_iso_format(self):
        dt = datetime(2025, 3, 15, 14, 30, 0)
        result = format_timestamp(dt, "%Y-%m-%dT%H:%M:%S")
        assert result == "2025-03-15T14:30:00"


class TestFormatTaskSummary:
    def test_basic_task(self):
        task = TaskDefinition(name="Log Step", action="log")
        result = format_task_summary(task)
        assert "Log Step [log]" in result
        assert "priority=medium" in result
        assert "deps=0" in result

    def test_task_with_dependencies(self):
        task = TaskDefinition(
            name="Transform", action="transform",
            depends_on=["a", "b", "c"],
        )
        result = format_task_summary(task)
        assert "deps=3" in result

    def test_task_with_hooks(self):
        task = TaskDefinition(
            name="Validate", action="validate",
            pre_hook="log", post_hook="notify",
        )
        result = format_task_summary(task)
        assert "pre_hook=log" in result
        assert "post_hook=notify" in result

    def test_task_with_high_priority(self):
        task = TaskDefinition(
            name="Critical", action="log",
            priority=TaskPriority.CRITICAL,
        )
        result = format_task_summary(task)
        assert "priority=critical" in result

    def test_task_with_only_pre_hook(self):
        task = TaskDefinition(name="T", action="log", pre_hook="validate")
        result = format_task_summary(task)
        assert "pre_hook=validate" in result
        assert "post_hook" not in result

    def test_task_with_only_post_hook(self):
        task = TaskDefinition(name="T", action="log", post_hook="notify")
        result = format_task_summary(task)
        assert "post_hook=notify" in result
        assert "pre_hook" not in result


class TestFormatTaskResultLine:
    def test_completed_result(self):
        result = TaskResult(
            task_id="t1",
            status=WorkflowStatus.COMPLETED,
            duration_ms=42,
        )
        line = format_task_result_line(result)
        assert "[COMPLETED]" in line
        assert "t1" in line
        assert "42ms" in line

    def test_failed_result_with_error(self):
        result = TaskResult(
            task_id="t2",
            status=WorkflowStatus.FAILED,
            duration_ms=100,
            error="Unknown action: bad",
        )
        line = format_task_result_line(result)
        assert "[FAILED]" in line
        assert "Unknown action: bad" in line

    def test_failed_result_without_error(self):
        result = TaskResult(
            task_id="t3",
            status=WorkflowStatus.FAILED,
            duration_ms=50,
        )
        line = format_task_result_line(result)
        assert "[FAILED]" in line
        assert "t3" in line

    def test_result_with_none_duration(self):
        result = TaskResult(
            task_id="t4",
            status=WorkflowStatus.COMPLETED,
        )
        line = format_task_result_line(result)
        assert "N/A" in line

    def test_pending_result(self):
        result = TaskResult(
            task_id="t5",
            status=WorkflowStatus.PENDING,
        )
        line = format_task_result_line(result)
        assert "[PENDING]" in line


class TestFormatExecutionReport:
    def test_completed_execution(self):
        started = datetime(2025, 1, 15, 10, 0, 0)
        completed = datetime(2025, 1, 15, 10, 0, 1)
        execution = WorkflowExecution(
            id="exec-1",
            workflow_id="wf-1",
            status=WorkflowStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
            trigger="manual",
            task_results=[
                TaskResult(task_id="t1", status=WorkflowStatus.COMPLETED, duration_ms=500),
            ],
        )
        report = format_execution_report(execution)
        assert "exec-1" in report
        assert "wf-1" in report
        assert "completed" in report
        assert "manual" in report
        assert "Tasks (1):" in report
        assert "[COMPLETED] t1" in report

    def test_cancelled_execution(self):
        now = datetime(2025, 1, 15, 10, 0, 0)
        execution = WorkflowExecution(
            id="exec-2",
            workflow_id="wf-2",
            status=WorkflowStatus.CANCELLED,
            started_at=now,
            completed_at=now,
            cancelled_at=now,
        )
        report = format_execution_report(execution)
        assert "cancelled" in report
        assert "Cancelled:" in report

    def test_execution_with_no_tasks(self):
        execution = WorkflowExecution(
            id="exec-3",
            workflow_id="wf-3",
            status=WorkflowStatus.COMPLETED,
        )
        report = format_execution_report(execution)
        assert "Tasks: (none)" in report

    def test_execution_with_metadata(self):
        execution = WorkflowExecution(
            id="exec-4",
            workflow_id="wf-4",
            status=WorkflowStatus.COMPLETED,
            metadata={"retried_from": "exec-0"},
        )
        report = format_execution_report(execution)
        assert "retried_from" in report

    def test_execution_without_timestamps(self):
        execution = WorkflowExecution(
            id="exec-5",
            workflow_id="wf-5",
            status=WorkflowStatus.PENDING,
        )
        report = format_execution_report(execution)
        assert "N/A" in report

    def test_failed_execution_with_error_task(self):
        execution = WorkflowExecution(
            id="exec-6",
            workflow_id="wf-6",
            status=WorkflowStatus.FAILED,
            task_results=[
                TaskResult(task_id="t1", status=WorkflowStatus.COMPLETED, duration_ms=10),
                TaskResult(
                    task_id="t2", status=WorkflowStatus.FAILED,
                    duration_ms=5, error="boom",
                ),
            ],
        )
        report = format_execution_report(execution)
        assert "failed" in report
        assert "boom" in report
        assert "Tasks (2):" in report


class TestFormatWorkflowTree:
    def test_empty_workflow(self):
        wf = WorkflowDefinition(name="Empty WF", tasks=[])
        tree = format_workflow_tree(wf)
        assert "Empty WF (no tasks)" in tree

    def test_single_task(self):
        wf = WorkflowDefinition(
            name="Single",
            tasks=[TaskDefinition(id="A", name="Task A", action="log")],
        )
        tree = format_workflow_tree(wf)
        assert "Single (v1)" in tree
        assert "Task A [log]" in tree

    def test_linear_chain(self):
        wf = WorkflowDefinition(
            name="Chain",
            tasks=[
                TaskDefinition(id="A", name="First", action="log"),
                TaskDefinition(id="B", name="Second", action="validate", depends_on=["A"]),
                TaskDefinition(id="C", name="Third", action="notify", depends_on=["B"]),
            ],
        )
        tree = format_workflow_tree(wf)
        assert "Chain (v1)" in tree
        assert "First [log]" in tree
        assert "Second [validate]" in tree
        assert "Third [notify]" in tree

    def test_fan_out(self):
        wf = WorkflowDefinition(
            name="Fan",
            tasks=[
                TaskDefinition(id="A", name="Root", action="log"),
                TaskDefinition(id="B", name="B1", action="log", depends_on=["A"]),
                TaskDefinition(id="C", name="C1", action="log", depends_on=["A"]),
            ],
        )
        tree = format_workflow_tree(wf)
        assert "Root [log]" in tree
        assert "B1 [log]" in tree
        assert "C1 [log]" in tree

    def test_diamond_dependency(self):
        wf = WorkflowDefinition(
            name="Diamond",
            tasks=[
                TaskDefinition(id="A", name="Start", action="log"),
                TaskDefinition(id="B", name="Left", action="log", depends_on=["A"]),
                TaskDefinition(id="C", name="Right", action="log", depends_on=["A"]),
                TaskDefinition(id="D", name="End", action="log", depends_on=["B", "C"]),
            ],
        )
        tree = format_workflow_tree(wf)
        assert "Diamond (v1)" in tree
        assert "Start [log]" in tree

    def test_versioned_workflow(self):
        wf = WorkflowDefinition(
            name="Versioned",
            version=3,
            tasks=[TaskDefinition(id="A", name="T", action="log")],
        )
        tree = format_workflow_tree(wf)
        assert "(v3)" in tree

    def test_multiple_roots(self):
        wf = WorkflowDefinition(
            name="Multi Root",
            tasks=[
                TaskDefinition(id="A", name="Root1", action="log"),
                TaskDefinition(id="B", name="Root2", action="validate"),
            ],
        )
        tree = format_workflow_tree(wf)
        assert "Root1 [log]" in tree
        assert "Root2 [validate]" in tree
