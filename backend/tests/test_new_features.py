"""Tests for new backend features: dry-run, cloning, tagging, search,
versioning, execution comparison, topological sort edge cases, and formatters.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowStatus, WorkflowUpdate
from app.services.analytics_service import clear_cache
from app.services.workflow_engine import (
    _executions,
    _topological_sort,
    _workflow_versions,
    add_tags,
    clear_all,
    clone_workflow,
    compare_executions,
    create_workflow,
    delete_workflow,
    dry_run_workflow,
    execute_workflow,
    get_execution,
    get_workflow,
    get_workflow_history,
    get_workflow_version,
    list_executions,
    list_workflows,
    remove_tag,
    search_workflows,
    update_workflow,
)
from app.models import TaskDefinition


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


# ===========================================================================
# Dry-run execution
# ===========================================================================


class TestDryRunService:
    def test_basic_dry_run(self):
        wf = create_workflow(WorkflowCreate(
            name="DR",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result is not None
        assert result.status == WorkflowStatus.COMPLETED
        assert result.trigger == "dry_run"
        assert len(result.task_results) == 1
        assert result.task_results[0].output["dry_run"] is True

    def test_dry_run_not_stored(self):
        wf = create_workflow(WorkflowCreate(
            name="DR",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        result = dry_run_workflow(wf.id)
        assert get_execution(result.id) is None
        assert len(list_executions()) == 0

    def test_dry_run_not_found(self):
        assert dry_run_workflow("nonexistent") is None

    def test_dry_run_with_dependencies(self):
        wf = create_workflow(WorkflowCreate(
            name="DR-Deps",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {}, "depends_on": ["b"]},
            ],
        ))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED
        task_ids = [tr.task_id for tr in result.task_results]
        assert task_ids.index("a") < task_ids.index("b") < task_ids.index("c")

    def test_dry_run_unknown_actions_succeed(self):
        wf = create_workflow(WorkflowCreate(
            name="DR-Unknown",
            tasks=[{"name": "S", "action": "totally_fake_action", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED

    def test_dry_run_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.task_results == []

    def test_dry_run_order_field(self):
        wf = create_workflow(WorkflowCreate(
            name="DR-Order",
            tasks=[
                {"name": "A", "action": "log", "parameters": {}},
                {"name": "B", "action": "log", "parameters": {}},
            ],
        ))
        result = dry_run_workflow(wf.id)
        assert result.task_results[0].output["order"] == 0
        assert result.task_results[1].output["order"] == 1

    def test_dry_run_metadata(self):
        wf = create_workflow(WorkflowCreate(
            name="DR",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result.metadata["dry_run"] is True

    def test_dry_run_has_timestamps(self):
        wf = create_workflow(WorkflowCreate(name="DR"))
        result = dry_run_workflow(wf.id)
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_dry_run_does_not_affect_analytics(self):
        wf = create_workflow(WorkflowCreate(
            name="DR",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        dry_run_workflow(wf.id)
        assert len(list_executions()) == 0


class TestDryRunAPI:
    def test_dry_run_endpoint(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "DR",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        resp = client.post(f"/api/workflows/{wf_id}/dry-run")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
        assert resp.json()["task_results"][0]["output"]["dry_run"] is True

    def test_dry_run_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/dry-run")
        assert resp.status_code == 404


# ===========================================================================
# Workflow cloning
# ===========================================================================


class TestCloneService:
    def test_clone_basic(self):
        wf = create_workflow(WorkflowCreate(
            name="Original",
            description="desc",
            tags=["a", "b"],
            tasks=[{"name": "S", "action": "log", "parameters": {"k": "v"}}],
        ))
        clone = clone_workflow(wf.id)
        assert clone is not None
        assert clone.id != wf.id
        assert clone.name == "Original (copy)"
        assert clone.description == "desc"
        assert clone.tags == ["a", "b"]
        assert len(clone.tasks) == 1

    def test_clone_not_found(self):
        assert clone_workflow("nonexistent") is None

    def test_clone_deep_independence(self):
        wf = create_workflow(WorkflowCreate(
            name="Orig",
            tasks=[{"name": "S", "action": "log", "parameters": {"k": "v"}}],
        ))
        clone = clone_workflow(wf.id)
        clone.tasks[0].parameters["k"] = "changed"
        assert wf.tasks[0].parameters["k"] == "v"

    def test_clone_with_dependencies(self):
        wf = create_workflow(WorkflowCreate(
            name="Deps",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        ))
        clone = clone_workflow(wf.id)
        assert len(clone.tasks) == 2

    def test_clone_appears_in_list(self):
        wf = create_workflow(WorkflowCreate(name="Orig"))
        clone_workflow(wf.id)
        assert len(list_workflows()) == 2

    def test_clone_preserves_schedule(self):
        wf = create_workflow(WorkflowCreate(name="Sched", schedule="0 8 * * *"))
        clone = clone_workflow(wf.id)
        assert clone.schedule == "0 8 * * *"

    def test_clone_tasks_have_new_ids(self):
        wf = create_workflow(WorkflowCreate(
            name="Orig",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        clone = clone_workflow(wf.id)
        assert clone.tasks[0].id != wf.tasks[0].id

    def test_clone_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        clone = clone_workflow(wf.id)
        assert clone.tasks == []

    def test_clone_can_be_executed(self):
        wf = create_workflow(WorkflowCreate(
            name="Orig",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        clone = clone_workflow(wf.id)
        ex = execute_workflow(clone.id)
        assert ex.status == WorkflowStatus.COMPLETED

    def test_clone_can_be_deleted_independently(self):
        wf = create_workflow(WorkflowCreate(name="Orig"))
        clone = clone_workflow(wf.id)
        delete_workflow(clone.id)
        assert get_workflow(wf.id) is not None
        assert get_workflow(clone.id) is None


class TestCloneAPI:
    def test_clone_endpoint(self, client):
        resp = client.post("/api/workflows/", json={"name": "Orig"})
        wf_id = resp.json()["id"]
        resp = client.post(f"/api/workflows/{wf_id}/clone")
        assert resp.status_code == 201
        assert resp.json()["name"] == "Orig (copy)"

    def test_clone_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/clone")
        assert resp.status_code == 404


# ===========================================================================
# Workflow tagging
# ===========================================================================


class TestTaggingService:
    def test_add_single_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        result = add_tags(wf.id, ["new-tag"])
        assert "new-tag" in result.tags

    def test_add_multiple_tags(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        result = add_tags(wf.id, ["a", "b", "c"])
        assert set(result.tags) >= {"a", "b", "c"}

    def test_add_duplicate_tag_idempotent(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["existing"]))
        result = add_tags(wf.id, ["existing"])
        assert result.tags.count("existing") == 1

    def test_add_tags_not_found(self):
        assert add_tags("nonexistent", ["tag"]) is None

    def test_remove_existing_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["a", "b"]))
        result = remove_tag(wf.id, "a")
        assert "a" not in result.tags
        assert "b" in result.tags

    def test_remove_nonexistent_tag_raises(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["a"]))
        with pytest.raises(ValueError, match="not found"):
            remove_tag(wf.id, "nonexistent")

    def test_remove_tag_not_found_workflow(self):
        assert remove_tag("nonexistent", "tag") is None

    def test_tag_filter_reflects_changes(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        add_tags(wf.id, ["new-tag"])
        results = list_workflows(tag="new-tag")
        assert len(results) == 1

    def test_remove_tag_removes_from_filter(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["removable"]))
        remove_tag(wf.id, "removable")
        results = list_workflows(tag="removable")
        assert len(results) == 0

    def test_add_tags_to_already_tagged(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["old"]))
        result = add_tags(wf.id, ["new"])
        assert "old" in result.tags
        assert "new" in result.tags


class TestTaggingAPI:
    def test_add_tags_endpoint(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["x", "y"]})
        assert resp.status_code == 200
        assert "x" in resp.json()["tags"]

    def test_remove_tag_endpoint(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF", "tags": ["a", "b"]})
        wf_id = resp.json()["id"]
        resp = client.delete(f"/api/workflows/{wf_id}/tags/a")
        assert resp.status_code == 200
        assert "a" not in resp.json()["tags"]

    def test_remove_nonexistent_tag_404(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        resp = client.delete(f"/api/workflows/{wf_id}/tags/nope")
        assert resp.status_code == 404

    def test_add_tags_workflow_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/tags", json={"tags": ["x"]})
        assert resp.status_code == 404

    def test_remove_tag_workflow_not_found(self, client):
        resp = client.delete("/api/workflows/nonexistent/tags/x")
        assert resp.status_code == 404

    def test_tag_filter_after_add(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["filterable"]})
        resp = client.get("/api/workflows/", params={"tag": "filterable"})
        assert len(resp.json()) == 1


# ===========================================================================
# Workflow search
# ===========================================================================


class TestSearchService:
    def test_search_basic(self):
        create_workflow(WorkflowCreate(name="Alpha Pipeline"))
        create_workflow(WorkflowCreate(name="Beta Pipeline"))
        create_workflow(WorkflowCreate(name="Gamma Process"))
        results = search_workflows("pipeline")
        assert len(results) == 2

    def test_search_case_insensitive(self):
        create_workflow(WorkflowCreate(name="MyWorkflow"))
        results = search_workflows("myworkflow")
        assert len(results) == 1

    def test_search_empty_results(self):
        create_workflow(WorkflowCreate(name="Something"))
        results = search_workflows("nonexistent")
        assert results == []

    def test_search_with_tag_filter(self):
        create_workflow(WorkflowCreate(name="Alpha", tags=["prod"]))
        create_workflow(WorkflowCreate(name="Alpha Dev", tags=["dev"]))
        results = search_workflows("alpha", tag="prod")
        assert len(results) == 1

    def test_search_with_pagination(self):
        for i in range(10):
            create_workflow(WorkflowCreate(name=f"Pipeline {i}"))
        page1 = search_workflows("pipeline", limit=3, offset=0)
        page2 = search_workflows("pipeline", limit=3, offset=3)
        assert len(page1) == 3
        assert len(page2) == 3

    def test_search_special_characters(self):
        create_workflow(WorkflowCreate(name="WF (v2.0)"))
        results = search_workflows("(v2")
        assert len(results) == 1

    def test_search_partial_match(self):
        create_workflow(WorkflowCreate(name="Data Processing Pipeline"))
        results = search_workflows("proc")
        assert len(results) == 1

    def test_search_all_match(self):
        for i in range(5):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        results = search_workflows("wf")
        assert len(results) == 5

    def test_search_empty_query(self):
        create_workflow(WorkflowCreate(name="Something"))
        results = search_workflows("")
        assert len(results) == 1

    def test_search_unicode(self):
        create_workflow(WorkflowCreate(name="工作流程"))
        results = search_workflows("工作")
        assert len(results) == 1


class TestSearchAPI:
    def test_search_endpoint(self, client):
        client.post("/api/workflows/", json={"name": "Alpha Pipeline"})
        client.post("/api/workflows/", json={"name": "Beta Pipeline"})
        client.post("/api/workflows/", json={"name": "Gamma"})
        resp = client.get("/api/workflows/", params={"search": "pipeline"})
        assert len(resp.json()) == 2

    def test_search_combined_with_tag(self, client):
        client.post("/api/workflows/", json={"name": "Alpha", "tags": ["prod"]})
        client.post("/api/workflows/", json={"name": "Alpha Dev", "tags": ["dev"]})
        resp = client.get("/api/workflows/", params={"search": "alpha", "tag": "prod"})
        assert len(resp.json()) == 1

    def test_search_with_pagination(self, client):
        for i in range(10):
            client.post("/api/workflows/", json={"name": f"Pipeline {i}"})
        resp = client.get("/api/workflows/", params={"search": "pipeline", "limit": 3})
        assert len(resp.json()) == 3


# ===========================================================================
# Workflow versioning
# ===========================================================================


class TestVersioningService:
    def test_version_increments_on_update(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        history = get_workflow_history(wf.id)
        assert len(history) == 1
        assert history[0]["name"] == "V1"

    def test_multiple_updates(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        update_workflow(wf.id, WorkflowUpdate(name="V3"))
        history = get_workflow_history(wf.id)
        assert len(history) == 2
        assert history[0]["name"] == "V2"
        assert history[1]["name"] == "V1"

    def test_get_specific_version(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        v1 = get_workflow_version(wf.id, 1)
        assert v1["name"] == "V1"

    def test_get_version_out_of_range(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        assert get_workflow_version(wf.id, 1) is None
        assert get_workflow_version(wf.id, 0) is None

    def test_history_empty_for_new_workflow(self):
        wf = create_workflow(WorkflowCreate(name="New"))
        history = get_workflow_history(wf.id)
        assert history == []

    def test_history_not_found(self):
        assert get_workflow_history("nonexistent") is None

    def test_version_snapshots_independent(self):
        wf = create_workflow(WorkflowCreate(name="V1", tags=["old"]))
        update_workflow(wf.id, WorkflowUpdate(name="V2", tags=["new"]))
        v1 = get_workflow_version(wf.id, 1)
        assert v1["tags"] == ["old"]
        current = get_workflow(wf.id)
        assert current.tags == ["new"]

    def test_version_preserves_tasks(self):
        wf = create_workflow(WorkflowCreate(
            name="V1",
            tasks=[{"name": "S", "action": "log", "parameters": {"k": "v"}}],
        ))
        update_workflow(wf.id, WorkflowUpdate(tasks=[]))
        v1 = get_workflow_version(wf.id, 1)
        assert len(v1["tasks"]) == 1

    def test_version_after_multiple_field_updates(self):
        wf = create_workflow(WorkflowCreate(name="V1", description="d1"))
        update_workflow(wf.id, WorkflowUpdate(description="d2"))
        update_workflow(wf.id, WorkflowUpdate(name="V3"))
        history = get_workflow_history(wf.id)
        assert len(history) == 2

    def test_version_number_is_1_based(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        update_workflow(wf.id, WorkflowUpdate(name="V3"))
        v1 = get_workflow_version(wf.id, 1)
        v2 = get_workflow_version(wf.id, 2)
        assert v1["name"] == "V1"
        assert v2["name"] == "V2"


class TestVersioningAPI:
    def test_history_endpoint(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        resp = client.get(f"/api/workflows/{wf_id}/history")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_version_endpoint(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        resp = client.get(f"/api/workflows/{wf_id}/history/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "V1"

    def test_version_not_found(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        resp = client.get(f"/api/workflows/{wf_id}/history/99")
        assert resp.status_code == 404

    def test_history_not_found(self, client):
        resp = client.get("/api/workflows/nonexistent/history")
        assert resp.status_code == 404


# ===========================================================================
# Execution comparison
# ===========================================================================


class TestComparisonService:
    def test_compare_same_workflow(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert result is not None
        assert result["workflow_id"] == wf.id
        assert len(result["executions"]) == 2
        assert len(result["task_comparison"]) == 1

    def test_compare_different_workflows_raises(self):
        wf1 = create_workflow(WorkflowCreate(
            name="WF1",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        wf2 = create_workflow(WorkflowCreate(
            name="WF2",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf1.id)
        ex2 = execute_workflow(wf2.id)
        with pytest.raises(ValueError, match="different workflows"):
            compare_executions(ex1.id, ex2.id)

    def test_compare_not_found(self):
        assert compare_executions("a", "b") is None

    def test_compare_summary_counts(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[
                {"name": "Good", "action": "log", "parameters": {"message": "ok"}},
                {"name": "Bad", "action": "unknown_action", "parameters": {}},
            ],
        ))
        ex1 = execute_workflow(wf.id)
        assert ex1.status == WorkflowStatus.FAILED

        from app.services.workflow_engine import LogOutput
        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            from app.services.workflow_engine import retry_execution
            ex2 = retry_execution(ex1.id)

        result = compare_executions(ex1.id, ex2.id)
        assert result["summary"]["improved_count"] >= 1

    def test_compare_one_missing(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex = execute_workflow(wf.id)
        assert compare_executions(ex.id, "nonexistent") is None

    def test_compare_task_comparison_fields(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        tc = result["task_comparison"][0]
        assert "task_id" in tc
        assert "status_a" in tc
        assert "status_b" in tc
        assert "duration_diff_ms" in tc

    def test_compare_identical_executions(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert result["summary"]["unchanged_count"] == 1
        assert result["summary"]["improved_count"] == 0
        assert result["summary"]["regressed_count"] == 0

    def test_compare_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert result["task_comparison"] == []

    def test_compare_preserves_workflow_id(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert result["workflow_id"] == wf.id

    def test_compare_executions_list(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert len(result["executions"]) == 2


class TestComparisonAPI:
    def test_compare_endpoint(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        ex1 = client.post(f"/api/workflows/{wf_id}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf_id}/execute").json()
        resp = client.get("/api/tasks/executions/compare", params={"ids": f"{ex1['id']},{ex2['id']}"})
        assert resp.status_code == 200
        assert "task_comparison" in resp.json()

    def test_compare_different_workflows_400(self, client):
        r1 = client.post("/api/workflows/", json={
            "name": "WF1",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        r2 = client.post("/api/workflows/", json={
            "name": "WF2",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        ex1 = client.post(f"/api/workflows/{r1.json()['id']}/execute").json()
        ex2 = client.post(f"/api/workflows/{r2.json()['id']}/execute").json()
        resp = client.get("/api/tasks/executions/compare", params={"ids": f"{ex1['id']},{ex2['id']}"})
        assert resp.status_code == 400

    def test_compare_not_found(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "a,b"})
        assert resp.status_code == 404

    def test_compare_wrong_count(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "a"})
        assert resp.status_code == 400


# ===========================================================================
# Topological sort edge cases
# ===========================================================================


class TestTopologicalSort:
    def test_single_task(self):
        tasks = [TaskDefinition(id="a", name="A", action="log")]
        result = _topological_sort(tasks)
        assert len(result) == 1
        assert result[0].id == "a"

    def test_linear_chain(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log"),
            TaskDefinition(id="b", name="B", action="log", depends_on=["a"]),
            TaskDefinition(id="c", name="C", action="log", depends_on=["b"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index("a") < ids.index("b") < ids.index("c")

    def test_fan_out(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log"),
            TaskDefinition(id="b", name="B", action="log", depends_on=["a"]),
            TaskDefinition(id="c", name="C", action="log", depends_on=["a"]),
            TaskDefinition(id="d", name="D", action="log", depends_on=["a"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids[0] == "a"

    def test_fan_in(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log"),
            TaskDefinition(id="b", name="B", action="log"),
            TaskDefinition(id="c", name="C", action="log"),
            TaskDefinition(id="d", name="D", action="log", depends_on=["a", "b", "c"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index("d") > ids.index("a")
        assert ids.index("d") > ids.index("b")
        assert ids.index("d") > ids.index("c")

    def test_diamond(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log"),
            TaskDefinition(id="b", name="B", action="log", depends_on=["a"]),
            TaskDefinition(id="c", name="C", action="log", depends_on=["a"]),
            TaskDefinition(id="d", name="D", action="log", depends_on=["b", "c"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids[0] == "a"
        assert ids[-1] == "d"

    def test_disconnected_components(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log"),
            TaskDefinition(id="b", name="B", action="log", depends_on=["a"]),
            TaskDefinition(id="c", name="C", action="log"),
            TaskDefinition(id="d", name="D", action="log", depends_on=["c"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index("a") < ids.index("b")
        assert ids.index("c") < ids.index("d")
        assert len(result) == 4

    def test_nonexistent_dependency_ignored(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log", depends_on=["nonexistent"]),
        ]
        result = _topological_sort(tasks)
        assert len(result) == 1

    def test_empty_tasks(self):
        result = _topological_sort([])
        assert result == []

    def test_large_dag(self):
        tasks = [TaskDefinition(id=f"t{i}", name=f"T{i}", action="log") for i in range(25)]
        for i in range(1, 25):
            tasks[i].depends_on = [f"t{i-1}"]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        for i in range(24):
            assert ids.index(f"t{i}") < ids.index(f"t{i+1}")

    def test_no_dependencies(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log"),
            TaskDefinition(id="b", name="B", action="log"),
            TaskDefinition(id="c", name="C", action="log"),
        ]
        result = _topological_sort(tasks)
        assert len(result) == 3


# ===========================================================================
# Edge case tests for workflow engine
# ===========================================================================


class TestWorkflowEngineEdgeCases:
    def test_deeply_nested_deps(self):
        tasks = []
        for i in range(5):
            t = {"id": f"t{i}", "name": f"T{i}", "action": "log", "parameters": {"message": "ok"}}
            if i > 0:
                t["depends_on"] = [f"t{i-1}"]
            tasks.append(t)
        wf = create_workflow(WorkflowCreate(name="Deep", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert len(ex.task_results) == 5

    def test_diamond_deps_execution(self):
        wf = create_workflow(WorkflowCreate(
            name="Diamond",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {"message": "a"}},
                {"id": "b", "name": "B", "action": "log", "parameters": {"message": "b"}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {"message": "c"}, "depends_on": ["a"]},
                {"id": "d", "name": "D", "action": "log", "parameters": {"message": "d"}, "depends_on": ["b", "c"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert len(ex.task_results) == 4

    def test_update_deleted_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Delete Me"))
        delete_workflow(wf.id)
        result = update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        assert result is None

    def test_execute_same_workflow_twice(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        assert ex1.id != ex2.id
        assert ex1.status == WorkflowStatus.COMPLETED
        assert ex2.status == WorkflowStatus.COMPLETED

    def test_pagination_offset_beyond_total(self):
        for i in range(5):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        results = list_workflows(offset=100)
        assert results == []

    def test_get_nonexistent_execution(self):
        assert get_execution("nonexistent") is None

    def test_list_executions_combined_filters(self):
        wf1 = create_workflow(WorkflowCreate(
            name="WF1",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        wf2 = create_workflow(WorkflowCreate(
            name="WF2",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))
        execute_workflow(wf1.id)
        execute_workflow(wf2.id)

        results = list_executions(workflow_id=wf1.id, status=WorkflowStatus.COMPLETED)
        assert len(results) == 1
        results = list_executions(workflow_id=wf2.id, status=WorkflowStatus.COMPLETED)
        assert len(results) == 0

    def test_empty_workflow_execution(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert ex.task_results == []

    def test_list_workflows_default_limit(self):
        for i in range(60):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        results = list_workflows()
        assert len(results) == 50

    def test_list_executions_default_limit(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        for _ in range(60):
            execute_workflow(wf.id)
        results = list_executions()
        assert len(results) == 50


# ===========================================================================
# Formatters
# ===========================================================================


class TestFormatters:
    def test_format_duration_ms(self):
        from app.utils.formatters import format_duration
        assert format_duration(500) == "500ms"

    def test_format_duration_seconds(self):
        from app.utils.formatters import format_duration
        assert format_duration(5000) == "5.0s"

    def test_format_duration_minutes(self):
        from app.utils.formatters import format_duration
        assert format_duration(120000) == "2.0m"

    def test_format_duration_hours(self):
        from app.utils.formatters import format_duration
        assert format_duration(7200000) == "2.0h"

    def test_format_timestamp_none(self):
        from app.utils.formatters import format_timestamp
        assert format_timestamp(None) == "—"

    def test_format_timestamp_datetime(self):
        from datetime import datetime
        from app.utils.formatters import format_timestamp
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert "2026-01-15" in format_timestamp(dt)

    def test_format_task_summary(self):
        from app.utils.formatters import format_task_summary
        result = format_task_summary({"task_id": "t1", "status": "completed", "duration_ms": 100})
        assert "t1" in result
        assert "completed" in result

    def test_format_task_summary_with_error(self):
        from app.utils.formatters import format_task_summary
        result = format_task_summary({"task_id": "t1", "status": "failed", "error": "boom"})
        assert "boom" in result

    def test_format_execution_report(self):
        from app.utils.formatters import format_execution_report
        report = format_execution_report({
            "id": "ex-1",
            "status": "completed",
            "trigger": "manual",
            "task_results": [{"task_id": "t1", "status": "completed"}],
        })
        assert "ex-1" in report
        assert "completed" in report

    def test_format_workflow_tree(self):
        from app.utils.formatters import format_workflow_tree
        tasks = [
            {"id": "a", "name": "A", "action": "log", "depends_on": []},
            {"id": "b", "name": "B", "action": "validate", "depends_on": ["a"]},
        ]
        tree = format_workflow_tree(tasks)
        assert "A" in tree
        assert "B" in tree

    def test_format_workflow_tree_empty(self):
        from app.utils.formatters import format_workflow_tree
        assert format_workflow_tree([]) == ""

    def test_format_duration_zero(self):
        from app.utils.formatters import format_duration
        assert format_duration(0) == "0ms"

    def test_format_task_summary_minimal(self):
        from app.utils.formatters import format_task_summary
        result = format_task_summary({})
        assert "unknown" in result
