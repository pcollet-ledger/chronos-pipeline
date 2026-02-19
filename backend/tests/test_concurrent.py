"""Concurrent-like access pattern tests for Chronos Pipeline.

Verifies correctness under rapid sequential and threaded access to
the in-memory stores — creating, executing, retrying, cancelling,
and reading workflows simultaneously.

Note: The in-memory engine is not designed for true multi-threaded
concurrency, but these tests exercise rapid interleaved operations
to surface race-condition-like bugs.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowStatus
from app.services.analytics_service import clear_cache, get_summary
from app.services.workflow_engine import (
    LogOutput,
    clear_all,
    create_workflow,
    execute_workflow,
    get_execution,
    get_workflow,
    list_executions,
    list_workflows,
    retry_execution,
    cancel_execution,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    clear_cache()
    yield
    clear_all()
    clear_cache()


@pytest.fixture
def client():
    return TestClient(app)


def _simple_workflow(**overrides) -> WorkflowCreate:
    defaults = {
        "name": "concurrent-wf",
        "tasks": [{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
    }
    defaults.update(overrides)
    return WorkflowCreate(**defaults)


# ---------------------------------------------------------------------------
# Threaded creation
# ---------------------------------------------------------------------------

class TestConcurrentCreation:
    """Verify workflow creation under concurrent-like access."""

    def test_threaded_creation_no_duplicates(self):
        results = []

        def create(i: int):
            wf = create_workflow(WorkflowCreate(name=f"Thread-{i}"))
            results.append(wf.id)

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(create, i) for i in range(50)]
            for f in as_completed(futures):
                f.result()

        assert len(set(results)) == 50
        assert len(list_workflows(limit=1000)) == 50

    def test_threaded_creation_unique_ids(self):
        ids: list[str] = []
        lock = threading.Lock()

        def create(i: int):
            wf = create_workflow(WorkflowCreate(name=f"Unique-{i}"))
            with lock:
                ids.append(wf.id)

        threads = [threading.Thread(target=create, args=(i,)) for i in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(set(ids)) == 30

    def test_rapid_sequential_creation(self):
        for i in range(100):
            wf = create_workflow(WorkflowCreate(name=f"Rapid-{i}"))
            assert wf.id is not None
        assert len(list_workflows(limit=1000)) == 100


# ---------------------------------------------------------------------------
# Threaded execution
# ---------------------------------------------------------------------------

class TestConcurrentExecution:
    """Verify execution under concurrent-like access."""

    def test_threaded_execution_same_workflow(self):
        wf = create_workflow(_simple_workflow())
        results = []
        lock = threading.Lock()

        def run():
            ex = execute_workflow(wf.id)
            with lock:
                results.append(ex)

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(run) for _ in range(40)]
            for f in as_completed(futures):
                f.result()

        assert len(results) == 40
        assert all(r.status == WorkflowStatus.COMPLETED for r in results)
        assert len(list_executions(workflow_id=wf.id, limit=1000)) == 40

    def test_threaded_execution_different_workflows(self):
        wfs = [create_workflow(_simple_workflow(name=f"WF-{i}")) for i in range(10)]
        results = []
        lock = threading.Lock()

        def run(wf_id: str):
            ex = execute_workflow(wf_id)
            with lock:
                results.append(ex)

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(run, wf.id) for wf in wfs for _ in range(5)]
            for f in as_completed(futures):
                f.result()

        assert len(results) == 50
        for wf in wfs:
            execs = list_executions(workflow_id=wf.id, limit=1000)
            assert len(execs) == 5

    def test_execution_ids_globally_unique(self):
        wf = create_workflow(_simple_workflow())
        ids: list[str] = []
        lock = threading.Lock()

        def run():
            ex = execute_workflow(wf.id)
            with lock:
                ids.append(ex.id)

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(run) for _ in range(30)]
            for f in as_completed(futures):
                f.result()

        assert len(set(ids)) == 30


# ---------------------------------------------------------------------------
# Threaded reads during writes
# ---------------------------------------------------------------------------

class TestConcurrentReadWrite:
    """Verify reads remain consistent while writes are happening."""

    def test_list_workflows_during_creation(self):
        errors = []

        def create_loop():
            for i in range(30):
                create_workflow(WorkflowCreate(name=f"CW-{i}"))

        def read_loop():
            for _ in range(30):
                try:
                    wfs = list_workflows(limit=1000)
                    assert isinstance(wfs, list)
                except Exception as e:
                    errors.append(e)

        t1 = threading.Thread(target=create_loop)
        t2 = threading.Thread(target=read_loop)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0
        assert len(list_workflows(limit=1000)) == 30

    def test_get_workflow_during_updates(self, client):
        resp = client.post("/api/workflows/", json={"name": "Updatable"})
        wf_id = resp.json()["id"]
        errors = []

        def update_loop():
            for i in range(20):
                client.patch(f"/api/workflows/{wf_id}", json={"name": f"V{i}"})

        def read_loop():
            for _ in range(20):
                try:
                    wf = get_workflow(wf_id)
                    assert wf is not None
                except Exception as e:
                    errors.append(e)

        t1 = threading.Thread(target=update_loop)
        t2 = threading.Thread(target=read_loop)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0

    def test_list_executions_during_execution(self):
        wf = create_workflow(_simple_workflow())
        errors = []

        def exec_loop():
            for _ in range(20):
                execute_workflow(wf.id)

        def read_loop():
            for _ in range(20):
                try:
                    execs = list_executions(workflow_id=wf.id, limit=1000)
                    assert isinstance(execs, list)
                except Exception as e:
                    errors.append(e)

        t1 = threading.Thread(target=exec_loop)
        t2 = threading.Thread(target=read_loop)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0
        assert len(list_executions(workflow_id=wf.id, limit=1000)) == 20


# ---------------------------------------------------------------------------
# Threaded retry and cancellation
# ---------------------------------------------------------------------------

class TestConcurrentRetryCancel:
    """Verify retry and cancel under concurrent-like access."""

    def test_threaded_retry_different_executions(self):
        wf = create_workflow(WorkflowCreate(
            name="Retry-Concurrent",
            tasks=[{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        ))
        exec_ids = [execute_workflow(wf.id).id for _ in range(20)]

        retried = []
        lock = threading.Lock()

        def do_retry(eid: str):
            with patch(
                "app.services.workflow_engine._run_action",
                side_effect=lambda action, params: LogOutput(message="fixed"),
            ):
                r = retry_execution(eid)
                with lock:
                    retried.append(r)

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(do_retry, eid) for eid in exec_ids]
            for f in as_completed(futures):
                f.result()

        assert len(retried) == 20
        assert all(r.status == WorkflowStatus.COMPLETED for r in retried)

    def test_cancel_already_completed_raises(self):
        """Synchronous execution completes instantly, so cancel must raise."""
        wf = create_workflow(_simple_workflow())
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        with pytest.raises(ValueError, match="Only running or pending"):
            cancel_execution(ex.id)

    def test_cancel_pending_execution(self):
        """A PENDING execution (no tasks started) can be cancelled."""
        wf = create_workflow(WorkflowCreate(name="cancel-pending"))
        ex = execute_workflow(wf.id)
        # Since the workflow has no tasks, it completes immediately.
        # Create a manual PENDING execution to test cancellation.
        from app.services.workflow_engine import _executions
        from app.models import WorkflowExecution
        import uuid

        pending_id = str(uuid.uuid4())
        pending_ex = WorkflowExecution(
            id=pending_id,
            workflow_id=wf.id,
            status=WorkflowStatus.PENDING,
            trigger="manual",
        )
        _executions[pending_id] = pending_ex

        result = cancel_execution(pending_id)
        assert result is not None
        assert result.status == WorkflowStatus.CANCELLED


# ---------------------------------------------------------------------------
# Threaded analytics
# ---------------------------------------------------------------------------

class TestConcurrentAnalytics:
    """Verify analytics under concurrent-like access."""

    def test_analytics_during_executions(self):
        wf = create_workflow(_simple_workflow())
        errors = []

        def exec_loop():
            for _ in range(20):
                execute_workflow(wf.id)

        def analytics_loop():
            for _ in range(10):
                try:
                    clear_cache()
                    summary = get_summary(days=30)
                    assert summary.total_workflows >= 0
                except Exception as e:
                    errors.append(e)

        t1 = threading.Thread(target=exec_loop)
        t2 = threading.Thread(target=analytics_loop)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0

    def test_cache_invalidation_under_load(self):
        wf = create_workflow(_simple_workflow())
        for _ in range(10):
            execute_workflow(wf.id)

        clear_cache()
        s1 = get_summary(days=30)
        assert s1.total_executions == 10

        for _ in range(10):
            execute_workflow(wf.id)

        clear_cache()
        s2 = get_summary(days=30)
        assert s2.total_executions == 20


# ---------------------------------------------------------------------------
# API-level concurrent-like access
# ---------------------------------------------------------------------------

class TestConcurrentAPI:
    """Verify API endpoints under concurrent-like access."""

    def test_threaded_api_creation(self, client):
        ids: list[str] = []
        lock = threading.Lock()

        def create(i: int):
            resp = client.post("/api/workflows/", json={"name": f"API-{i}"})
            assert resp.status_code == 201
            with lock:
                ids.append(resp.json()["id"])

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(create, i) for i in range(20)]
            for f in as_completed(futures):
                f.result()

        assert len(set(ids)) == 20

    def test_threaded_api_execution(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "API-Exec",
            "tasks": [{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]

        statuses: list[str] = []
        lock = threading.Lock()

        def run():
            r = client.post(f"/api/workflows/{wf_id}/execute")
            assert r.status_code == 200
            with lock:
                statuses.append(r.json()["status"])

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(run) for _ in range(20)]
            for f in as_completed(futures):
                f.result()

        assert len(statuses) == 20
        assert all(s == "completed" for s in statuses)

    def test_threaded_api_mixed_operations(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Mixed-Ops",
            "tasks": [{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        errors = []

        def execute():
            try:
                r = client.post(f"/api/workflows/{wf_id}/execute")
                assert r.status_code == 200
            except Exception as e:
                errors.append(e)

        def read():
            try:
                r = client.get(f"/api/workflows/{wf_id}")
                assert r.status_code == 200
            except Exception as e:
                errors.append(e)

        def list_all():
            try:
                r = client.get("/api/workflows/")
                assert r.status_code == 200
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = []
            for _ in range(10):
                futures.append(pool.submit(execute))
                futures.append(pool.submit(read))
                futures.append(pool.submit(list_all))
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0
