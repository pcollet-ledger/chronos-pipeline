"""Tests simulating concurrent-like access patterns.

Covers rapid creation/deletion, simultaneous executions, and
retry during execution.
"""

import threading

import pytest

from app.models import WorkflowCreate, WorkflowExecution, WorkflowStatus
from app.services.workflow_engine import (
    _executions,
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


class TestConcurrentCreation:
    def test_rapid_create_delete(self):
        for _ in range(50):
            wf = create_workflow(WorkflowCreate(name="Ephemeral"))
            delete_workflow(wf.id)
        assert len(list_workflows(limit=1000)) == 0

    def test_threaded_creation(self):
        errors = []
        created_ids = []
        lock = threading.Lock()

        def creator(idx: int) -> None:
            try:
                wf = create_workflow(WorkflowCreate(name=f"Thread-{idx}"))
                with lock:
                    created_ids.append(wf.id)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=creator, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(created_ids) == 20

    def test_threaded_execution(self):
        wf = create_workflow(WorkflowCreate(
            name="Threaded Exec",
            tasks=[{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        ))
        errors = []

        def executor() -> None:
            try:
                ex = execute_workflow(wf.id)
                assert ex.status == WorkflowStatus.COMPLETED
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=executor) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        execs = list_executions(workflow_id=wf.id, limit=1000)
        assert len(execs) == 10

    def test_create_and_list_concurrent(self):
        errors = []

        def creator() -> None:
            try:
                for i in range(10):
                    create_workflow(WorkflowCreate(name=f"C-{i}"))
            except Exception as exc:
                errors.append(exc)

        def lister() -> None:
            try:
                for _ in range(10):
                    list_workflows(limit=100)
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

    def test_execute_and_retry_concurrent(self):
        wf = create_workflow(WorkflowCreate(
            name="Retry Concurrent",
            tasks=[{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        ))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.FAILED

        errors = []

        def retrier() -> None:
            try:
                retry_execution(ex.id)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=retrier) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
