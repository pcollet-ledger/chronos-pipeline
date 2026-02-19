"""Tests simulating concurrent-like access patterns.

Covers rapid creation/deletion, simultaneous executions, retry during
execution, and index consistency under concurrent-like load.
"""

import threading
from unittest.mock import patch

import pytest

from app.models import WorkflowCreate, WorkflowExecution, WorkflowStatus
from app.services.analytics_service import clear_cache, get_summary
from app.services.workflow_engine import (
    LogOutput,
    _executions,
    _index_execution,
    cancel_execution,
    clear_all,
    clone_workflow,
    create_workflow,
    delete_workflow,
    execute_workflow,
    get_workflow,
    list_executions,
    list_workflows,
    retry_execution,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    clear_cache()
    yield
    clear_all()
    clear_cache()


class TestRapidCreationDeletion:
    """Create and delete workflows in rapid succession."""

    def test_create_delete_cycle(self):
        for _ in range(100):
            wf = create_workflow(WorkflowCreate(name="Ephemeral"))
            assert delete_workflow(wf.id)
        assert list_workflows(limit=1000) == []

    def test_create_many_then_delete_all(self):
        ids = [create_workflow(WorkflowCreate(name=f"WF-{i}")).id for i in range(50)]
        for wid in ids:
            delete_workflow(wid)
        assert list_workflows(limit=1000) == []

    def test_interleaved_create_delete(self):
        """Alternate between creating and deleting different workflows."""
        live_ids = []
        for i in range(50):
            wf = create_workflow(WorkflowCreate(name=f"WF-{i}"))
            live_ids.append(wf.id)
            if len(live_ids) > 10:
                delete_workflow(live_ids.pop(0))
        assert len(list_workflows(limit=1000)) == len(live_ids)

    def test_delete_nonexistent_is_safe(self):
        for _ in range(50):
            assert not delete_workflow("nonexistent-id")


class TestSimultaneousExecutions:
    """Execute the same workflow many times in rapid succession."""

    def test_rapid_executions_all_stored(self):
        wf = create_workflow(WorkflowCreate(
            name="Rapid",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        for _ in range(50):
            ex = execute_workflow(wf.id)
            assert ex.status == WorkflowStatus.COMPLETED
        assert len(list_executions(workflow_id=wf.id, limit=1000)) == 50

    def test_threaded_executions(self):
        """Run executions from multiple threads."""
        wf = create_workflow(WorkflowCreate(
            name="Threaded",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        errors = []
        results = []

        def run():
            try:
                ex = execute_workflow(wf.id)
                results.append(ex)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=run) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(results) == 10
        assert all(r.status == WorkflowStatus.COMPLETED for r in results)

    def test_execution_ids_unique(self):
        wf = create_workflow(WorkflowCreate(
            name="Unique IDs",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ids = set()
        for _ in range(100):
            ex = execute_workflow(wf.id)
            ids.add(ex.id)
        assert len(ids) == 100


class TestRetryDuringExecution:
    """Retry and execution interactions."""

    def test_retry_while_other_execution_runs(self):
        """Retrying one execution while another is in progress."""
        wf = create_workflow(WorkflowCreate(
            name="Multi",
            tasks=[
                {"name": "Good", "action": "log", "parameters": {"message": "ok"}},
                {"name": "Bad", "action": "unknown_action", "parameters": {}},
            ],
        ))
        ex1 = execute_workflow(wf.id)
        assert ex1.status == WorkflowStatus.FAILED

        ex2 = execute_workflow(wf.id)
        assert ex2.status == WorkflowStatus.FAILED

        retry1 = retry_execution(ex1.id)
        retry2 = retry_execution(ex2.id)
        assert retry1.id != retry2.id

    def test_retry_then_execute_original_workflow(self):
        wf = create_workflow(WorkflowCreate(
            name="RetryExec",
            tasks=[{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        ))
        ex = execute_workflow(wf.id)
        retry_execution(ex.id)

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda a, p: LogOutput(message="ok"),
        ):
            new_ex = execute_workflow(wf.id)
        assert new_ex.status == WorkflowStatus.COMPLETED

    def test_cancel_then_execute_same_workflow(self):
        wf = create_workflow(WorkflowCreate(
            name="CancelExec",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        pending = WorkflowExecution(
            workflow_id=wf.id,
            status=WorkflowStatus.PENDING,
        )
        _executions[pending.id] = pending
        _index_execution(pending)

        cancel_execution(pending.id)
        new_ex = execute_workflow(wf.id)
        assert new_ex.status == WorkflowStatus.COMPLETED


class TestIndexConsistency:
    """Verify indexes remain consistent under rapid mutations."""

    def test_tag_index_after_rapid_tag_changes(self):
        from app.services.workflow_engine import add_tags, remove_tag
        wf = create_workflow(WorkflowCreate(name="TagStress"))
        for i in range(50):
            add_tags(wf.id, [f"tag-{i}"])
        for i in range(25):
            remove_tag(wf.id, f"tag-{i}")
        current = get_workflow(wf.id)
        assert len(current.tags) == 25
        for i in range(25, 50):
            results = list_workflows(tag=f"tag-{i}")
            assert len(results) == 1

    def test_execution_index_after_many_operations(self):
        wf = create_workflow(WorkflowCreate(
            name="IndexStress",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        for _ in range(30):
            execute_workflow(wf.id)

        by_wf = list_executions(workflow_id=wf.id, limit=1000)
        by_status = list_executions(status=WorkflowStatus.COMPLETED, limit=1000)
        assert len(by_wf) == 30
        assert len(by_status) == 30

    def test_clone_preserves_tag_index(self):
        wf = create_workflow(WorkflowCreate(name="Original", tags=["shared"]))
        cloned = clone_workflow(wf.id)
        results = list_workflows(tag="shared")
        assert len(results) == 2
        ids = {w.id for w in results}
        assert wf.id in ids
        assert cloned.id in ids

    def test_delete_cleans_tag_index(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["cleanup"]))
        assert len(list_workflows(tag="cleanup")) == 1
        delete_workflow(wf.id)
        assert len(list_workflows(tag="cleanup")) == 0

    def test_analytics_consistent_after_mixed_operations(self):
        wf_good = create_workflow(WorkflowCreate(
            name="Good",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        wf_bad = create_workflow(WorkflowCreate(
            name="Bad",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))
        for _ in range(10):
            execute_workflow(wf_good.id)
            execute_workflow(wf_bad.id)

        clear_cache()
        summary = get_summary(days=30)
        assert summary.total_executions == 20
        assert summary.success_rate == 50.0


class TestConcurrentCreation:
    """Threaded workflow creation."""

    def test_threaded_creation(self):
        errors = []
        created = []

        def create():
            try:
                wf = create_workflow(WorkflowCreate(name="Threaded"))
                created.append(wf)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=create) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(created) == 20
        assert len(set(w.id for w in created)) == 20

    def test_threaded_creation_and_listing(self):
        errors = []

        def create_and_list():
            try:
                create_workflow(WorkflowCreate(name="CL"))
                list_workflows(limit=100)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=create_and_list) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert len(list_workflows(limit=1000)) == 10

    def test_threaded_clone(self):
        wf = create_workflow(WorkflowCreate(
            name="Template",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        errors = []
        clones = []

        def do_clone():
            try:
                c = clone_workflow(wf.id)
                clones.append(c)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=do_clone) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert len(clones) == 10

    def test_threaded_analytics(self):
        wf = create_workflow(WorkflowCreate(
            name="Analytics",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        for _ in range(10):
            execute_workflow(wf.id)

        errors = []

        def read_analytics():
            try:
                clear_cache()
                get_summary(days=30)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=read_analytics) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []

    def test_threaded_retry(self):
        wf = create_workflow(WorkflowCreate(
            name="RetryThreaded",
            tasks=[{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        ))
        exec_ids = [execute_workflow(wf.id).id for _ in range(5)]
        errors = []
        retries = []

        def do_retry(eid):
            try:
                r = retry_execution(eid)
                retries.append(r)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=do_retry, args=(eid,)) for eid in exec_ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert len(retries) == 5
