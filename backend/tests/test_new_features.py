"""Tests for new backend features: versioning, cloning, dry-run,
comparison, search, and tag management.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowStatus, WorkflowUpdate
from app.services.workflow_engine import (
    _executions,
    add_tags,
    clear_all,
    clone_workflow,
    compare_executions,
    create_workflow,
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


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    return TestClient(app)


# ===========================================================================
# Versioning
# ===========================================================================


class TestVersioning:
    def test_new_workflow_has_version_1(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        assert wf.version == 1

    def test_update_increments_version(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        updated = update_workflow(wf.id, WorkflowUpdate(name="V2"))
        assert updated.version == 2

    def test_multiple_updates_increment(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        for i in range(5):
            update_workflow(wf.id, WorkflowUpdate(name=f"V{i+2}"))
        assert get_workflow(wf.id).version == 6

    def test_history_empty_for_new_workflow(self):
        wf = create_workflow(WorkflowCreate(name="New"))
        history = get_workflow_history(wf.id)
        assert history == []

    def test_history_after_update(self):
        wf = create_workflow(WorkflowCreate(name="Original"))
        update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        history = get_workflow_history(wf.id)
        assert len(history) == 1
        assert history[0]["name"] == "Original"
        assert history[0]["version"] == 1

    def test_history_order_newest_first(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        update_workflow(wf.id, WorkflowUpdate(name="V3"))
        history = get_workflow_history(wf.id)
        assert len(history) == 2
        assert history[0]["version"] == 2
        assert history[1]["version"] == 1

    def test_get_specific_version(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        snap = get_workflow_version(wf.id, 1)
        assert snap is not None
        assert snap["name"] == "V1"

    def test_get_nonexistent_version(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        assert get_workflow_version(wf.id, 99) is None

    def test_history_not_found_workflow(self):
        assert get_workflow_history("nonexistent") is None

    def test_version_snapshot_independent(self):
        wf = create_workflow(WorkflowCreate(name="V1", tags=["a"]))
        update_workflow(wf.id, WorkflowUpdate(name="V2", tags=["b"]))
        snap = get_workflow_version(wf.id, 1)
        assert snap["tags"] == ["a"]
        current = get_workflow(wf.id)
        assert current.tags == ["b"]

    def test_version_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V3"})

        history = client.get(f"/api/workflows/{wf_id}/history").json()
        assert len(history) == 2

        snap = client.get(f"/api/workflows/{wf_id}/history/1").json()
        assert snap["name"] == "V1"

    def test_version_not_found_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        resp = client.get(f"/api/workflows/{wf_id}/history/99")
        assert resp.status_code == 404

    def test_history_not_found_workflow_via_api(self, client):
        resp = client.get("/api/workflows/nonexistent/history")
        assert resp.status_code == 404


# ===========================================================================
# Cloning
# ===========================================================================


class TestCloning:
    def test_clone_success(self):
        wf = create_workflow(WorkflowCreate(
            name="Original",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
            tags=["prod"],
        ))
        cloned = clone_workflow(wf.id)
        assert cloned is not None
        assert cloned.id != wf.id
        assert cloned.name == "Original (copy)"
        assert cloned.tags == ["prod"]
        assert len(cloned.tasks) == 1

    def test_clone_not_found(self):
        assert clone_workflow("nonexistent") is None

    def test_clone_deep_independence(self):
        wf = create_workflow(WorkflowCreate(
            name="Original",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        cloned = clone_workflow(wf.id)
        cloned.tasks[0].name = "Modified"
        assert wf.tasks[0].name == "S"

    def test_clone_with_dependencies(self):
        wf = create_workflow(WorkflowCreate(
            name="Dep WF",
            tasks=[
                {"id": "A", "name": "A", "action": "log", "parameters": {}},
                {"id": "B", "name": "B", "action": "log", "parameters": {}, "depends_on": ["A"]},
            ],
        ))
        cloned = clone_workflow(wf.id)
        assert len(cloned.tasks) == 2
        b_task = next(t for t in cloned.tasks if t.name == "B")
        assert "A" in b_task.depends_on

    def test_clone_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "Original"})
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        assert clone_resp.status_code == 201
        assert clone_resp.json()["name"] == "Original (copy)"
        assert clone_resp.json()["id"] != wf_id

    def test_clone_not_found_via_api(self, client):
        resp = client.post("/api/workflows/nonexistent/clone")
        assert resp.status_code == 404

    def test_clone_appears_in_list(self):
        wf = create_workflow(WorkflowCreate(name="Original"))
        clone_workflow(wf.id)
        all_wfs = list_workflows(limit=100)
        assert len(all_wfs) == 2

    def test_clone_has_version_1(self):
        wf = create_workflow(WorkflowCreate(name="Original"))
        update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        cloned = clone_workflow(wf.id)
        assert cloned.version == 1

    def test_clone_preserves_description(self):
        wf = create_workflow(WorkflowCreate(name="WF", description="A description"))
        cloned = clone_workflow(wf.id)
        assert cloned.description == "A description"

    def test_clone_can_be_executed(self):
        wf = create_workflow(WorkflowCreate(
            name="Exec WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        cloned = clone_workflow(wf.id)
        ex = execute_workflow(cloned.id)
        assert ex.status == WorkflowStatus.COMPLETED


# ===========================================================================
# Dry-run
# ===========================================================================


class TestDryRun:
    def test_basic_dry_run(self):
        wf = create_workflow(WorkflowCreate(
            name="DR",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result is not None
        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.task_results) == 1
        assert result.task_results[0].output == {"dry_run": True}

    def test_dry_run_with_dependencies(self):
        wf = create_workflow(WorkflowCreate(
            name="DR Deps",
            tasks=[
                {"id": "A", "name": "A", "action": "log", "parameters": {}},
                {"id": "B", "name": "B", "action": "log", "parameters": {}, "depends_on": ["A"]},
                {"id": "C", "name": "C", "action": "log", "parameters": {}, "depends_on": ["B"]},
            ],
        ))
        result = dry_run_workflow(wf.id)
        ids = [tr.task_id for tr in result.task_results]
        assert ids == ["A", "B", "C"]

    def test_dry_run_unknown_action_succeeds(self):
        wf = create_workflow(WorkflowCreate(
            name="DR Unknown",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED

    def test_dry_run_not_found(self):
        assert dry_run_workflow("nonexistent") is None

    def test_dry_run_not_stored(self):
        wf = create_workflow(WorkflowCreate(
            name="DR",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert get_execution(result.id) is None

    def test_dry_run_trigger_is_dry_run(self):
        wf = create_workflow(WorkflowCreate(name="DR", tasks=[]))
        result = dry_run_workflow(wf.id)
        assert result.trigger == "dry_run"

    def test_dry_run_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.task_results == []

    def test_dry_run_via_api(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "DR API",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        dr_resp = client.post(f"/api/workflows/{wf_id}/dry-run")
        assert dr_resp.status_code == 200
        assert dr_resp.json()["status"] == "completed"
        assert dr_resp.json()["task_results"][0]["output"]["dry_run"] is True

    def test_dry_run_not_found_via_api(self, client):
        resp = client.post("/api/workflows/nonexistent/dry-run")
        assert resp.status_code == 404

    def test_dry_run_does_not_appear_in_executions(self):
        wf = create_workflow(WorkflowCreate(
            name="DR",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        dry_run_workflow(wf.id)
        execs = list_executions(workflow_id=wf.id)
        assert len(execs) == 0


# ===========================================================================
# Comparison
# ===========================================================================


class TestComparison:
    def test_compare_same_workflow(self):
        wf = create_workflow(WorkflowCreate(
            name="Cmp",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert result is not None
        assert result["workflow_id"] == wf.id
        assert len(result["executions"]) == 2
        assert result["summary"]["unchanged_count"] == 1

    def test_compare_different_workflows_raises(self):
        wf1 = create_workflow(WorkflowCreate(
            name="WF1",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        wf2 = create_workflow(WorkflowCreate(
            name="WF2",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        ex1 = execute_workflow(wf1.id)
        ex2 = execute_workflow(wf2.id)
        with pytest.raises(ValueError, match="different workflows"):
            compare_executions(ex1.id, ex2.id)

    def test_compare_not_found(self):
        assert compare_executions("a", "b") is None

    def test_compare_improved_count(self):
        from app.services.workflow_engine import LogOutput
        wf = create_workflow(WorkflowCreate(
            name="Cmp",
            tasks=[
                {"name": "Good", "action": "log", "parameters": {"message": "ok"}},
                {"name": "Bad", "action": "unknown_action", "parameters": {}},
            ],
        ))
        ex1 = execute_workflow(wf.id)
        assert ex1.status == WorkflowStatus.FAILED

        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda a, p: LogOutput(message="ok"),
        ):
            ex2 = execute_workflow(wf.id)
        assert ex2.status == WorkflowStatus.COMPLETED

        result = compare_executions(ex1.id, ex2.id)
        assert result["summary"]["improved_count"] >= 1

    def test_compare_via_api(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Cmp API",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        ex1 = client.post(f"/api/workflows/{wf_id}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf_id}/execute").json()

        cmp_resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": f"{ex1['id']},{ex2['id']}"},
        )
        assert cmp_resp.status_code == 200
        assert cmp_resp.json()["workflow_id"] == wf_id

    def test_compare_different_workflows_via_api(self, client):
        wf1 = client.post("/api/workflows/", json={
            "name": "A", "tasks": [{"name": "S", "action": "log", "parameters": {}}],
        }).json()["id"]
        wf2 = client.post("/api/workflows/", json={
            "name": "B", "tasks": [{"name": "S", "action": "log", "parameters": {}}],
        }).json()["id"]
        ex1 = client.post(f"/api/workflows/{wf1}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf2}/execute").json()

        resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": f"{ex1['id']},{ex2['id']}"},
        )
        assert resp.status_code == 400

    def test_compare_wrong_number_of_ids(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "only-one"})
        assert resp.status_code == 400

    def test_compare_not_found_via_api(self, client):
        resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": "a,b"},
        )
        assert resp.status_code == 404

    def test_compare_task_comparison_structure(self):
        wf = create_workflow(WorkflowCreate(
            name="Cmp",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        tc = result["task_comparison"]
        assert len(tc) == 1
        assert "task_id" in tc[0]
        assert "status_a" in tc[0]
        assert "status_b" in tc[0]

    def test_compare_duration_diff(self):
        wf = create_workflow(WorkflowCreate(
            name="Cmp",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        tc = result["task_comparison"]
        assert tc[0]["duration_diff_ms"] is not None


# ===========================================================================
# Search
# ===========================================================================


class TestSearch:
    def test_search_empty_results(self):
        create_workflow(WorkflowCreate(name="Alpha"))
        results = search_workflows("zzz")
        assert results == []

    def test_search_partial_match(self):
        create_workflow(WorkflowCreate(name="Data Pipeline"))
        results = search_workflows("pipe")
        assert len(results) == 1

    def test_search_case_insensitive(self):
        create_workflow(WorkflowCreate(name="MyWorkflow"))
        assert len(search_workflows("myworkflow")) == 1
        assert len(search_workflows("MYWORKFLOW")) == 1

    def test_search_combined_with_tag(self):
        create_workflow(WorkflowCreate(name="Alpha", tags=["prod"]))
        create_workflow(WorkflowCreate(name="Alpha Beta", tags=["dev"]))
        results = search_workflows("Alpha", tag="prod")
        assert len(results) == 1
        assert results[0].tags == ["prod"]

    def test_search_with_pagination(self):
        for i in range(10):
            create_workflow(WorkflowCreate(name=f"Pipeline {i}"))
        page1 = search_workflows("Pipeline", limit=3, offset=0)
        page2 = search_workflows("Pipeline", limit=3, offset=3)
        assert len(page1) == 3
        assert len(page2) == 3
        ids1 = {w.id for w in page1}
        ids2 = {w.id for w in page2}
        assert ids1.isdisjoint(ids2)

    def test_search_special_characters(self):
        create_workflow(WorkflowCreate(name="WF (v2.0)"))
        results = search_workflows("(v2")
        assert len(results) == 1

    def test_search_via_api(self, client):
        client.post("/api/workflows/", json={"name": "Alpha Pipeline"})
        client.post("/api/workflows/", json={"name": "Beta Pipeline"})
        client.post("/api/workflows/", json={"name": "Gamma"})

        resp = client.get("/api/workflows/", params={"search": "pipeline"})
        assert len(resp.json()) == 2

    def test_search_via_api_with_tag(self, client):
        client.post("/api/workflows/", json={"name": "Alpha", "tags": ["prod"]})
        client.post("/api/workflows/", json={"name": "Alpha Beta", "tags": ["dev"]})

        resp = client.get("/api/workflows/", params={"search": "alpha", "tag": "prod"})
        assert len(resp.json()) == 1

    def test_search_empty_query_returns_all(self):
        create_workflow(WorkflowCreate(name="A"))
        create_workflow(WorkflowCreate(name="B"))
        results = search_workflows("")
        assert len(results) == 2

    def test_list_workflows_search_param(self):
        create_workflow(WorkflowCreate(name="Findme"))
        create_workflow(WorkflowCreate(name="Other"))
        results = list_workflows(search="findme")
        assert len(results) == 1


# ===========================================================================
# Tag management
# ===========================================================================


class TestTagManagement:
    def test_add_single_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        result = add_tags(wf.id, ["new-tag"])
        assert "new-tag" in result.tags

    def test_add_multiple_tags(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        result = add_tags(wf.id, ["a", "b", "c"])
        assert set(result.tags) == {"a", "b", "c"}

    def test_add_duplicate_tag_idempotent(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["existing"]))
        result = add_tags(wf.id, ["existing"])
        assert result.tags.count("existing") == 1

    def test_remove_existing_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["a", "b"]))
        result = remove_tag(wf.id, "a")
        assert result is True
        assert "a" not in get_workflow(wf.id).tags

    def test_remove_nonexistent_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["a"]))
        result = remove_tag(wf.id, "nonexistent")
        assert result is False

    def test_add_tags_workflow_not_found(self):
        assert add_tags("nonexistent", ["tag"]) is None

    def test_remove_tag_workflow_not_found(self):
        assert remove_tag("nonexistent", "tag") is None

    def test_tag_filter_reflects_changes(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        add_tags(wf.id, ["new-tag"])
        results = list_workflows(tag="new-tag")
        assert len(results) == 1

    def test_add_tags_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        tag_resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["a", "b"]})
        assert tag_resp.status_code == 200
        assert "a" in tag_resp.json()["tags"]

    def test_remove_tag_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF", "tags": ["a", "b"]})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/a")
        assert del_resp.status_code == 200
        assert "a" not in del_resp.json()["tags"]

    def test_remove_nonexistent_tag_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/nonexistent")
        assert del_resp.status_code == 404

    def test_add_tags_not_found_via_api(self, client):
        resp = client.post("/api/workflows/nonexistent/tags", json={"tags": ["a"]})
        assert resp.status_code == 404

    def test_remove_tag_not_found_workflow_via_api(self, client):
        resp = client.delete("/api/workflows/nonexistent/tags/a")
        assert resp.status_code == 404


# ===========================================================================
# Edge case tests for workflow engine (Task H)
# ===========================================================================


class TestWorkflowEngineEdgeCases:
    def test_deeply_nested_dependencies(self):
        tasks = []
        for i in range(5):
            tid = chr(65 + i)
            deps = [chr(64 + i)] if i > 0 else []
            tasks.append({"id": tid, "name": tid, "action": "log", "parameters": {"message": tid}, "depends_on": deps})
        wf = create_workflow(WorkflowCreate(name="Deep", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        ids = [tr.task_id for tr in ex.task_results]
        assert ids == ["A", "B", "C", "D", "E"]

    def test_diamond_dependencies_execution(self):
        wf = create_workflow(WorkflowCreate(
            name="Diamond",
            tasks=[
                {"id": "A", "name": "A", "action": "log", "parameters": {}},
                {"id": "B", "name": "B", "action": "log", "parameters": {}, "depends_on": ["A"]},
                {"id": "C", "name": "C", "action": "log", "parameters": {}, "depends_on": ["A"]},
                {"id": "D", "name": "D", "action": "log", "parameters": {}, "depends_on": ["B", "C"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        ids = [tr.task_id for tr in ex.task_results]
        assert ids[0] == "A" and ids[-1] == "D"

    def test_update_deleted_workflow(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        from app.services.workflow_engine import delete_workflow
        delete_workflow(wf.id)
        result = update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        assert result is None

    def test_execute_same_workflow_twice_independent(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        assert ex1.id != ex2.id
        assert ex1.status == ex2.status == WorkflowStatus.COMPLETED

    def test_pagination_offset_beyond_total(self):
        create_workflow(WorkflowCreate(name="WF"))
        results = list_workflows(offset=100)
        assert results == []

    def test_get_execution_nonexistent(self):
        assert get_execution("nonexistent") is None

    def test_list_executions_all_filter_combinations(self):
        wf_good = create_workflow(WorkflowCreate(
            name="Good",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        wf_bad = create_workflow(WorkflowCreate(
            name="Bad",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))
        execute_workflow(wf_good.id)
        execute_workflow(wf_bad.id)

        assert len(list_executions()) == 2
        assert len(list_executions(workflow_id=wf_good.id)) == 1
        assert len(list_executions(status=WorkflowStatus.COMPLETED)) == 1
        assert len(list_executions(status=WorkflowStatus.FAILED)) == 1
        assert len(list_executions(workflow_id=wf_good.id, status=WorkflowStatus.COMPLETED)) == 1
        assert len(list_executions(workflow_id=wf_good.id, status=WorkflowStatus.FAILED)) == 0

    def test_empty_workflow_execution(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert ex.task_results == []

    def test_execution_has_timestamps(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex = execute_workflow(wf.id)
        assert ex.started_at is not None
        assert ex.completed_at is not None

    def test_execution_task_results_have_timing(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex = execute_workflow(wf.id)
        tr = ex.task_results[0]
        assert tr.duration_ms is not None
        assert tr.duration_ms >= 0
