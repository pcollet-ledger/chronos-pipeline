"""Tests for the formatters utility module."""

from datetime import datetime

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

    def test_boundary_59999(self):
        assert format_duration(59999) == "60.0s"

    def test_boundary_60000(self):
        assert format_duration(60000) == "1.0m"

    def test_large_value(self):
        assert format_duration(36000000) == "10.0h"


class TestFormatTimestamp:
    def test_with_datetime(self):
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert format_timestamp(dt) == "2026-01-15 10:30:00"

    def test_none(self):
        assert format_timestamp(None) == "—"

    def test_custom_format(self):
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert format_timestamp(dt, "%Y-%m-%d") == "2026-01-15"

    def test_midnight(self):
        dt = datetime(2026, 1, 1, 0, 0, 0)
        assert format_timestamp(dt) == "2026-01-01 00:00:00"

    def test_end_of_day(self):
        dt = datetime(2026, 12, 31, 23, 59, 59)
        assert format_timestamp(dt) == "2026-12-31 23:59:59"


class TestFormatTaskSummary:
    def test_completed_with_duration(self):
        result = format_task_summary({
            "task_id": "abc", "status": "completed", "duration_ms": 150,
        })
        assert "abc" in result
        assert "completed" in result
        assert "150ms" in result

    def test_failed_no_duration(self):
        result = format_task_summary({
            "task_id": "xyz", "status": "failed",
        })
        assert "xyz" in result
        assert "failed" in result

    def test_missing_fields(self):
        result = format_task_summary({})
        assert "unknown" in result

    def test_zero_duration(self):
        result = format_task_summary({
            "task_id": "t", "status": "completed", "duration_ms": 0,
        })
        assert "0ms" in result

    def test_large_duration(self):
        result = format_task_summary({
            "task_id": "t", "status": "completed", "duration_ms": 7200000,
        })
        assert "2.0h" in result


class TestFormatExecutionReport:
    def test_basic_report(self):
        report = format_execution_report({
            "id": "exec-1",
            "status": "completed",
            "trigger": "manual",
            "task_results": [
                {"task_id": "t1", "status": "completed", "duration_ms": 100},
            ],
        })
        assert "exec-1" in report
        assert "completed" in report
        assert "manual" in report
        assert "t1" in report

    def test_empty_tasks(self):
        report = format_execution_report({
            "id": "exec-2",
            "status": "completed",
            "trigger": "manual",
            "task_results": [],
        })
        assert "exec-2" in report

    def test_missing_fields(self):
        report = format_execution_report({})
        assert "unknown" in report

    def test_multiple_tasks(self):
        report = format_execution_report({
            "id": "exec-3",
            "status": "failed",
            "trigger": "retry",
            "task_results": [
                {"task_id": "t1", "status": "completed", "duration_ms": 50},
                {"task_id": "t2", "status": "failed", "duration_ms": 10},
            ],
        })
        assert "t1" in report
        assert "t2" in report

    def test_report_is_multiline(self):
        report = format_execution_report({
            "id": "e", "status": "completed", "trigger": "manual",
            "task_results": [{"task_id": "t", "status": "completed"}],
        })
        assert "\n" in report


class TestFormatWorkflowTree:
    def test_simple_tree(self):
        tree = format_workflow_tree("My WF", [
            {"id": "a", "name": "A", "depends_on": []},
            {"id": "b", "name": "B", "depends_on": ["a"]},
        ])
        assert "My WF" in tree
        assert "A" in tree
        assert "B" in tree

    def test_no_tasks(self):
        tree = format_workflow_tree("Empty", [])
        assert "Empty" in tree

    def test_multiple_roots(self):
        tree = format_workflow_tree("WF", [
            {"id": "a", "name": "A", "depends_on": []},
            {"id": "b", "name": "B", "depends_on": []},
        ])
        assert "A" in tree
        assert "B" in tree

    def test_deep_nesting(self):
        tree = format_workflow_tree("WF", [
            {"id": "a", "name": "A", "depends_on": []},
            {"id": "b", "name": "B", "depends_on": ["a"]},
            {"id": "c", "name": "C", "depends_on": ["b"]},
        ])
        assert "C" in tree

    def test_returns_string(self):
        tree = format_workflow_tree("WF", [])
        assert isinstance(tree, str)
