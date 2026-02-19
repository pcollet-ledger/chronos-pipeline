"""Comprehensive tests for new features: search, dry-run, tagging,
versioning, cloning, comparison, topological sort edge cases, and
workflow engine edge cases.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowStatus, WorkflowUpdate
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
    update_workflow,
)
from app.models import TaskDefinition, WorkflowExecution


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    return TestClient(app)


# ===========================================================================
# Search by name
# ===========================================================================


class TestSearchByName:
    def test_search_empty_results(self, client):
        client.post("/api/workflows/", json={"name": "Alpha"})
        resp = client.get("/api/workflows/", params={"search": "zzz"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_search_partial_match(self, client):
        client.post("/api/workflows/", json={"name": "Data Pipeline"})
        client.post("/api/workflows/", json={"name": "ETL Job"})
        resp = client.get("/api/workflows/", params={"search": "pipe"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Data Pipeline"

    def test_search_case_insensitive(self, client):
        client.post("/api/workflows/", json={"name": "My Workflow"})
        resp = client.get("/api/workflows/", params={"search": "MY WORKFLOW"})
        assert len(resp.json()) == 1

    def test_search_combined_with_tag(self, client):
        client.post("/api/workflows/", json={"name": "Alpha Prod", "tags": ["prod"]})
        client.post("/api/workflows/", json={"name": "Alpha Dev", "tags": ["dev"]})
        client.post("/api/workflows/", json={"name": "Beta Prod", "tags": ["prod"]})
        resp = client.get("/api/workflows/", params={"search": "alpha", "tag": "prod"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Alpha Prod"

    def test_search_with_pagination(self, client):
        for i in range(10):
            client.post("/api/workflows/", json={"name": f"Pipeline {i}"})
        resp = client.get("/api/workflows/", params={"search": "Pipeline", "limit": 3, "offset": 0})
        assert len(resp.json()) == 3
        resp2 = client.get("/api/workflows/", params={"search": "Pipeline", "limit": 3, "offset": 3})
        assert len(resp2.json()) == 3

    def test_search_special_characters(self, client):
        client.post("/api/workflows/", json={"name": "WF (v2.0)"})
        resp = client.get("/api/workflows/", params={"search": "(v2"})
        assert len(resp.json()) == 1

    def test_search_all_match(self, client):
        for i in range(5):
            client.post("/api/workflows/", json={"name": f"Test {i}"})
        resp = client.get("/api/workflows/", params={"search": "Test"})
        assert len(resp.json()) == 5

    def test_search_no_filter_returns_all(self, client):
        client.post("/api/workflows/", json={"name": "A"})
        client.post("/api/workflows/", json={"name": "B"})
        resp = client.get("/api/workflows/")
        assert len(resp.json()) == 2

    def test_search_service_layer(self):
        create_workflow(WorkflowCreate(name="Foo Bar"))
        create_workflow(WorkflowCreate(name="Baz Qux"))
        results = list_workflows(search="foo")
        assert len(results) == 1
        assert results[0].name == "Foo Bar"

    def test_search_unicode(self, client):
        client.post("/api/workflows/", json={"name": "工作流程"})
        resp = client.get("/api/workflows/", params={"search": "工作"})
        assert len(resp.json()) == 1


# ===========================================================================
# Dry-run
# ===========================================================================


class TestDryRun:
    def test_basic_dry_run(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "DryRun WF",
            "tasks": [
                {"name": "Step1", "action": "log", "parameters": {"message": "hi"}},
                {"name": "Step2", "action": "validate", "parameters": {"key": "val"}},
            ],
        }).json()
        resp = client.post(f"/api/workflows/{wf['id']}/dry-run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["task_results"]) == 2
        assert all(tr["output"]["dry_run"] is True for tr in data["task_results"])

    def test_dry_run_with_dependencies(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "Dep DryRun",
            "tasks": [
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {}, "depends_on": ["b"]},
            ],
        }).json()
        resp = client.post(f"/api/workflows/{wf['id']}/dry-run")
        data = resp.json()
        task_ids = [tr["task_id"] for tr in data["task_results"]]
        assert task_ids.index("a") < task_ids.index("b") < task_ids.index("c")

    def test_dry_run_unknown_actions_succeed(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "Unknown Action DryRun",
            "tasks": [{"name": "Bad", "action": "nonexistent", "parameters": {}}],
        }).json()
        resp = client.post(f"/api/workflows/{wf['id']}/dry-run")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_dry_run_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/dry-run")
        assert resp.status_code == 404

    def test_dry_run_not_stored(self, client):
        wf = client.post("/api/workflows/", json={"name": "NoStore"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/dry-run")
        exec_id = resp.json()["id"]
        get_resp = client.get(f"/api/tasks/executions/{exec_id}")
        assert get_resp.status_code == 404

    def test_dry_run_empty_workflow(self, client):
        wf = client.post("/api/workflows/", json={"name": "Empty"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/dry-run")
        assert resp.json()["status"] == "completed"
        assert resp.json()["task_results"] == []

    def test_dry_run_metadata(self, client):
        wf = client.post("/api/workflows/", json={"name": "Meta"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/dry-run")
        assert resp.json()["metadata"]["dry_run"] is True

    def test_dry_run_trigger(self, client):
        wf = client.post("/api/workflows/", json={"name": "Trigger"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/dry-run")
        assert resp.json()["trigger"] == "dry_run"

    def test_dry_run_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SL DryRun"))
        result = dry_run_workflow(wf.id)
        assert result is not None
        assert result.status == WorkflowStatus.COMPLETED

    def test_dry_run_service_not_found(self):
        assert dry_run_workflow("nonexistent") is None


# ===========================================================================
# Tagging operations
# ===========================================================================


class TestTaggingOperations:
    def test_add_single_tag(self, client):
        wf = client.post("/api/workflows/", json={"name": "TagWF"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/tags", json={"tags": ["new-tag"]})
        assert resp.status_code == 200
        assert "new-tag" in resp.json()["tags"]

    def test_add_multiple_tags(self, client):
        wf = client.post("/api/workflows/", json={"name": "TagWF"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/tags", json={"tags": ["a", "b", "c"]})
        assert set(resp.json()["tags"]) == {"a", "b", "c"}

    def test_add_duplicate_tag_idempotent(self, client):
        wf = client.post("/api/workflows/", json={"name": "TagWF", "tags": ["existing"]}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/tags", json={"tags": ["existing"]})
        assert resp.json()["tags"].count("existing") == 1

    def test_remove_existing_tag(self, client):
        wf = client.post("/api/workflows/", json={"name": "TagWF", "tags": ["remove-me"]}).json()
        resp = client.delete(f"/api/workflows/{wf['id']}/tags/remove-me")
        assert resp.status_code == 200
        assert "remove-me" not in resp.json()["tags"]

    def test_remove_nonexistent_tag(self, client):
        wf = client.post("/api/workflows/", json={"name": "TagWF"}).json()
        resp = client.delete(f"/api/workflows/{wf['id']}/tags/nope")
        assert resp.status_code == 409

    def test_tag_workflow_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/tags", json={"tags": ["x"]})
        assert resp.status_code == 404

    def test_remove_tag_workflow_not_found(self, client):
        resp = client.delete("/api/workflows/nonexistent/tags/x")
        assert resp.status_code == 404

    def test_tag_filter_reflects_changes(self, client):
        wf = client.post("/api/workflows/", json={"name": "TagWF"}).json()
        client.post(f"/api/workflows/{wf['id']}/tags", json={"tags": ["filterable"]})
        resp = client.get("/api/workflows/", params={"tag": "filterable"})
        assert len(resp.json()) == 1

    def test_add_tags_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SL"))
        result = add_tags(wf.id, ["x", "y"])
        assert "x" in result.tags
        assert "y" in result.tags

    def test_remove_tag_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SL", tags=["z"]))
        result = remove_tag(wf.id, "z")
        assert "z" not in result.tags

    def test_remove_tag_raises_for_missing(self):
        wf = create_workflow(WorkflowCreate(name="SL"))
        with pytest.raises(ValueError, match="not found"):
            remove_tag(wf.id, "nope")

    def test_add_tags_not_found(self):
        assert add_tags("nonexistent", ["x"]) is None

    def test_remove_tag_not_found(self):
        assert remove_tag("nonexistent", "x") is None


# ===========================================================================
# Versioning
# ===========================================================================


class TestVersioning:
    def test_version_increments_on_update(self, client):
        wf = client.post("/api/workflows/", json={"name": "V1"}).json()
        client.patch(f"/api/workflows/{wf['id']}", json={"name": "V2"})
        client.patch(f"/api/workflows/{wf['id']}", json={"name": "V3"})
        resp = client.get(f"/api/workflows/{wf['id']}/history")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_history_newest_first(self, client):
        wf = client.post("/api/workflows/", json={"name": "First"}).json()
        client.patch(f"/api/workflows/{wf['id']}", json={"name": "Second"})
        client.patch(f"/api/workflows/{wf['id']}", json={"name": "Third"})
        history = client.get(f"/api/workflows/{wf['id']}/history").json()
        assert history[0]["name"] == "Second"
        assert history[1]["name"] == "First"

    def test_fetch_specific_version(self, client):
        wf = client.post("/api/workflows/", json={"name": "Original"}).json()
        client.patch(f"/api/workflows/{wf['id']}", json={"name": "Updated"})
        resp = client.get(f"/api/workflows/{wf['id']}/history/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Original"

    def test_history_empty_for_new_workflow(self, client):
        wf = client.post("/api/workflows/", json={"name": "New"}).json()
        resp = client.get(f"/api/workflows/{wf['id']}/history")
        assert resp.json() == []

    def test_version_not_found(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF"}).json()
        resp = client.get(f"/api/workflows/{wf['id']}/history/99")
        assert resp.status_code == 404

    def test_history_workflow_not_found(self, client):
        resp = client.get("/api/workflows/nonexistent/history")
        assert resp.status_code == 404

    def test_snapshots_independent(self, client):
        wf = client.post("/api/workflows/", json={"name": "Snap", "tags": ["v1"]}).json()
        client.patch(f"/api/workflows/{wf['id']}", json={"tags": ["v2"]})
        v1 = client.get(f"/api/workflows/{wf['id']}/history/1").json()
        current = client.get(f"/api/workflows/{wf['id']}").json()
        assert v1["tags"] == ["v1"]
        assert current["tags"] == ["v2"]

    def test_version_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SL"))
        update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        history = get_workflow_history(wf.id)
        assert len(history) == 1
        assert history[0].name == "SL"

    def test_version_service_not_found(self):
        assert get_workflow_history("nonexistent") is None

    def test_specific_version_service(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        v = get_workflow_version(wf.id, 1)
        assert v is not None
        assert v.name == "V1"

    def test_specific_version_out_of_range(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        assert get_workflow_version(wf.id, 1) is None
        assert get_workflow_version(wf.id, 0) is None


# ===========================================================================
# Cloning
# ===========================================================================


class TestCloning:
    def test_clone_success(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "Original",
            "description": "desc",
            "tags": ["prod"],
            "tasks": [{"name": "Step", "action": "log", "parameters": {"msg": "hi"}}],
        }).json()
        resp = client.post(f"/api/workflows/{wf['id']}/clone")
        assert resp.status_code == 201
        clone = resp.json()
        assert clone["name"] == "Original (copy)"
        assert clone["id"] != wf["id"]
        assert len(clone["tasks"]) == 1

    def test_clone_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/clone")
        assert resp.status_code == 404

    def test_clone_deep_independence(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "Original",
            "tasks": [{"name": "Step", "action": "log", "parameters": {"key": "val"}}],
        }).json()
        clone = client.post(f"/api/workflows/{wf['id']}/clone").json()
        client.patch(f"/api/workflows/{clone['id']}", json={"name": "Modified Clone"})
        original = client.get(f"/api/workflows/{wf['id']}").json()
        assert original["name"] == "Original"

    def test_clone_with_dependencies(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "DepWF",
            "tasks": [
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        }).json()
        clone = client.post(f"/api/workflows/{wf['id']}/clone").json()
        assert len(clone["tasks"]) == 2

    def test_clone_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SL Original"))
        clone = clone_workflow(wf.id)
        assert clone is not None
        assert clone.name == "SL Original (copy)"
        assert clone.id != wf.id

    def test_clone_service_not_found(self):
        assert clone_workflow("nonexistent") is None

    def test_clone_preserves_tags(self):
        wf = create_workflow(WorkflowCreate(name="Tagged", tags=["a", "b"]))
        clone = clone_workflow(wf.id)
        assert clone.tags == ["a", "b"]

    def test_clone_appears_in_list(self, client):
        wf = client.post("/api/workflows/", json={"name": "ListClone"}).json()
        client.post(f"/api/workflows/{wf['id']}/clone")
        all_wfs = client.get("/api/workflows/").json()
        assert len(all_wfs) == 2

    def test_clone_tasks_preserve_ids_for_deps(self):
        """Cloned tasks keep their IDs so depends_on references remain valid."""
        wf = create_workflow(WorkflowCreate(
            name="KeepIDs",
            tasks=[
                {"id": "step-a", "name": "A", "action": "log", "parameters": {}},
                {"id": "step-b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["step-a"]},
            ],
        ))
        clone = clone_workflow(wf.id)
        clone_task_ids = {t.id for t in clone.tasks}
        assert "step-a" in clone_task_ids
        assert "step-b" in clone_task_ids
        dep_task = next(t for t in clone.tasks if t.id == "step-b")
        assert dep_task.depends_on == ["step-a"]

    def test_clone_can_be_executed(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "Exec Clone",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()
        clone = client.post(f"/api/workflows/{wf['id']}/clone").json()
        resp = client.post(f"/api/workflows/{clone['id']}/execute")
        assert resp.json()["status"] == "completed"


# ===========================================================================
# Execution comparison
# ===========================================================================


class TestExecutionComparison:
    def test_compare_same_workflow(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "Compare WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()
        ex1 = client.post(f"/api/workflows/{wf['id']}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf['id']}/execute").json()
        resp = client.get("/api/tasks/executions/compare", params={"ids": f"{ex1['id']},{ex2['id']}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow_id"] == wf["id"]
        assert len(data["executions"]) == 2
        assert len(data["task_comparison"]) >= 1

    def test_compare_different_workflows_returns_400(self, client):
        wf1 = client.post("/api/workflows/", json={
            "name": "WF1",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()
        wf2 = client.post("/api/workflows/", json={
            "name": "WF2",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()
        ex1 = client.post(f"/api/workflows/{wf1['id']}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf2['id']}/execute").json()
        resp = client.get("/api/tasks/executions/compare", params={"ids": f"{ex1['id']},{ex2['id']}"})
        assert resp.status_code == 400

    def test_compare_not_found(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "a,b"})
        assert resp.status_code == 404

    def test_compare_wrong_format(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "only-one"})
        assert resp.status_code == 400

    def test_compare_summary_counts(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "Summary WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()
        ex1 = client.post(f"/api/workflows/{wf['id']}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf['id']}/execute").json()
        resp = client.get("/api/tasks/executions/compare", params={"ids": f"{ex1['id']},{ex2['id']}"})
        summary = resp.json()["summary"]
        assert summary["improved_count"] + summary["regressed_count"] + summary["unchanged_count"] >= 1

    def test_compare_service_layer(self):
        wf = create_workflow(WorkflowCreate(
            name="SL",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert result is not None
        assert result.workflow_id == wf.id

    def test_compare_service_not_found(self):
        assert compare_executions("a", "b") is None

    def test_compare_service_different_workflows(self):
        wf1 = create_workflow(WorkflowCreate(
            name="A", tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        wf2 = create_workflow(WorkflowCreate(
            name="B", tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf1.id)
        ex2 = execute_workflow(wf2.id)
        with pytest.raises(ValueError, match="different workflows"):
            compare_executions(ex1.id, ex2.id)

    def test_compare_improved_count(self):
        wf = create_workflow(WorkflowCreate(
            name="Improve",
            tasks=[
                {"name": "Good", "action": "log", "parameters": {"message": "ok"}},
                {"name": "Bad", "action": "unknown_action", "parameters": {}},
            ],
        ))
        ex_fail = execute_workflow(wf.id)
        from app.services.workflow_engine import LogOutput
        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            from app.services.workflow_engine import retry_execution
            ex_pass = retry_execution(ex_fail.id)
        result = compare_executions(ex_fail.id, ex_pass.id)
        assert result.summary.improved_count >= 1


# ===========================================================================
# Topological sort edge cases
# ===========================================================================


class TestTopologicalSort:
    def test_single_task_no_deps(self):
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
        assert ids.index("a") < ids.index("b")
        assert ids.index("a") < ids.index("c")
        assert ids.index("a") < ids.index("d")

    def test_fan_in(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log"),
            TaskDefinition(id="b", name="B", action="log"),
            TaskDefinition(id="c", name="C", action="log"),
            TaskDefinition(id="d", name="D", action="log", depends_on=["a", "b", "c"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index("a") < ids.index("d")
        assert ids.index("b") < ids.index("d")
        assert ids.index("c") < ids.index("d")

    def test_diamond(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log"),
            TaskDefinition(id="b", name="B", action="log", depends_on=["a"]),
            TaskDefinition(id="c", name="C", action="log", depends_on=["a"]),
            TaskDefinition(id="d", name="D", action="log", depends_on=["b", "c"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index("a") < ids.index("b")
        assert ids.index("a") < ids.index("c")
        assert ids.index("b") < ids.index("d")
        assert ids.index("c") < ids.index("d")

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

    def test_nonexistent_dependency_skipped(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log", depends_on=["nonexistent"]),
        ]
        result = _topological_sort(tasks)
        assert len(result) == 1

    def test_self_referencing_task(self):
        tasks = [
            TaskDefinition(id="a", name="A", action="log", depends_on=["a"]),
        ]
        result = _topological_sort(tasks)
        assert len(result) == 1

    def test_large_dag(self):
        tasks = []
        for i in range(25):
            deps = [f"task-{i-1}"] if i > 0 else []
            tasks.append(TaskDefinition(id=f"task-{i}", name=f"T{i}", action="log", depends_on=deps))
        result = _topological_sort(tasks)
        assert len(result) == 25
        for i in range(1, 25):
            ids = [t.id for t in result]
            assert ids.index(f"task-{i-1}") < ids.index(f"task-{i}")

    def test_empty_task_list(self):
        result = _topological_sort([])
        assert result == []


# ===========================================================================
# Workflow engine edge cases
# ===========================================================================


class TestWorkflowEngineEdgeCases:
    def test_empty_workflow_execution(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert ex.task_results == []

    def test_deeply_nested_dependencies(self):
        tasks = []
        for i in range(5):
            deps = [f"step-{i-1}"] if i > 0 else []
            tasks.append({"id": f"step-{i}", "name": f"S{i}", "action": "log", "parameters": {"message": "ok"}, "depends_on": deps})
        wf = create_workflow(WorkflowCreate(name="Deep", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert len(ex.task_results) == 5

    def test_diamond_dependencies(self):
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
        wf = create_workflow(WorkflowCreate(name="Del"))
        delete_workflow(wf.id)
        result = update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        assert result is None

    def test_execute_same_workflow_twice(self):
        wf = create_workflow(WorkflowCreate(
            name="Twice",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        assert ex1.id != ex2.id
        assert ex1.status == WorkflowStatus.COMPLETED
        assert ex2.status == WorkflowStatus.COMPLETED

    def test_pagination_offset_beyond_total(self):
        for i in range(3):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        results = list_workflows(offset=100)
        assert results == []

    def test_get_execution_nonexistent(self):
        assert get_execution("nonexistent") is None

    def test_list_executions_all_filters(self):
        wf = create_workflow(WorkflowCreate(
            name="Filters",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        execute_workflow(wf.id)
        results = list_executions(workflow_id=wf.id, status=WorkflowStatus.COMPLETED)
        assert len(results) == 1

    def test_list_executions_no_match(self):
        wf = create_workflow(WorkflowCreate(
            name="NoMatch",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        execute_workflow(wf.id)
        results = list_executions(status=WorkflowStatus.FAILED)
        assert len(results) == 0

    def test_delete_nonexistent(self):
        assert delete_workflow("nonexistent") is False


# ===========================================================================
# Formatters tests
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

    def test_format_duration_none(self):
        from app.utils.formatters import format_duration
        assert format_duration(None) == "—"

    def test_format_timestamp(self):
        from app.utils.formatters import format_timestamp
        from datetime import datetime
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert format_timestamp(dt) == "2026-01-15 10:30:00"

    def test_format_timestamp_none(self):
        from app.utils.formatters import format_timestamp
        assert format_timestamp(None) == "—"

    def test_format_task_summary(self):
        from app.utils.formatters import format_task_summary
        result = format_task_summary({"task_id": "abc", "status": "completed", "duration_ms": 150})
        assert "abc" in result
        assert "completed" in result

    def test_format_task_summary_with_error(self):
        from app.utils.formatters import format_task_summary
        result = format_task_summary({"task_id": "x", "status": "failed", "error": "boom"})
        assert "boom" in result

    def test_format_execution_report(self):
        from app.utils.formatters import format_execution_report
        report = format_execution_report({
            "id": "exec-1",
            "workflow_id": "wf-1",
            "status": "completed",
            "trigger": "manual",
            "started_at": "2026-01-15",
            "completed_at": "2026-01-15",
            "task_results": [{"task_id": "t1", "status": "completed", "duration_ms": 10}],
        })
        assert "exec-1" in report
        assert "wf-1" in report

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
