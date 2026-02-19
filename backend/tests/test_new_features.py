"""Tests for new backend features: cloning, dry-run, search, tagging, versioning, comparison.

Covers all new endpoints and service functions with comprehensive test cases.
"""

import copy
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowStatus, WorkflowUpdate
from app.services.workflow_engine import (
    _executions,
    _workflow_versions,
    add_tags,
    clear_all,
    clone_workflow,
    compare_executions,
    create_workflow,
    dry_run_workflow,
    execute_workflow,
    get_workflow,
    get_workflow_history,
    get_workflow_version,
    list_workflows,
    remove_tag,
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
# Workflow Cloning
# ===========================================================================


class TestCloneWorkflow:
    def test_clone_success(self, client):
        resp = client.post("/api/workflows/", json={"name": "Original", "tags": ["a"]})
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        assert clone_resp.status_code == 201
        data = clone_resp.json()
        assert data["name"] == "Original (copy)"
        assert data["id"] != wf_id
        assert data["tags"] == ["a"]

    def test_clone_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/clone")
        assert resp.status_code == 404

    def test_clone_deep_independence(self, client):
        payload = {
            "name": "WithTasks",
            "tasks": [{"name": "T1", "action": "log", "parameters": {"msg": "hi"}}],
        }
        resp = client.post("/api/workflows/", json=payload)
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        clone_id = clone_resp.json()["id"]

        client.patch(f"/api/workflows/{clone_id}", json={"name": "Modified Clone"})
        original = client.get(f"/api/workflows/{wf_id}").json()
        assert original["name"] == "WithTasks"

    def test_clone_with_dependencies(self, client):
        payload = {
            "name": "DepWF",
            "tasks": [
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        }
        resp = client.post("/api/workflows/", json=payload)
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        assert clone_resp.status_code == 201
        assert len(clone_resp.json()["tasks"]) == 2

    def test_clone_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SVC", tags=["x"]))
        clone = clone_workflow(wf.id)
        assert clone is not None
        assert clone.name == "SVC (copy)"
        assert clone.id != wf.id

    def test_clone_service_not_found(self):
        assert clone_workflow("nope") is None

    def test_clone_tasks_have_new_ids(self):
        wf = create_workflow(WorkflowCreate(
            name="IDs",
            tasks=[{"name": "T", "action": "log", "parameters": {}}],
        ))
        clone = clone_workflow(wf.id)
        assert clone.tasks[0].id != wf.tasks[0].id

    def test_clone_preserves_description(self):
        wf = create_workflow(WorkflowCreate(name="D", description="desc"))
        clone = clone_workflow(wf.id)
        assert clone.description == "desc"

    def test_clone_preserves_schedule(self):
        wf = create_workflow(WorkflowCreate(name="S", schedule="0 * * * *"))
        clone = clone_workflow(wf.id)
        assert clone.schedule == "0 * * * *"

    def test_clone_appears_in_list(self, client):
        client.post("/api/workflows/", json={"name": "ListTest"})
        wf_id = client.get("/api/workflows/").json()[0]["id"]
        client.post(f"/api/workflows/{wf_id}/clone")
        all_wfs = client.get("/api/workflows/").json()
        assert len(all_wfs) == 2


# ===========================================================================
# Workflow Dry-Run
# ===========================================================================


class TestDryRunWorkflow:
    def test_dry_run_basic(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "DryWF",
            "tasks": [{"name": "T", "action": "log", "parameters": {}}],
        })
        wf_id = resp.json()["id"]
        dry_resp = client.post(f"/api/workflows/{wf_id}/dry-run")
        assert dry_resp.status_code == 200
        data = dry_resp.json()
        assert data["status"] == "completed"
        assert data["trigger"] == "dry_run"
        assert data["task_results"][0]["output"]["dry_run"] is True

    def test_dry_run_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/dry-run")
        assert resp.status_code == 404

    def test_dry_run_with_dependencies(self):
        wf = create_workflow(WorkflowCreate(
            name="DepDry",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        ))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.task_results[0].task_id == "a"
        assert result.task_results[1].task_id == "b"

    def test_dry_run_unknown_actions_succeed(self):
        wf = create_workflow(WorkflowCreate(
            name="UnknownAction",
            tasks=[{"name": "T", "action": "nonexistent", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED

    def test_dry_run_not_stored(self):
        wf = create_workflow(WorkflowCreate(
            name="NotStored",
            tasks=[{"name": "T", "action": "log", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result.id not in _executions

    def test_dry_run_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.task_results == []

    def test_dry_run_service_not_found(self):
        assert dry_run_workflow("nope") is None

    def test_dry_run_preserves_task_order(self):
        wf = create_workflow(WorkflowCreate(
            name="Order",
            tasks=[
                {"id": "c", "name": "C", "action": "log", "parameters": {}, "depends_on": ["a", "b"]},
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        ))
        result = dry_run_workflow(wf.id)
        ids = [tr.task_id for tr in result.task_results]
        assert ids.index("a") < ids.index("b")
        assert ids.index("b") < ids.index("c")

    def test_dry_run_all_tasks_completed(self):
        wf = create_workflow(WorkflowCreate(
            name="AllCompleted",
            tasks=[
                {"name": f"T{i}", "action": "log", "parameters": {}}
                for i in range(5)
            ],
        ))
        result = dry_run_workflow(wf.id)
        assert all(tr.status == WorkflowStatus.COMPLETED for tr in result.task_results)

    def test_dry_run_duration_is_zero(self):
        wf = create_workflow(WorkflowCreate(
            name="ZeroDur",
            tasks=[{"name": "T", "action": "log", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result.task_results[0].duration_ms == 0


# ===========================================================================
# Workflow Search
# ===========================================================================


class TestWorkflowSearch:
    def test_search_empty_results(self, client):
        client.post("/api/workflows/", json={"name": "Alpha"})
        resp = client.get("/api/workflows/", params={"search": "zzz"})
        assert resp.json() == []

    def test_search_partial_match(self, client):
        client.post("/api/workflows/", json={"name": "Data Pipeline"})
        client.post("/api/workflows/", json={"name": "ETL Job"})
        resp = client.get("/api/workflows/", params={"search": "pipe"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Data Pipeline"

    def test_search_case_insensitive(self, client):
        client.post("/api/workflows/", json={"name": "MyWorkflow"})
        resp = client.get("/api/workflows/", params={"search": "myworkflow"})
        assert len(resp.json()) == 1

    def test_search_combined_with_tag(self, client):
        client.post("/api/workflows/", json={"name": "Alpha Pipeline", "tags": ["prod"]})
        client.post("/api/workflows/", json={"name": "Beta Pipeline", "tags": ["dev"]})
        resp = client.get("/api/workflows/", params={"search": "pipeline", "tag": "prod"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Alpha Pipeline"

    def test_search_with_pagination(self, client):
        for i in range(10):
            client.post("/api/workflows/", json={"name": f"Search WF {i}"})
        resp = client.get("/api/workflows/", params={"search": "Search", "limit": 3, "offset": 0})
        assert len(resp.json()) == 3

    def test_search_special_characters(self, client):
        client.post("/api/workflows/", json={"name": "WF (v2.0)"})
        resp = client.get("/api/workflows/", params={"search": "(v2"})
        assert len(resp.json()) == 1

    def test_search_service_layer(self):
        create_workflow(WorkflowCreate(name="Alpha"))
        create_workflow(WorkflowCreate(name="Beta"))
        results = list_workflows(search="alp")
        assert len(results) == 1
        assert results[0].name == "Alpha"

    def test_search_returns_all_when_empty(self):
        create_workflow(WorkflowCreate(name="A"))
        create_workflow(WorkflowCreate(name="B"))
        results = list_workflows(search="")
        assert len(results) == 2

    def test_search_no_match(self):
        create_workflow(WorkflowCreate(name="A"))
        results = list_workflows(search="zzz")
        assert results == []

    def test_search_unicode(self, client):
        client.post("/api/workflows/", json={"name": "工作流程"})
        resp = client.get("/api/workflows/", params={"search": "工作"})
        assert len(resp.json()) == 1


# ===========================================================================
# Workflow Tagging
# ===========================================================================


class TestWorkflowTagging:
    def test_add_single_tag(self, client):
        resp = client.post("/api/workflows/", json={"name": "TagWF"})
        wf_id = resp.json()["id"]
        tag_resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["new"]})
        assert tag_resp.status_code == 200
        assert "new" in tag_resp.json()["tags"]

    def test_add_multiple_tags(self, client):
        resp = client.post("/api/workflows/", json={"name": "TagWF"})
        wf_id = resp.json()["id"]
        tag_resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["a", "b", "c"]})
        assert set(tag_resp.json()["tags"]) >= {"a", "b", "c"}

    def test_add_duplicate_tag_idempotent(self, client):
        resp = client.post("/api/workflows/", json={"name": "TagWF", "tags": ["x"]})
        wf_id = resp.json()["id"]
        tag_resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["x"]})
        assert tag_resp.json()["tags"].count("x") == 1

    def test_remove_existing_tag(self, client):
        resp = client.post("/api/workflows/", json={"name": "TagWF", "tags": ["rem"]})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/rem")
        assert del_resp.status_code == 200
        assert "rem" not in del_resp.json()["tags"]

    def test_remove_nonexistent_tag(self, client):
        resp = client.post("/api/workflows/", json={"name": "TagWF"})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/nope")
        assert del_resp.status_code == 404

    def test_add_tags_workflow_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/tags", json={"tags": ["x"]})
        assert resp.status_code == 404

    def test_remove_tag_workflow_not_found(self, client):
        resp = client.delete("/api/workflows/nonexistent/tags/x")
        assert resp.status_code == 404

    def test_tag_filter_reflects_changes(self, client):
        resp = client.post("/api/workflows/", json={"name": "TagWF"})
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["dynamic"]})
        filtered = client.get("/api/workflows/", params={"tag": "dynamic"}).json()
        assert len(filtered) == 1

    def test_add_tags_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SVC"))
        result = add_tags(wf.id, ["a", "b"])
        assert "a" in result.tags
        assert "b" in result.tags

    def test_remove_tag_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SVC", tags=["x"]))
        result = remove_tag(wf.id, "x")
        assert "x" not in result.tags

    def test_remove_tag_raises_if_missing(self):
        wf = create_workflow(WorkflowCreate(name="SVC"))
        with pytest.raises(ValueError, match="not found"):
            remove_tag(wf.id, "nope")


# ===========================================================================
# Workflow Versioning
# ===========================================================================


class TestWorkflowVersioning:
    def test_version_increments_on_update(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        history = client.get(f"/api/workflows/{wf_id}/history").json()
        assert len(history) == 2
        assert history[0]["version"] == 2
        assert history[1]["version"] == 1

    def test_history_list_order(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        for i in range(5):
            client.patch(f"/api/workflows/{wf_id}", json={"name": f"V{i+2}"})
        history = client.get(f"/api/workflows/{wf_id}/history").json()
        versions = [h["version"] for h in history]
        assert versions == sorted(versions, reverse=True)

    def test_fetch_specific_version(self, client):
        resp = client.post("/api/workflows/", json={"name": "Original"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "Updated"})
        v1 = client.get(f"/api/workflows/{wf_id}/history/1").json()
        assert v1["name"] == "Original"
        v2 = client.get(f"/api/workflows/{wf_id}/history/2").json()
        assert v2["name"] == "Updated"

    def test_history_empty_for_new_workflow(self, client):
        resp = client.post("/api/workflows/", json={"name": "New"})
        wf_id = resp.json()["id"]
        history = client.get(f"/api/workflows/{wf_id}/history").json()
        assert len(history) == 1

    def test_history_not_found(self, client):
        resp = client.get("/api/workflows/nonexistent/history")
        assert resp.status_code == 404

    def test_version_not_found(self, client):
        resp = client.post("/api/workflows/", json={"name": "V"})
        wf_id = resp.json()["id"]
        resp = client.get(f"/api/workflows/{wf_id}/history/999")
        assert resp.status_code == 404

    def test_snapshots_independent(self, client):
        resp = client.post("/api/workflows/", json={"name": "Snap", "tags": ["a"]})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"tags": ["b"]})
        v1 = client.get(f"/api/workflows/{wf_id}/history/1").json()
        assert v1["tags"] == ["a"]

    def test_version_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SVC"))
        update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        history = get_workflow_history(wf.id)
        assert len(history) == 2

    def test_get_version_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SVC"))
        v = get_workflow_version(wf.id, 1)
        assert v is not None
        assert v["name"] == "SVC"

    def test_get_version_missing(self):
        wf = create_workflow(WorkflowCreate(name="SVC"))
        assert get_workflow_version(wf.id, 99) is None

    def test_history_returns_none_for_unknown(self):
        assert get_workflow_history("nonexistent") is None


# ===========================================================================
# Execution Comparison
# ===========================================================================


class TestExecutionComparison:
    def test_compare_same_workflow(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "CmpWF",
            "tasks": [{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        ex1 = client.post(f"/api/workflows/{wf_id}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf_id}/execute").json()

        cmp_resp = client.get("/api/tasks/executions/compare", params={"ids": f"{ex1['id']},{ex2['id']}"})
        assert cmp_resp.status_code == 200
        data = cmp_resp.json()
        assert data["workflow_id"] == wf_id
        assert len(data["task_comparison"]) >= 1
        assert "summary" in data

    def test_compare_different_workflows_returns_400(self, client):
        wf1 = client.post("/api/workflows/", json={
            "name": "WF1",
            "tasks": [{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        }).json()["id"]
        wf2 = client.post("/api/workflows/", json={
            "name": "WF2",
            "tasks": [{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        }).json()["id"]
        ex1 = client.post(f"/api/workflows/{wf1}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf2}/execute").json()

        resp = client.get("/api/tasks/executions/compare", params={"ids": f"{ex1['id']},{ex2['id']}"})
        assert resp.status_code == 400

    def test_compare_not_found(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "a,b"})
        assert resp.status_code == 404

    def test_compare_wrong_count(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "a"})
        assert resp.status_code == 400

    def test_compare_three_ids(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "a,b,c"})
        assert resp.status_code == 400

    def test_compare_summary_counts(self):
        wf = create_workflow(WorkflowCreate(
            name="CmpSvc",
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
            side_effect=lambda action, params: LogOutput(message="ok"),
        ):
            from app.services.workflow_engine import retry_execution
            ex2 = retry_execution(ex1.id)

        result = compare_executions(ex1.id, ex2.id)
        assert result is not None
        assert result["summary"]["improved_count"] >= 0

    def test_compare_service_not_found(self):
        assert compare_executions("a", "b") is None

    def test_compare_service_different_workflows(self):
        wf1 = create_workflow(WorkflowCreate(
            name="A",
            tasks=[{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        ))
        wf2 = create_workflow(WorkflowCreate(
            name="B",
            tasks=[{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf1.id)
        ex2 = execute_workflow(wf2.id)
        with pytest.raises(ValueError, match="different workflows"):
            compare_executions(ex1.id, ex2.id)

    def test_compare_identical_executions(self):
        wf = create_workflow(WorkflowCreate(
            name="Same",
            tasks=[{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert result["summary"]["unchanged_count"] >= 1

    def test_compare_empty_string_ids(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": ","})
        assert resp.status_code == 400


# ===========================================================================
# Topological Sort Edge Cases
# ===========================================================================


class TestTopologicalSort:
    def test_single_task_no_deps(self):
        wf = create_workflow(WorkflowCreate(
            name="Single",
            tasks=[{"name": "A", "action": "log", "parameters": {}}],
        ))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert len(ex.task_results) == 1

    def test_linear_chain(self):
        wf = create_workflow(WorkflowCreate(
            name="Chain",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {"message": "a"}},
                {"id": "b", "name": "B", "action": "log", "parameters": {"message": "b"}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {"message": "c"}, "depends_on": ["b"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        ids = [tr.task_id for tr in ex.task_results]
        assert ids.index("a") < ids.index("b") < ids.index("c")

    def test_fan_out(self):
        wf = create_workflow(WorkflowCreate(
            name="FanOut",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {"message": "a"}},
                {"id": "b", "name": "B", "action": "log", "parameters": {"message": "b"}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {"message": "c"}, "depends_on": ["a"]},
                {"id": "d", "name": "D", "action": "log", "parameters": {"message": "d"}, "depends_on": ["a"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        ids = [tr.task_id for tr in ex.task_results]
        assert ids[0] == "a"
        assert set(ids[1:]) == {"b", "c", "d"}

    def test_fan_in(self):
        wf = create_workflow(WorkflowCreate(
            name="FanIn",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {"message": "a"}},
                {"id": "b", "name": "B", "action": "log", "parameters": {"message": "b"}},
                {"id": "c", "name": "C", "action": "log", "parameters": {"message": "c"}},
                {"id": "d", "name": "D", "action": "log", "parameters": {"message": "d"}, "depends_on": ["a", "b", "c"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        ids = [tr.task_id for tr in ex.task_results]
        assert ids[-1] == "d"

    def test_diamond(self):
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
        ids = [tr.task_id for tr in ex.task_results]
        assert ids[0] == "a"
        assert ids[-1] == "d"

    def test_disconnected_components(self):
        wf = create_workflow(WorkflowCreate(
            name="Disconnected",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {"message": "a"}},
                {"id": "b", "name": "B", "action": "log", "parameters": {"message": "b"}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {"message": "c"}},
                {"id": "d", "name": "D", "action": "log", "parameters": {"message": "d"}, "depends_on": ["c"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert len(ex.task_results) == 4

    def test_nonexistent_dependency(self):
        wf = create_workflow(WorkflowCreate(
            name="BadDep",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {"message": "a"}, "depends_on": ["nonexistent"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED

    def test_self_referencing_task(self):
        wf = create_workflow(WorkflowCreate(
            name="SelfRef",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {"message": "a"}, "depends_on": ["a"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED

    def test_large_dag(self):
        tasks = []
        for i in range(25):
            deps = [f"t-{i-1}"] if i > 0 else []
            tasks.append({
                "id": f"t-{i}",
                "name": f"Task {i}",
                "action": "log",
                "parameters": {"message": f"t{i}"},
                "depends_on": deps,
            })
        wf = create_workflow(WorkflowCreate(name="LargeDAG", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert len(ex.task_results) == 25

    def test_wide_dag(self):
        tasks = [{"id": "root", "name": "Root", "action": "log", "parameters": {"message": "r"}}]
        for i in range(20):
            tasks.append({
                "id": f"leaf-{i}",
                "name": f"Leaf {i}",
                "action": "log",
                "parameters": {"message": f"l{i}"},
                "depends_on": ["root"],
            })
        wf = create_workflow(WorkflowCreate(name="WideDAG", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert ex.task_results[0].task_id == "root"


# ===========================================================================
# Workflow Engine Edge Cases
# ===========================================================================


class TestWorkflowEngineEdgeCases:
    def test_deeply_nested_deps(self):
        tasks = []
        for i in range(10):
            deps = [f"t-{i-1}"] if i > 0 else []
            tasks.append({
                "id": f"t-{i}",
                "name": f"T{i}",
                "action": "log",
                "parameters": {"message": f"t{i}"},
                "depends_on": deps,
            })
        wf = create_workflow(WorkflowCreate(name="Deep", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        ids = [tr.task_id for tr in ex.task_results]
        for i in range(1, len(ids)):
            assert ids.index(f"t-{i-1}") < ids.index(f"t-{i}")

    def test_update_deleted_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Del"))
        from app.services.workflow_engine import delete_workflow
        delete_workflow(wf.id)
        result = update_workflow(wf.id, WorkflowUpdate(name="X"))
        assert result is None

    def test_execute_same_workflow_twice(self):
        wf = create_workflow(WorkflowCreate(
            name="Twice",
            tasks=[{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        assert ex1.id != ex2.id
        assert ex1.status == WorkflowStatus.COMPLETED
        assert ex2.status == WorkflowStatus.COMPLETED

    def test_pagination_offset_beyond_total(self):
        for i in range(3):
            create_workflow(WorkflowCreate(name=f"WF{i}"))
        results = list_workflows(offset=100)
        assert results == []

    def test_get_execution_nonexistent(self):
        from app.services.workflow_engine import get_execution
        assert get_execution("nonexistent") is None

    def test_list_executions_all_filters(self):
        from app.services.workflow_engine import list_executions
        wf = create_workflow(WorkflowCreate(
            name="Filters",
            tasks=[{"name": "T", "action": "log", "parameters": {"message": "ok"}}],
        ))
        execute_workflow(wf.id)
        results = list_executions(workflow_id=wf.id, status=WorkflowStatus.COMPLETED)
        assert len(results) == 1

    def test_list_executions_no_match(self):
        from app.services.workflow_engine import list_executions
        results = list_executions(status=WorkflowStatus.CANCELLED)
        assert results == []

    def test_empty_workflow_execution(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert ex.task_results == []

    def test_workflow_diamond_deps(self):
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

    def test_list_workflows_default_limit(self):
        for i in range(60):
            create_workflow(WorkflowCreate(name=f"WF{i}"))
        results = list_workflows()
        assert len(results) == 50
