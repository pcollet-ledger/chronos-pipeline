"""Concurrent execution tests for Chronos Pipeline.

Verifies that concurrent operations on the in-memory stores do not
corrupt state.  Uses threading to simulate parallel requests.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowStatus
from app.services.analytics_service import clear_cache
from app.services.workflow_engine import (
    clear_all,
    create_workflow,
    execute_workflow,
    get_execution,
    list_executions,
    list_workflows,
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


class TestConcurrentWorkflowCreation:
    """Creating many workflows in parallel should not lose any."""

    def test_parallel_creates(self):
        count = 20
        results = []

        def _create(i: int):
            wf = create_workflow(WorkflowCreate(name=f"WF-{i}"))
            return wf.id

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(_create, i) for i in range(count)]
            for f in as_completed(futures):
                results.append(f.result())

        assert len(set(results)) == count
        assert len(list_workflows(limit=1000)) == count

    def test_parallel_creates_via_api(self, client):
        count = 15
        ids = []

        def _create_api(i: int):
            resp = client.post("/api/workflows/", json={"name": f"API-WF-{i}"})
            assert resp.status_code == 201
            return resp.json()["id"]

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(_create_api, i) for i in range(count)]
            for f in as_completed(futures):
                ids.append(f.result())

        assert len(set(ids)) == count


class TestConcurrentExecution:
    """Executing the same workflow concurrently should produce independent results."""

    def test_parallel_executions_of_same_workflow(self):
        wf = create_workflow(WorkflowCreate(
            name="Shared",
            tasks=[{"name": "Log", "action": "log", "parameters": {"message": "ok"}}],
        ))
        count = 10
        exec_ids = []

        def _execute(_: int):
            ex = execute_workflow(wf.id)
            return ex.id

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(_execute, i) for i in range(count)]
            for f in as_completed(futures):
                exec_ids.append(f.result())

        assert len(set(exec_ids)) == count
        execs = list_executions(workflow_id=wf.id, limit=100)
        assert len(execs) == count
        assert all(e.status == WorkflowStatus.COMPLETED for e in execs)

    def test_parallel_executions_different_workflows(self):
        workflows = [
            create_workflow(WorkflowCreate(
                name=f"WF-{i}",
                tasks=[{"name": "Log", "action": "log", "parameters": {"message": str(i)}}],
            ))
            for i in range(5)
        ]
        exec_ids = []

        def _execute(wf_id: str):
            ex = execute_workflow(wf_id)
            return ex.id

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(_execute, wf.id) for wf in workflows]
            for f in as_completed(futures):
                exec_ids.append(f.result())

        assert len(set(exec_ids)) == 5
        total = list_executions(limit=100)
        assert len(total) == 5


class TestConcurrentReadWrite:
    """Reads and writes happening simultaneously should not crash."""

    def test_read_during_writes(self):
        barrier = threading.Barrier(4)
        errors = []

        def _writer():
            try:
                barrier.wait(timeout=5)
                for i in range(10):
                    create_workflow(WorkflowCreate(name=f"Writer-{i}"))
            except Exception as e:
                errors.append(e)

        def _reader():
            try:
                barrier.wait(timeout=5)
                for _ in range(10):
                    list_workflows(limit=100)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=_writer),
            threading.Thread(target=_writer),
            threading.Thread(target=_reader),
            threading.Thread(target=_reader),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors

    def test_execute_and_list_simultaneously(self):
        wf = create_workflow(WorkflowCreate(
            name="SimulWF",
            tasks=[{"name": "Log", "action": "log", "parameters": {"message": "ok"}}],
        ))
        errors = []

        def _execute():
            try:
                for _ in range(5):
                    execute_workflow(wf.id)
            except Exception as e:
                errors.append(e)

        def _list():
            try:
                for _ in range(5):
                    list_executions(workflow_id=wf.id, limit=100)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=_execute),
            threading.Thread(target=_execute),
            threading.Thread(target=_list),
            threading.Thread(target=_list),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors
        execs = list_executions(workflow_id=wf.id, limit=100)
        assert len(execs) == 10


class TestConcurrentAnalytics:
    """Analytics queries during execution should not error."""

    def test_analytics_during_execution(self, client):
        wf = create_workflow(WorkflowCreate(
            name="AnalyticsWF",
            tasks=[{"name": "Log", "action": "log", "parameters": {"message": "ok"}}],
        ))
        errors = []

        def _execute():
            try:
                for _ in range(5):
                    execute_workflow(wf.id)
                    clear_cache()
            except Exception as e:
                errors.append(e)

        def _query():
            try:
                for _ in range(5):
                    client.get("/api/analytics/summary")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=_execute),
            threading.Thread(target=_query),
            threading.Thread(target=_query),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors


class TestConcurrentTagging:
    """Tagging operations in parallel should not lose tags."""

    def test_parallel_tag_additions(self):
        from app.services.workflow_engine import add_tags, get_workflow

        wf = create_workflow(WorkflowCreate(name="TagWF"))
        errors = []

        def _add_tag(tag: str):
            try:
                add_tags(wf.id, [tag])
            except Exception as e:
                errors.append(e)

        tags = [f"tag-{i}" for i in range(20)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(_add_tag, tags))

        assert not errors
        result = get_workflow(wf.id)
        assert len(result.tags) == 20
        assert set(result.tags) == set(tags)
