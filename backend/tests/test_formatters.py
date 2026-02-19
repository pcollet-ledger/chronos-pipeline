"""Tests for the formatters utility module."""

from datetime import datetime

import pytest

from app.models import (
    TaskResult,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStatus,
)
from app.utils.formatters import (
    format_duration,
    format_execution_report,
    format_task_summary,
    format_timestamp,
    format_workflow_tree,
)


class TestFormatDuration:
    def test_milliseconds(self):
        assert format_duration(500) == "500ms"

    def test_zero(self):
        assert format_duration(0) == "0ms"

    def test_seconds(self):
        assert format_duration(5000) == "5.0s"

    def test_minutes(self):
        assert format_duration(120000) == "2.0m"

    def test_hours(self):
        assert format_duration(7200000) == "2.0h"

    def test_boundary_999(self):
        assert format_duration(999) == "999ms"

    def test_boundary_1000(self):
        assert format_duration(1000) == "1.0s"

    def test_boundary_60s(self):
        assert format_duration(60000) == "1.0m"

    def test_boundary_60m(self):
        assert format_duration(3600000) == "1.0h"

    def test_fractional(self):
        assert format_duration(1500) == "1.5s"


class TestFormatTimestamp:
    def test_with_datetime(self):
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert format_timestamp(dt) == "2026-01-15T10:30:00Z"

    def test_none(self):
        assert format_timestamp(None) == "—"

    def test_with_microseconds(self):
        dt = datetime(2026, 1, 15, 10, 30, 0, 123456)
        result = format_timestamp(dt)
        assert result.endswith("Z")
        assert "2026-01-15" in result


class TestFormatTaskSummary:
    def test_completed_task(self):
        tr = TaskResult(
            task_id="t1",
            status=WorkflowStatus.COMPLETED,
            duration_ms=150,
        )
        result = format_task_summary(tr)
        assert "t1" in result
        assert "completed" in result
        assert "150ms" in result

    def test_failed_task_with_error(self):
        tr = TaskResult(
            task_id="t2",
            status=WorkflowStatus.FAILED,
            duration_ms=50,
            error="Something broke",
        )
        result = format_task_summary(tr)
        assert "failed" in result
        assert "Something broke" in result

    def test_no_duration(self):
        tr = TaskResult(
            task_id="t3",
            status=WorkflowStatus.PENDING,
        )
        result = format_task_summary(tr)
        assert "—" in result

    def test_zero_duration(self):
        tr = TaskResult(
            task_id="t4",
            status=WorkflowStatus.COMPLETED,
            duration_ms=0,
        )
        result = format_task_summary(tr)
        assert "0ms" in result


class TestFormatExecutionReport:
    def test_basic_report(self):
        ex = WorkflowExecution(
            workflow_id="wf-1",
            status=WorkflowStatus.COMPLETED,
            started_at=datetime(2026, 1, 15, 10, 0),
            completed_at=datetime(2026, 1, 15, 10, 1),
            trigger="manual",
            task_results=[
                TaskResult(task_id="t1", status=WorkflowStatus.COMPLETED, duration_ms=100),
            ],
        )
        report = format_execution_report(ex)
        assert "wf-1" in report
        assert "completed" in report
        assert "manual" in report
        assert "t1" in report

    def test_empty_task_results(self):
        ex = WorkflowExecution(
            workflow_id="wf-1",
            status=WorkflowStatus.COMPLETED,
            trigger="manual",
        )
        report = format_execution_report(ex)
        assert "Tasks (0)" in report

    def test_failed_report(self):
        ex = WorkflowExecution(
            workflow_id="wf-1",
            status=WorkflowStatus.FAILED,
            trigger="scheduled",
            task_results=[
                TaskResult(task_id="t1", status=WorkflowStatus.FAILED, error="boom"),
            ],
        )
        report = format_execution_report(ex)
        assert "failed" in report
        assert "boom" in report


class TestFormatWorkflowTree:
    def test_simple_tree(self):
        wf = WorkflowDefinition(
            name="Pipeline",
            tasks=[
                {"id": "a", "name": "Extract", "action": "log", "parameters": {}},
                {"id": "b", "name": "Transform", "action": "transform", "parameters": {}, "depends_on": ["a"]},
            ],
        )
        tree = format_workflow_tree(wf)
        assert "Pipeline" in tree
        assert "Extract" in tree
        assert "Transform" in tree

    def test_empty_workflow(self):
        wf = WorkflowDefinition(name="Empty")
        tree = format_workflow_tree(wf)
        assert "Empty" in tree

    def test_version_in_header(self):
        wf = WorkflowDefinition(name="WF", version=3)
        tree = format_workflow_tree(wf)
        assert "v3" in tree
