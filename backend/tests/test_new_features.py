"""Comprehensive tests for new backend features.

Covers: search, clone, versioning, tagging, dry-run, comparison,
topological sort edge cases, and workflow engine edge cases.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    TaskDefinition,
    WorkflowCreate,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowUpdate,
)
from app.services.workflow_engine import (
    _executions,
    _topological_sort,
    _workflow_versions,
    add_tags,
    cancel_execution,
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
    retry_execution,
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
# Search
# ===========================================================================


class TestWorkflowSearch:
    def test_search_empty_results(self):
        create_workflow(WorkflowCreate(name="Alpha"))
        results = list_workflows(search="zzz")
        assert results == []

    def test_search_partial_match(self):
        create_workflow(WorkflowCreate(name="Data Pipeline"))
        create_workflow(WorkflowCreate(name="ETL Job"))
        results = list_workflows(search="pipe")
        assert len(results) == 1
        assert results[0].name == "Data Pipeline"

    def test_search_case_insensitive(self):
        create_workflow(WorkflowCreate(name="MyWorkflow"))
        results = list_workflows(search="MYWORK")
        assert len(results) == 1

    def test_search_combined_with_tag(self):
        create_workflow(WorkflowCreate(name="Alpha ETL", tags=["prod"]))
        create_workflow(WorkflowCreate(name="Beta ETL", tags=["dev"]))
        create_workflow(WorkflowCreate(name="Alpha Job", tags=["prod"]))
        results = list_workflows(tag="prod", search="etl")
        assert len(results) == 1
        assert results[0].name == "Alpha ETL"

    def test_search_with_pagination(self):
        for i in range(10):
            create_workflow(WorkflowCreate(name=f"Pipeline-{i}"))
        results = list_workflows(search="Pipeline", limit=3, offset=0)
        assert len(results) == 3
        results2 = list_workflows(search="Pipeline", limit=3, offset=3)
        assert len(results2) == 3

    def test_search_special_characters(self):
        create_workflow(WorkflowCreate(name="WF (v2.0)"))
        results = list_workflows(search="(v2")
        assert len(results) == 1

    def test_search_all_match(self):
        for i in range(5):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        results = list_workflows(search="WF")
        assert len(results) == 5

    def test_search_empty_string_returns_all(self):
        create_workflow(WorkflowCreate(name="A"))
        create_workflow(WorkflowCreate(name="B"))
        results = list_workflows(search="")
        assert len(results) == 2

    def test_search_via_api(self, client):
        client.post("/api/workflows/", json={"name": "Alpha Pipeline"})
        client.post("/api/workflows/", json={"name": "Beta Job"})
        resp = client.get("/api/workflows/", params={"search": "alpha"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Alpha Pipeline"

    def test_search_combined_tag_api(self, client):
        client.post("/api/workflows/", json={"name": "A ETL", "tags": ["prod"]})
        client.post("/api/workflows/", json={"name": "B ETL", "tags": ["dev"]})
        resp = client.get("/api/workflows/", params={"search": "etl", "tag": "prod"})
        assert len(resp.json()) == 1


# ===========================================================================
# Clone
# ===========================================================================


class TestCloneWorkflow:
    def test_clone_success(self):
        wf = create_workflow(WorkflowCreate(
            name="Original",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
            tags=["prod"],
        ))
        clone = clone_workflow(wf.id)
        assert clone is not None
        assert clone.id != wf.id
        assert clone.name == "Original (copy)"
        assert len(clone.tasks) == 1
        assert clone.tags == ["prod"]

    def test_clone_not_found(self):
        assert clone_workflow("nonexistent") is None

    def test_clone_deep_independence(self):
        wf = create_workflow(WorkflowCreate(
            name="Original",
            tasks=[{"name": "S", "action": "log", "parameters": {"key": "val"}}],
        ))
        clone = clone_workflow(wf.id)
        clone.tasks[0].parameters["key"] = "modified"
        original = get_workflow(wf.id)
        assert original.tasks[0].parameters["key"] == "val"

    def test_clone_with_dependencies(self):
        wf = create_workflow(WorkflowCreate(
            name="Dep WF",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        ))
        clone = clone_workflow(wf.id)
        assert len(clone.tasks) == 2
        assert clone.tasks[1].depends_on == ["a"]

    def test_clone_version_resets(self):
        wf = create_workflow(WorkflowCreate(name="V"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        clone = clone_workflow(wf.id)
        assert clone.version == 1

    def test_clone_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "Original"})
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        assert clone_resp.status_code == 201
        assert clone_resp.json()["name"] == "Original (copy)"
        assert clone_resp.json()["id"] != wf_id

    def test_clone_not_found_api(self, client):
        resp = client.post("/api/workflows/nonexistent/clone")
        assert resp.status_code == 404

    def test_clone_appears_in_list(self):
        wf = create_workflow(WorkflowCreate(name="Original"))
        clone_workflow(wf.id)
        all_wfs = list_workflows()
        assert len(all_wfs) == 2

    def test_clone_preserves_description(self):
        wf = create_workflow(WorkflowCreate(name="WF", description="A desc"))
        clone = clone_workflow(wf.id)
        assert clone.description == "A desc"

    def test_clone_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        clone = clone_workflow(wf.id)
        assert clone.tasks == []


# ===========================================================================
# Versioning
# ===========================================================================


class TestVersioning:
    def test_version_starts_at_1(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        assert wf.version == 1

    def test_version_increments_on_update(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        updated = update_workflow(wf.id, WorkflowUpdate(name="V2"))
        assert updated.version == 2
        updated2 = update_workflow(wf.id, WorkflowUpdate(name="V3"))
        assert updated2.version == 3

    def test_history_list_order(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        update_workflow(wf.id, WorkflowUpdate(name="V3"))
        history = get_workflow_history(wf.id)
        assert len(history) == 2
        assert history[0]["version"] == 2
        assert history[1]["version"] == 1

    def test_fetch_specific_version(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        v1 = get_workflow_version(wf.id, 1)
        assert v1 is not None
        assert v1["name"] == "V1"

    def test_history_empty_for_new_workflow(self):
        wf = create_workflow(WorkflowCreate(name="New"))
        history = get_workflow_history(wf.id)
        assert history == []

    def test_not_found_history(self):
        assert get_workflow_history("nonexistent") is None

    def test_not_found_version(self):
        wf = create_workflow(WorkflowCreate(name="V"))
        assert get_workflow_version(wf.id, 99) is None

    def test_version_snapshots_independent(self):
        wf = create_workflow(WorkflowCreate(name="Original", tags=["a"]))
        update_workflow(wf.id, WorkflowUpdate(name="Updated", tags=["b"]))
        v1 = get_workflow_version(wf.id, 1)
        assert v1["name"] == "Original"
        assert v1["tags"] == ["a"]
        current = get_workflow(wf.id)
        assert current.name == "Updated"
        assert current.tags == ["b"]

    def test_version_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        history_resp = client.get(f"/api/workflows/{wf_id}/history")
        assert history_resp.status_code == 200
        assert len(history_resp.json()) == 1
        assert history_resp.json()[0]["name"] == "V1"

    def test_version_specific_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        v_resp = client.get(f"/api/workflows/{wf_id}/history/1")
        assert v_resp.status_code == 200
        assert v_resp.json()["name"] == "V1"

    def test_version_not_found_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        v_resp = client.get(f"/api/workflows/{wf_id}/history/99")
        assert v_resp.status_code == 404

    def test_history_not_found_api(self, client):
        resp = client.get("/api/workflows/nonexistent/history")
        assert resp.status_code == 404


# ===========================================================================
# Tagging
# ===========================================================================


class TestTagging:
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
        updated = get_workflow(wf.id)
        assert "a" not in updated.tags
        assert "b" in updated.tags

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
        assert results[0].id == wf.id

    def test_tag_filter_after_removal(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["old"]))
        remove_tag(wf.id, "old")
        results = list_workflows(tag="old")
        assert len(results) == 0

    def test_add_tags_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        tag_resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["x", "y"]})
        assert tag_resp.status_code == 200
        assert "x" in tag_resp.json()["tags"]
        assert "y" in tag_resp.json()["tags"]

    def test_remove_tag_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF", "tags": ["a", "b"]})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/a")
        assert del_resp.status_code == 200
        assert "a" not in del_resp.json()["tags"]

    def test_remove_nonexistent_tag_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/nope")
        assert del_resp.status_code == 404

    def test_add_tags_not_found_api(self, client):
        resp = client.post("/api/workflows/nonexistent/tags", json={"tags": ["x"]})
        assert resp.status_code == 404


# ===========================================================================
# Dry-run
# ===========================================================================


class TestDryRun:
    def test_basic_dry_run(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result is not None
        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.task_results) == 1
        assert result.task_results[0].output == {"dry_run": True}

    def test_dry_run_with_dependencies(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        ))
        result = dry_run_workflow(wf.id)
        assert result.task_results[0].task_id == "a"
        assert result.task_results[1].task_id == "b"

    def test_dry_run_unknown_actions_succeed(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED

    def test_dry_run_not_found(self):
        assert dry_run_workflow("nonexistent") is None

    def test_dry_run_not_stored(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert get_execution(result.id) is None
        assert len(list_executions()) == 0

    def test_dry_run_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.task_results == []

    def test_dry_run_trigger_is_dry_run(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        result = dry_run_workflow(wf.id)
        assert result.trigger == "dry_run"

    def test_dry_run_via_api(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = resp.json()["id"]
        dr_resp = client.post(f"/api/workflows/{wf_id}/dry-run")
        assert dr_resp.status_code == 200
        assert dr_resp.json()["status"] == "completed"
        assert dr_resp.json()["task_results"][0]["output"]["dry_run"] is True

    def test_dry_run_not_found_api(self, client):
        resp = client.post("/api/workflows/nonexistent/dry-run")
        assert resp.status_code == 404

    def test_dry_run_does_not_affect_analytics(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        dry_run_workflow(wf.id)
        assert len(list_executions()) == 0


# ===========================================================================
# Execution Comparison
# ===========================================================================


class TestExecutionComparison:
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

    def test_compare_improved(self):
        from app.services.workflow_engine import LogOutput
        wf = create_workflow(WorkflowCreate(
            name="WF",
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
            ex2 = retry_execution(ex1.id)

        result = compare_executions(ex1.id, ex2.id)
        assert result["summary"]["improved_count"] >= 1

    def test_compare_via_api(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "WF",
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

    def test_compare_different_workflows_api(self, client):
        wf1 = client.post("/api/workflows/", json={
            "name": "WF1",
            "tasks": [{"name": "S", "action": "log", "parameters": {}}],
        }).json()["id"]
        wf2 = client.post("/api/workflows/", json={
            "name": "WF2",
            "tasks": [{"name": "S", "action": "log", "parameters": {}}],
        }).json()["id"]
        ex1 = client.post(f"/api/workflows/{wf1}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf2}/execute").json()
        resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": f"{ex1['id']},{ex2['id']}"},
        )
        assert resp.status_code == 400

    def test_compare_not_found_api(self, client):
        resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": "a,b"},
        )
        assert resp.status_code == 404

    def test_compare_wrong_count_api(self, client):
        resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": "a"},
        )
        assert resp.status_code == 400

    def test_compare_three_ids_api(self, client):
        resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": "a,b,c"},
        )
        assert resp.status_code == 400

    def test_compare_summary_counts(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        s = result["summary"]
        assert s["improved_count"] + s["regressed_count"] + s["unchanged_count"] == 1


# ===========================================================================
# Topological Sort Edge Cases
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
        assert len(ids) == 4
        assert ids.index("a") < ids.index("b")
        assert ids.index("c") < ids.index("d")

    def test_nonexistent_dependency_ignored(self):
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
# Workflow Engine Edge Cases
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
            tasks.append({"id": f"step-{i}", "name": f"S{i}", "action": "log",
                          "parameters": {"message": "ok"}, "depends_on": deps})
        wf = create_workflow(WorkflowCreate(name="Deep", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert len(ex.task_results) == 5

    def test_diamond_dependency_execution(self):
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
        wf = create_workflow(WorkflowCreate(name="WF"))
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
        assert ex1.status == WorkflowStatus.COMPLETED
        assert ex2.status == WorkflowStatus.COMPLETED

    def test_pagination_offset_beyond_total(self):
        for i in range(3):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        results = list_workflows(offset=100)
        assert results == []

    def test_pagination_limit_larger_than_total(self):
        for i in range(3):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        results = list_workflows(limit=100)
        assert len(results) == 3

    def test_list_executions_all_filters(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        execute_workflow(wf.id)
        results = list_executions(
            workflow_id=wf.id, status=WorkflowStatus.COMPLETED, limit=10
        )
        assert len(results) == 1

    def test_get_execution_nonexistent(self):
        assert get_execution("nonexistent") is None

    def test_list_executions_empty(self):
        assert list_executions() == []

    def test_execute_nonexistent_workflow(self):
        assert execute_workflow("nonexistent") is None


# ===========================================================================
# Formatters
# ===========================================================================


class TestFormatters:
    def test_format_duration(self):
        from app.utils.formatters import format_duration
        assert format_duration(500) == "500ms"
        assert format_duration(5000) == "5.0s"
        assert format_duration(120000) == "2.0m"
        assert format_duration(7200000) == "2.0h"

    def test_format_timestamp(self):
        from app.utils.formatters import format_timestamp
        from datetime import datetime
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert format_timestamp(dt) == "2026-01-15 10:30:00"
        assert format_timestamp(None) == "—"

    def test_format_task_summary(self):
        from app.utils.formatters import format_task_summary
        result = format_task_summary({"task_id": "abc", "status": "completed", "duration_ms": 150})
        assert "abc" in result
        assert "completed" in result
        assert "150ms" in result

    def test_format_task_summary_no_duration(self):
        from app.utils.formatters import format_task_summary
        result = format_task_summary({"task_id": "abc", "status": "failed"})
        assert "abc" in result
        assert "failed" in result

    def test_format_execution_report(self):
        from app.utils.formatters import format_execution_report
        report = format_execution_report({
            "id": "exec-1",
            "status": "completed",
            "trigger": "manual",
            "task_results": [
                {"task_id": "t1", "status": "completed", "duration_ms": 100},
            ],
        })
        assert "exec-1" in report
        assert "completed" in report

    def test_format_workflow_tree(self):
        from app.utils.formatters import format_workflow_tree
        tree = format_workflow_tree({
            "name": "My WF",
            "tasks": [
                {"id": "a", "name": "A", "action": "log", "depends_on": []},
                {"id": "b", "name": "B", "action": "validate", "depends_on": ["a"]},
            ],
        })
        assert "My WF" in tree
        assert "A" in tree
        assert "B" in tree

    def test_format_workflow_tree_empty(self):
        from app.utils.formatters import format_workflow_tree
        tree = format_workflow_tree({"name": "Empty", "tasks": []})
        assert "no tasks" in tree

    def test_format_duration_zero(self):
        from app.utils.formatters import format_duration
        assert format_duration(0) == "0ms"

    def test_format_timestamp_custom_format(self):
        from app.utils.formatters import format_timestamp
        from datetime import datetime
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert format_timestamp(dt, "%Y-%m-%d") == "2026-01-15"

    def test_format_execution_report_empty_tasks(self):
        from app.utils.formatters import format_execution_report
        report = format_execution_report({"id": "x", "status": "completed", "trigger": "manual", "task_results": []})
        assert "Tasks:   0" in report
