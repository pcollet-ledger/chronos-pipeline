"""Stress tests creating 100+ workflows, executing, retrying, and verifying analytics.

These tests verify the system handles large volumes of data correctly
and that indexes, analytics, and retry logic all work under load.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowStatus
from app.services.analytics_service import clear_cache, get_summary
from app.services.workflow_engine import (
    clear_all,
    create_workflow,
    execute_workflow,
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


@pytest.fixture
def client():
    return TestClient(app)


class TestStressWorkflows:
    """Create and manage 100+ workflows."""

    def test_create_150_workflows(self):
        for i in range(150):
            wf = create_workflow(WorkflowCreate(name=f"WF-{i}", tags=[f"batch-{i % 10}"]))
            assert wf.id is not None

        all_wfs = list_workflows(limit=1000)
        assert len(all_wfs) == 150

    def test_tag_filtering_at_scale(self):
        for i in range(100):
            create_workflow(WorkflowCreate(
                name=f"WF-{i}",
                tags=["group-a" if i % 3 == 0 else "group-b"],
            ))

        group_a = list_workflows(tag="group-a", limit=1000)
        group_b = list_workflows(tag="group-b", limit=1000)
        assert len(group_a) + len(group_b) == 100

    def test_pagination_at_scale(self):
        for i in range(100):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))

        all_ids = set()
        for offset in range(0, 100, 20):
            page = list_workflows(limit=20, offset=offset)
            for wf in page:
                all_ids.add(wf.id)
        assert len(all_ids) == 100


class TestStressExecutions:
    """Execute 100+ workflows and verify correctness."""

    def test_execute_100_workflows(self):
        wf = create_workflow(WorkflowCreate(
            name="Stress WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        for _ in range(100):
            ex = execute_workflow(wf.id)
            assert ex.status == WorkflowStatus.COMPLETED

        execs = list_executions(workflow_id=wf.id, limit=1000)
        assert len(execs) == 100

    def test_mixed_success_and_failure(self):
        good = create_workflow(WorkflowCreate(
            name="Good",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        bad = create_workflow(WorkflowCreate(
            name="Bad",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))

        for _ in range(50):
            execute_workflow(good.id)
            execute_workflow(bad.id)

        completed = list_executions(status=WorkflowStatus.COMPLETED, limit=1000)
        failed = list_executions(status=WorkflowStatus.FAILED, limit=1000)
        assert len(completed) == 50
        assert len(failed) == 50

    def test_analytics_after_100_executions(self):
        wf = create_workflow(WorkflowCreate(
            name="Analytics Stress",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        for _ in range(100):
            execute_workflow(wf.id)

        clear_cache()
        summary = get_summary(days=30)
        assert summary.total_executions == 100
        assert summary.success_rate == 100.0
        assert summary.total_workflows == 1


class TestStressRetry:
    """Retry failures at scale."""

    def test_retry_50_failures(self):
        from app.services.workflow_engine import LogOutput

        wf = create_workflow(WorkflowCreate(
            name="Retry Stress",
            tasks=[
                {"name": "Good", "action": "log", "parameters": {"message": "ok"}},
                {"name": "Bad", "action": "unknown_action", "parameters": {}},
            ],
        ))

        exec_ids = []
        for _ in range(50):
            ex = execute_workflow(wf.id)
            assert ex.status == WorkflowStatus.FAILED
            exec_ids.append(ex.id)

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            for eid in exec_ids:
                retry_ex = retry_execution(eid)
                assert retry_ex.status == WorkflowStatus.COMPLETED

        all_execs = list_executions(workflow_id=wf.id, limit=1000)
        assert len(all_execs) == 100

    def test_analytics_after_retries(self):
        from app.services.workflow_engine import LogOutput

        wf = create_workflow(WorkflowCreate(
            name="Retry Analytics",
            tasks=[{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        ))

        for _ in range(20):
            ex = execute_workflow(wf.id)
            with patch(
                "app.services.workflow_engine._run_action",
                side_effect=lambda action, params: LogOutput(message="ok"),
            ):
                retry_execution(ex.id)

        clear_cache()
        summary = get_summary(days=30)
        assert summary.total_executions == 40
        completed = list_executions(status=WorkflowStatus.COMPLETED, limit=1000)
        failed = list_executions(status=WorkflowStatus.FAILED, limit=1000)
        assert len(completed) == 20
        assert len(failed) == 20


class TestStressViaAPI:
    """Stress tests through the HTTP API."""

    def test_create_and_execute_100_via_api(self, client):
        wf_id = client.post("/api/workflows/", json={
            "name": "API Stress",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()["id"]

        for _ in range(100):
            resp = client.post(f"/api/workflows/{wf_id}/execute")
            assert resp.status_code == 200

        execs = client.get(f"/api/workflows/{wf_id}/executions", params={"limit": 1000}).json()
        assert len(execs) == 100

    def test_bulk_operations_at_scale(self, client):
        ids = []
        for i in range(50):
            resp = client.post("/api/workflows/", json={"name": f"Bulk-{i}"})
            ids.append(resp.json()["id"])

        resp = client.post("/api/workflows/bulk-delete", json={"ids": ids})
        assert resp.json()["deleted"] == 50

        remaining = client.get("/api/workflows/").json()
        assert len(remaining) == 0

    def test_many_tags_at_scale(self, client):
        for i in range(50):
            tags = [f"tag-{j}" for j in range(10)]
            client.post("/api/workflows/", json={"name": f"Tagged-{i}", "tags": tags})
        resp = client.get("/api/workflows/", params={"tag": "tag-0", "limit": 1000})
        assert len(resp.json()) == 50

    def test_concurrent_like_executions(self):
        wf = create_workflow(WorkflowCreate(
            name="Concurrent",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        results = [execute_workflow(wf.id) for _ in range(50)]
        assert all(r.status == WorkflowStatus.COMPLETED for r in results)
        assert len(list_executions(workflow_id=wf.id, limit=1000)) == 50

    def test_stress_update_workflows(self, client):
        resp = client.post("/api/workflows/", json={"name": "Update Stress"})
        wf_id = resp.json()["id"]
        for i in range(100):
            client.patch(f"/api/workflows/{wf_id}", json={"name": f"Updated-{i}"})
        final = client.get(f"/api/workflows/{wf_id}").json()
        assert final["name"] == "Updated-99"

    def test_stress_delete_and_recreate(self, client):
        for _ in range(50):
            resp = client.post("/api/workflows/", json={"name": "Ephemeral"})
            wf_id = resp.json()["id"]
            client.delete(f"/api/workflows/{wf_id}")
        remaining = client.get("/api/workflows/").json()
        assert len(remaining) == 0

    def test_stress_list_executions_all(self, client):
        wf_id = client.post("/api/workflows/", json={
            "name": "Exec List Stress",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()["id"]
        for _ in range(50):
            client.post(f"/api/workflows/{wf_id}/execute")
        resp = client.get("/api/tasks/executions", params={"limit": 1000})
        assert len(resp.json()) == 50


class TestStressSearch:
    """Search under load."""

    def test_search_among_200_workflows(self):
        for i in range(200):
            create_workflow(WorkflowCreate(name=f"Pipeline-{i}" if i % 2 == 0 else f"Job-{i}"))
        from app.services.workflow_engine import search_workflows
        results = search_workflows("Pipeline", limit=1000)
        assert len(results) == 100

    def test_search_with_tags_at_scale(self):
        for i in range(100):
            create_workflow(WorkflowCreate(
                name=f"WF-{i}",
                tags=["alpha"] if i < 50 else ["beta"],
            ))
        from app.services.workflow_engine import search_workflows
        results = search_workflows("WF", tag="alpha", limit=1000)
        assert len(results) == 50

    def test_clone_at_scale(self):
        from app.services.workflow_engine import clone_workflow
        wf = create_workflow(WorkflowCreate(
            name="Template",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        for _ in range(50):
            cloned = clone_workflow(wf.id)
            assert cloned is not None
        all_wfs = list_workflows(limit=1000)
        assert len(all_wfs) == 51

    def test_versioning_at_scale(self):
        from app.services.workflow_engine import update_workflow, get_workflow_history
        from app.models import WorkflowUpdate
        wf = create_workflow(WorkflowCreate(name="Versioned"))
        for i in range(50):
            update_workflow(wf.id, WorkflowUpdate(name=f"V{i+2}"))
        history = get_workflow_history(wf.id)
        assert len(history) == 50

    def test_delete_half_and_verify_analytics(self):
        wf_ids = []
        for i in range(100):
            wf = create_workflow(WorkflowCreate(
                name=f"WF-{i}",
                tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
            ))
            execute_workflow(wf.id)
            wf_ids.append(wf.id)

        from app.services.workflow_engine import delete_workflow
        for wid in wf_ids[:50]:
            delete_workflow(wid)

        assert len(list_workflows(limit=1000)) == 50
        clear_cache()
        summary = get_summary(days=30)
        assert summary.total_workflows == 50
        assert summary.total_executions == 100
