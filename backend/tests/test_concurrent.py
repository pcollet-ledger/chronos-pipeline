"""Concurrent-like access pattern tests.

Simulates rapid creation/deletion, simultaneous executions, retry during
execution, and concurrent analytics queries to verify thread-safety and
data consistency under contention.
"""

import threading
from unittest.mock import patch

import pytest

from app.models import WorkflowCreate, WorkflowExecution, WorkflowStatus
from app.services.analytics_service import clear_cache, get_summary, invalidate_cache
from app.services.workflow_engine import (
    LogOutput,
    _executions,
    _index_execution,
    cancel_execution,
    clear_all,
    create_workflow,
    delete_workflow,
    execute_workflow,
    get_execution,
    get_workflow,
    list_executions,
    list_workflows,
    retry_execution,
    update_workflow,
)
from app.models import WorkflowUpdate


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    clear_cache()
    yield
    clear_all()
    clear_cache()


def _make_wf(name: str = "WF", action: str = "log") -> str:
    wf = create_workflow(WorkflowCreate(
        name=name,
        tasks=[{"name": "Step", "action": action, "parameters": {"message": "ok"}}],
    ))
    return wf.id


class TestRapidCreationDeletion:
    """Simulate rapid creation and deletion of workflows."""

    def test_create_delete_cycle(self):
        """Create and immediately delete 50 workflows."""
        for i in range(50):
            wf_id = _make_wf(f"Rapid-{i}")
            assert delete_workflow(wf_id) is True
        assert len(list_workflows()) == 0

    def test_concurrent_creates(self):
        """Multiple threads creating workflows simultaneously."""
        results = []
        errors = []

        def creator(idx):
            try:
                wf = create_workflow(WorkflowCreate(name=f"Thread-{idx}"))
                results.append(wf.id)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=creator, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(results) == 20
        assert len(set(results)) == 20

    def test_concurrent_deletes(self):
        """Create workflows, then delete them concurrently."""
        ids = [_make_wf(f"Del-{i}") for i in range(20)]
        results = []
        errors = []

        def deleter(wf_id):
            try:
                results.append(delete_workflow(wf_id))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=deleter, args=(wid,)) for wid in ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert sum(1 for r in results if r) == 20

    def test_interleaved_create_and_delete(self):
        """Alternate between creating and deleting workflows."""
        created_ids = []
        for i in range(30):
            wf_id = _make_wf(f"Interleave-{i}")
            created_ids.append(wf_id)
            if i % 3 == 0 and created_ids:
                delete_workflow(created_ids.pop(0))
        remaining = list_workflows(limit=1000)
        assert len(remaining) == len(created_ids)


class TestSimultaneousExecutions:
    """Simulate multiple executions happening at the same time."""

    def test_concurrent_executions_of_same_workflow(self):
        """Execute the same workflow from multiple threads."""
        wf_id = _make_wf("Concurrent Exec")
        results = []
        errors = []

        def executor():
            try:
                ex = execute_workflow(wf_id)
                results.append(ex)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=executor) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(results) == 10
        assert all(r.status == WorkflowStatus.COMPLETED for r in results)
        assert len(set(r.id for r in results)) == 10

    def test_concurrent_executions_of_different_workflows(self):
        """Execute different workflows concurrently."""
        wf_ids = [_make_wf(f"ConcWF-{i}") for i in range(10)]
        results = []
        errors = []

        def executor(wid):
            try:
                results.append(execute_workflow(wid))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=executor, args=(wid,)) for wid in wf_ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(results) == 10

    def test_execution_count_consistency(self):
        """Verify execution count is correct after concurrent executions."""
        wf_id = _make_wf("Count Check")
        threads = []
        for _ in range(25):
            t = threading.Thread(target=execute_workflow, args=(wf_id,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

        execs = list_executions(workflow_id=wf_id, limit=1000)
        assert len(execs) == 25


class TestRetryDuringExecution:
    """Simulate retry operations while other executions are in progress."""

    def test_retry_while_new_execution_runs(self):
        """Retry a failed execution while a new one completes."""
        wf_id = _make_wf("Retry-While-Running", action="unknown_action")
        ex1 = execute_workflow(wf_id)
        assert ex1.status == WorkflowStatus.FAILED

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda a, p: LogOutput(message="fixed"),
        ):
            retried = retry_execution(ex1.id)
        assert retried.status == WorkflowStatus.COMPLETED

        ex2 = execute_workflow(wf_id)
        assert ex2.status == WorkflowStatus.FAILED
        assert ex2.id != retried.id

    def test_concurrent_retries_of_different_executions(self):
        """Retry multiple failed executions concurrently."""
        wf_id = _make_wf("Multi-Retry", action="unknown_action")
        exec_ids = []
        for _ in range(10):
            ex = execute_workflow(wf_id)
            exec_ids.append(ex.id)

        results = []
        errors = []

        def retrier(eid):
            try:
                with patch(
                    "app.services.workflow_engine._run_action",
                    side_effect=lambda a, p: LogOutput(message="ok"),
                ):
                    results.append(retry_execution(eid))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=retrier, args=(eid,)) for eid in exec_ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(results) == 10
        assert all(r.status == WorkflowStatus.COMPLETED for r in results)

    def test_retry_does_not_affect_original(self):
        """Retrying creates a new execution without modifying the original."""
        wf_id = _make_wf("Retry-Isolation", action="unknown_action")
        original = execute_workflow(wf_id)
        original_status = original.status

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda a, p: LogOutput(message="ok"),
        ):
            retried = retry_execution(original.id)

        assert get_execution(original.id).status == original_status
        assert retried.id != original.id


