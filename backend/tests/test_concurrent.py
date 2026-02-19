"""Concurrent-like access pattern tests.

Simulates rapid creation/deletion, simultaneous executions, and
retry during execution to verify data integrity.
"""

import threading

import pytest

from app.models import WorkflowCreate, WorkflowExecution, WorkflowStatus
from app.services.workflow_engine import (
    _executions,
    cancel_execution,
    clear_all,
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
    yield
    clear_all()


class TestConcurrentCreationDeletion:
    def test_rapid_create_delete(self):
        errors = []

        def create_and_delete():
            try:
                for _ in range(20):
                    wf = create_workflow(WorkflowCreate(name="Ephemeral"))
                    delete_workflow(wf.id)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=create_and_delete) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []

    def test_rapid_creation(self):
        errors = []
        ids = []
        lock = threading.Lock()

        def creator():
            try:
                for i in range(10):
                    wf = create_workflow(WorkflowCreate(name=f"WF-{threading.current_thread().name}-{i}"))
                    with lock:
                        ids.append(wf.id)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=creator) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert len(ids) == 50

    def test_create_while_listing(self):
        errors = []

        def creator():
            try:
                for i in range(20):
                    create_workflow(WorkflowCreate(name=f"WF-{i}"))
            except Exception as exc:
                errors.append(exc)

        def lister():
            try:
                for _ in range(20):
                    list_workflows()
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=creator),
            threading.Thread(target=lister),
            threading.Thread(target=lister),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []


class TestConcurrentExecutions:
    def test_simultaneous_executions(self):
        wf = create_workflow(WorkflowCreate(
            name="Concurrent",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        errors = []
        results = []
        lock = threading.Lock()

        def executor():
            try:
                ex = execute_workflow(wf.id)
                with lock:
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

    def test_execute_while_listing(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        errors = []

        def executor():
            try:
                for _ in range(10):
                    execute_workflow(wf.id)
            except Exception as exc:
                errors.append(exc)

        def lister():
            try:
                for _ in range(10):
                    list_executions()
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=executor),
            threading.Thread(target=lister),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []


class TestConcurrentRetryAndCancel:
    def test_retry_multiple_failures(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        ))
        exec_ids = []
        for _ in range(5):
            ex = execute_workflow(wf.id)
            exec_ids.append(ex.id)

        errors = []

        def retrier(eid):
            try:
                retry_execution(eid)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=retrier, args=(eid,)) for eid in exec_ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []

    def test_cancel_while_creating(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        errors = []

        def creator():
            try:
                for _ in range(10):
                    ex = WorkflowExecution(
                        workflow_id=wf.id,
                        status=WorkflowStatus.PENDING,
                    )
                    _executions[ex.id] = ex
                    cancel_execution(ex.id)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=creator) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
