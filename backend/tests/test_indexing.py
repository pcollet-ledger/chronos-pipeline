"""Tests for secondary indexes in workflow_engine.

Verifies that tag, status, and workflow_id indexes are maintained
correctly on create, update, delete, and execution operations.
Includes benchmarking tests with 100+ workflows.
"""

import pytest

from app.models import WorkflowCreate, WorkflowExecution, WorkflowStatus, WorkflowUpdate
from app.services.workflow_engine import (
    _execution_status_index,
    _execution_workflow_index,
    _executions,
    _rebuild_indexes,
    _workflow_tag_index,
    _workflows,
    clear_all,
    create_workflow,
    delete_workflow,
    execute_workflow,
    list_executions,
    list_workflows,
    update_workflow,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    yield
    clear_all()


class TestWorkflowTagIndex:
    """Verify the tag index is maintained on CRUD operations."""

    def test_create_indexes_tags(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["alpha", "beta"]))
        assert wf.id in _workflow_tag_index["alpha"]
        assert wf.id in _workflow_tag_index["beta"]

    def test_delete_removes_from_tag_index(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["alpha"]))
        delete_workflow(wf.id)
        assert wf.id not in _workflow_tag_index.get("alpha", set())

    def test_update_tags_reindexes(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["old"]))
        update_workflow(wf.id, WorkflowUpdate(tags=["new"]))
        assert wf.id not in _workflow_tag_index.get("old", set())
        assert wf.id in _workflow_tag_index["new"]

    def test_list_by_tag_uses_index(self):
        create_workflow(WorkflowCreate(name="A", tags=["x"]))
        create_workflow(WorkflowCreate(name="B", tags=["y"]))
        create_workflow(WorkflowCreate(name="C", tags=["x", "y"]))

        x_results = list_workflows(tag="x")
        assert len(x_results) == 2
        y_results = list_workflows(tag="y")
        assert len(y_results) == 2

    def test_empty_tag_returns_all(self):
        create_workflow(WorkflowCreate(name="A", tags=["x"]))
        create_workflow(WorkflowCreate(name="B", tags=["y"]))
        results = list_workflows()
        assert len(results) == 2

    def test_nonexistent_tag_returns_empty(self):
        create_workflow(WorkflowCreate(name="A", tags=["x"]))
        results = list_workflows(tag="nonexistent")
        assert results == []


class TestExecutionStatusIndex:
    """Verify the execution status index is maintained."""

    def test_execute_indexes_status(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex = execute_workflow(wf.id)
        assert ex.id in _execution_status_index[WorkflowStatus.COMPLETED]

    def test_failed_execution_indexed(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))
        ex = execute_workflow(wf.id)
        assert ex.id in _execution_status_index[WorkflowStatus.FAILED]

    def test_list_by_status_uses_index(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        execute_workflow(wf.id)
        execute_workflow(wf.id)

        completed = list_executions(status=WorkflowStatus.COMPLETED)
        assert len(completed) == 2
        failed = list_executions(status=WorkflowStatus.FAILED)
        assert len(failed) == 0


class TestExecutionWorkflowIndex:
    """Verify the workflow_id index for executions."""

    def test_execute_indexes_workflow_id(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex = execute_workflow(wf.id)
        assert ex.id in _execution_workflow_index[wf.id]

    def test_list_by_workflow_uses_index(self):
        wf1 = create_workflow(WorkflowCreate(
            name="WF1",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        wf2 = create_workflow(WorkflowCreate(
            name="WF2",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        execute_workflow(wf1.id)
        execute_workflow(wf1.id)
        execute_workflow(wf2.id)

        wf1_execs = list_executions(workflow_id=wf1.id)
        assert len(wf1_execs) == 2
        wf2_execs = list_executions(workflow_id=wf2.id)
        assert len(wf2_execs) == 1


class TestRebuildIndexes:
    """Verify _rebuild_indexes recovers from inconsistencies."""

    def test_rebuild_restores_tag_index(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["alpha"]))
        _workflow_tag_index.clear()
        _rebuild_indexes()
        assert wf.id in _workflow_tag_index["alpha"]

    def test_rebuild_restores_execution_indexes(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex = execute_workflow(wf.id)
        _execution_status_index.clear()
        _execution_workflow_index.clear()
        _rebuild_indexes()
        assert ex.id in _execution_status_index[WorkflowStatus.COMPLETED]
        assert ex.id in _execution_workflow_index[wf.id]

    def test_rebuild_on_empty_stores(self):
        _rebuild_indexes()
        assert len(_workflow_tag_index) == 0
        assert len(_execution_status_index) == 0
        assert len(_execution_workflow_index) == 0


class TestBenchmarkIndexedQueries:
    """Benchmarking tests with 100+ workflows to verify correctness."""

    def test_100_workflows_tag_filter(self):
        for i in range(100):
            tag = "even" if i % 2 == 0 else "odd"
            create_workflow(WorkflowCreate(name=f"WF-{i}", tags=[tag]))

        even = list_workflows(tag="even")
        odd = list_workflows(tag="odd")
        assert len(even) == 50
        assert len(odd) == 50

    def test_100_workflows_list_all(self):
        for i in range(100):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        results = list_workflows(limit=1000)
        assert len(results) == 100

    def test_100_workflows_pagination(self):
        for i in range(100):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        page1 = list_workflows(limit=25, offset=0)
        page2 = list_workflows(limit=25, offset=25)
        assert len(page1) == 25
        assert len(page2) == 25
        ids1 = {w.id for w in page1}
        ids2 = {w.id for w in page2}
        assert ids1.isdisjoint(ids2)

    def test_100_executions_status_filter(self):
        wf_good = create_workflow(WorkflowCreate(
            name="Good",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        wf_bad = create_workflow(WorkflowCreate(
            name="Bad",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))
        for _ in range(50):
            execute_workflow(wf_good.id)
        for _ in range(50):
            execute_workflow(wf_bad.id)

        completed = list_executions(status=WorkflowStatus.COMPLETED, limit=1000)
        failed = list_executions(status=WorkflowStatus.FAILED, limit=1000)
        assert len(completed) == 50
        assert len(failed) == 50

    def test_100_executions_workflow_filter(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        for _ in range(100):
            execute_workflow(wf.id)

        results = list_executions(workflow_id=wf.id, limit=1000)
        assert len(results) == 100

    def test_combined_filters(self):
        wf1 = create_workflow(WorkflowCreate(
            name="WF1",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        wf2 = create_workflow(WorkflowCreate(
            name="WF2",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))
        for _ in range(10):
            execute_workflow(wf1.id)
            execute_workflow(wf2.id)

        wf1_completed = list_executions(
            workflow_id=wf1.id, status=WorkflowStatus.COMPLETED, limit=1000
        )
        assert len(wf1_completed) == 10
        wf2_failed = list_executions(
            workflow_id=wf2.id, status=WorkflowStatus.FAILED, limit=1000
        )
        assert len(wf2_failed) == 10