class TestConcurrentCancellation:
    """Simulate cancellation during concurrent operations."""

    def test_cancel_while_others_execute(self):
        """Cancel a pending execution while others complete."""
        wf_id = _make_wf("Cancel-Concurrent")
        pending = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.PENDING,
        )
        _executions[pending.id] = pending
        _index_execution(pending)

        execute_workflow(wf_id)
        result = cancel_execution(pending.id)
        assert result.status == WorkflowStatus.CANCELLED

        execs = list_executions(workflow_id=wf_id, limit=1000)
        statuses = {e.status for e in execs}
        assert WorkflowStatus.CANCELLED in statuses
        assert WorkflowStatus.COMPLETED in statuses

    def test_double_cancel_raises(self):
        """Cancelling an already-cancelled execution raises ValueError."""
        wf_id = _make_wf("Double-Cancel")
        pending = WorkflowExecution(
            workflow_id=wf_id,
            status=WorkflowStatus.RUNNING,
        )
        _executions[pending.id] = pending
        _index_execution(pending)

        cancel_execution(pending.id)
        with pytest.raises(ValueError, match="Only running or pending"):
            cancel_execution(pending.id)


class TestConcurrentAnalytics:
    """Verify analytics remain consistent under concurrent access."""

    def test_concurrent_summary_reads(self):
        """Multiple threads reading analytics summary simultaneously."""
        _make_wf("Analytics-Conc")
        execute_workflow(list_workflows()[0].id)
        clear_cache()

        results = []
        errors = []

        def reader():
            try:
                results.append(get_summary(days=30))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(results) == 10
        assert all(r.total_executions == 1 for r in results)

    def test_analytics_with_concurrent_invalidation(self):
        """Read analytics while another thread invalidates the cache."""
        _make_wf("Inv-Conc")
        execute_workflow(list_workflows()[0].id)
        clear_cache()

        errors = []

        def reader():
            try:
                for _ in range(20):
                    get_summary(days=30)
            except Exception as exc:
                errors.append(exc)

        def invalidator():
            try:
                for _ in range(20):
                    invalidate_cache()
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=invalidator),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []


class TestConcurrentUpdates:
    """Simulate concurrent workflow updates."""

    def test_concurrent_updates_to_same_workflow(self):
        """Multiple threads updating the same workflow."""
        wf_id = _make_wf("Update-Conc")
        errors = []

        def updater(idx):
            try:
                update_workflow(wf_id, WorkflowUpdate(name=f"Updated-{idx}"))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=updater, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        wf = get_workflow(wf_id)
        assert wf is not None
        assert wf.name.startswith("Updated-")

    def test_update_and_execute_concurrently(self):
        """Update a workflow while it's being executed."""
        wf_id = _make_wf("Update-Exec-Conc")
        errors = []
        exec_results = []

        def updater():
            try:
                for i in range(5):
                    update_workflow(wf_id, WorkflowUpdate(description=f"v{i}"))
            except Exception as exc:
                errors.append(exc)

        def executor():
            try:
                for _ in range(5):
                    exec_results.append(execute_workflow(wf_id))
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=updater)
        t2 = threading.Thread(target=executor)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert errors == []
        assert len(exec_results) == 5


class TestConcurrentTagOperations:
    """Verify tag operations under concurrent access."""

    def test_concurrent_tag_adds(self):
        """Add tags from multiple threads simultaneously."""
        from app.services.workflow_engine import add_tags, get_workflow
        wf_id = _make_wf("Tag-Conc")
        errors = []

        def tagger(idx):
            try:
                add_tags(wf_id, [f"tag-{idx}"])
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=tagger, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        wf = get_workflow(wf_id)
        assert len(wf.tags) >= 10

    def test_concurrent_search_operations(self):
        """Search workflows from multiple threads."""
        for i in range(20):
            create_workflow(WorkflowCreate(name=f"Searchable-{i}"))

        from app.services.workflow_engine import search_workflows
        results = []
        errors = []

        def searcher():
            try:
                results.append(len(search_workflows("Searchable", limit=100)))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=searcher) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert all(r == 20 for r in results)

    def test_concurrent_list_and_create(self):
        """List workflows while creating new ones concurrently."""
        errors = []

        def creator():
            try:
                for i in range(10):
                    create_workflow(WorkflowCreate(name=f"ListCreate-{i}"))
            except Exception as exc:
                errors.append(exc)

        def lister():
            try:
                for _ in range(10):
                    list_workflows(limit=100)
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=creator)
        t2 = threading.Thread(target=lister)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert errors == []
        assert len(list_workflows(limit=100)) == 10

    def test_concurrent_execution_and_analytics(self):
        """Execute workflows while querying analytics concurrently."""
        wf_id = _make_wf("Exec-Analytics-Conc")
        errors = []

        def executor():
            try:
                for _ in range(5):
                    execute_workflow(wf_id)
            except Exception as exc:
                errors.append(exc)

        def analytics_reader():
            try:
                for _ in range(5):
                    clear_cache()
                    get_summary(days=30)
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=executor)
        t2 = threading.Thread(target=analytics_reader)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert errors == []
