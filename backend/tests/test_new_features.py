"""Comprehensive tests for new backend features.

Covers: cloning, tagging, versioning, dry-run, search, execution
comparison, topological sort edge cases, and workflow engine edge cases.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowStatus, WorkflowUpdate
from app.services.analytics_service import clear_cache
from app.services.workflow_engine import (
    LogOutput,
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
        assert clone.tags == ["prod"]

    def test_clone_not_found(self):
        assert clone_workflow("nonexistent") is None

    def test_clone_deep_independence(self):
        wf = create_workflow(WorkflowCreate(
            name="Original",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        clone = clone_workflow(wf.id)
        clone.tasks[0].name = "Modified"
        assert wf.tasks[0].name == "S"

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

    def test_clone_new_task_ids(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        clone = clone_workflow(wf.id)
        assert clone.tasks[0].id != wf.tasks[0].id

    def test_clone_version_reset(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        clone = clone_workflow(wf.id)
        assert clone.version == 1

    def test_clone_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "API Clone"})
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        assert clone_resp.status_code == 201
        assert clone_resp.json()["name"] == "API Clone (copy)"

    def test_clone_not_found_via_api(self, client):
        resp = client.post("/api/workflows/nonexistent/clone")
        assert resp.status_code == 404

    def test_clone_appears_in_list(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        clone_workflow(wf.id)
        assert len(list_workflows()) == 2

    def test_clone_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        clone = clone_workflow(wf.id)
        assert clone.tasks == []


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
        assert "a" not in result.tags
        assert "b" in result.tags

    def test_remove_nonexistent_tag_raises(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["a"]))
        with pytest.raises(ValueError, match="not found"):
            remove_tag(wf.id, "nonexistent")

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
        tag_resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["api-tag"]})
        assert tag_resp.status_code == 200
        assert "api-tag" in tag_resp.json()["tags"]

    def test_remove_tag_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF", "tags": ["removable"]})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/removable")
        assert del_resp.status_code == 200
        assert "removable" not in del_resp.json()["tags"]

    def test_remove_nonexistent_tag_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/nope")
        assert del_resp.status_code == 404


# ===========================================================================
# Versioning
# ===========================================================================


class TestVersioning:
    def test_version_starts_at_1(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        assert wf.version == 1

    def test_version_increments_on_update(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        updated = update_workflow(wf.id, WorkflowUpdate(name="V2"))
        assert updated.version == 2

    def test_multiple_updates_increment(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        updated = update_workflow(wf.id, WorkflowUpdate(name="V3"))
        assert updated.version == 3

    def test_history_empty_for_new_workflow(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        history = get_workflow_history(wf.id)
        assert history == []

    def test_history_after_updates(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        update_workflow(wf.id, WorkflowUpdate(name="V3"))
        history = get_workflow_history(wf.id)
        assert len(history) == 2
        assert history[0].version == 2
        assert history[1].version == 1

    def test_get_specific_version(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        v1 = get_workflow_version(wf.id, 1)
        assert v1 is not None
        assert v1.name == "WF"

    def test_get_current_version(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        v2 = get_workflow_version(wf.id, 2)
        assert v2 is not None
        assert v2.name == "V2"

    def test_get_nonexistent_version(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        assert get_workflow_version(wf.id, 99) is None

    def test_history_not_found(self):
        assert get_workflow_history("nonexistent") is None

    def test_version_snapshots_independent(self):
        wf = create_workflow(WorkflowCreate(name="Original"))
        update_workflow(wf.id, WorkflowUpdate(name="Changed"))
        v1 = get_workflow_version(wf.id, 1)
        assert v1.name == "Original"
        current = get_workflow(wf.id)
        assert current.name == "Changed"

    def test_history_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        hist_resp = client.get(f"/api/workflows/{wf_id}/history")
        assert hist_resp.status_code == 200
        assert len(hist_resp.json()) == 1

    def test_version_via_api(self, client):
        resp = client.post("/api/workflows/", json={"name": "WF"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        ver_resp = client.get(f"/api/workflows/{wf_id}/history/1")
        assert ver_resp.status_code == 200
        assert ver_resp.json()["name"] == "WF"


# ===========================================================================
# Dry-run
# ===========================================================================


class TestDryRun:
    def test_basic_dry_run(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
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

    def test_dry_run_trigger_label(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        result = dry_run_workflow(wf.id)
        assert result.trigger == "dry-run"

    def test_dry_run_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.task_results == []

    def test_dry_run_via_api(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {}}],
        })
        wf_id = resp.json()["id"]
        dr_resp = client.post(f"/api/workflows/{wf_id}/dry-run")
        assert dr_resp.status_code == 200
        assert dr_resp.json()["status"] == "completed"

    def test_dry_run_not_found_via_api(self, client):
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
# Search
# ===========================================================================


class TestSearch:
    def test_search_empty_results(self):
        create_workflow(WorkflowCreate(name="Alpha"))
        results = list_workflows(search="zzz")
        assert results == []

    def test_search_partial_match(self):
        create_workflow(WorkflowCreate(name="Data Pipeline"))
        results = list_workflows(search="pipe")
        assert len(results) == 1

    def test_search_case_insensitive(self):
        create_workflow(WorkflowCreate(name="My Workflow"))
        results = list_workflows(search="MY WORKFLOW")
        assert len(results) == 1

    def test_search_combined_with_tag(self):
        create_workflow(WorkflowCreate(name="Alpha", tags=["prod"]))
        create_workflow(WorkflowCreate(name="Beta", tags=["prod"]))
        create_workflow(WorkflowCreate(name="Alpha Dev", tags=["dev"]))
        results = list_workflows(tag="prod", search="alpha")
        assert len(results) == 1

    def test_search_with_pagination(self):
        for i in range(10):
            create_workflow(WorkflowCreate(name=f"Pipeline {i}"))
        results = list_workflows(search="pipeline", limit=3, offset=0)
        assert len(results) == 3

    def test_search_special_characters(self):
        create_workflow(WorkflowCreate(name="WF (v2.0)"))
        results = list_workflows(search="(v2")
        assert len(results) == 1

    def test_search_via_api(self, client):
        client.post("/api/workflows/", json={"name": "Searchable WF"})
        client.post("/api/workflows/", json={"name": "Other WF"})
        resp = client.get("/api/workflows/", params={"search": "searchable"})
        assert len(resp.json()) == 1

    def test_search_no_filter_returns_all(self):
        create_workflow(WorkflowCreate(name="A"))
        create_workflow(WorkflowCreate(name="B"))
        results = list_workflows(search=None)
        assert len(results) == 2

    def test_search_empty_string(self):
        create_workflow(WorkflowCreate(name="A"))
        results = list_workflows(search="")
        assert len(results) == 1

    def test_search_unicode(self):
        create_workflow(WorkflowCreate(name="工作流程"))
        results = list_workflows(search="工作")
        assert len(results) == 1


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
        result = compare_executions([ex1.id, ex2.id])
        assert result is not None
        assert result["workflow_id"] == wf.id
        assert result["summary"]["unchanged_count"] >= 1

    def test_compare_different_workflows_raises(self):
        wf1 = create_workflow(WorkflowCreate(name="WF1"))
        wf2 = create_workflow(WorkflowCreate(name="WF2"))
        ex1 = execute_workflow(wf1.id)
        ex2 = execute_workflow(wf2.id)
        with pytest.raises(ValueError, match="different workflows"):
            compare_executions([ex1.id, ex2.id])

    def test_compare_not_found(self):
        assert compare_executions(["a", "b"]) is None

    def test_compare_wrong_count(self):
        with pytest.raises(ValueError, match="Exactly two"):
            compare_executions(["a"])

    def test_compare_improved(self):
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
            ex2 = execute_workflow(wf.id)
        assert ex2.status == WorkflowStatus.COMPLETED

        result = compare_executions([ex1.id, ex2.id])
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
        assert "summary" in cmp_resp.json()

    def test_compare_different_workflows_via_api(self, client):
        wf1 = client.post("/api/workflows/", json={"name": "WF1"}).json()["id"]
        wf2 = client.post("/api/workflows/", json={"name": "WF2"}).json()["id"]
        ex1 = client.post(f"/api/workflows/{wf1}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf2}/execute").json()
        resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": f"{ex1['id']},{ex2['id']}"},
        )
        assert resp.status_code == 400

    def test_compare_not_found_via_api(self, client):
        resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": "a,b"},
        )
        assert resp.status_code == 404

    def test_compare_task_comparison_structure(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions([ex1.id, ex2.id])
        for tc in result["task_comparison"]:
            assert "task_id" in tc
            assert "status_a" in tc
            assert "status_b" in tc
            assert "duration_diff_ms" in tc

    def test_compare_single_id_raises_via_api(self, client):
        resp = client.get(
            "/api/tasks/executions/compare",
            params={"ids": "single-id"},
        )
        assert resp.status_code == 400


# ===========================================================================
# Topological Sort
# ===========================================================================


class TestTopologicalSort:
    def _make_task(self, tid: str, deps: list[str] | None = None) -> TaskDefinition:
        return TaskDefinition(
            id=tid, name=tid, action="log", depends_on=deps or [],
        )

    def test_single_task_no_deps(self):
        tasks = [self._make_task("A")]
        result = _topological_sort(tasks)
        assert [t.id for t in result] == ["A"]

    def test_linear_chain(self):
        tasks = [
            self._make_task("A"),
            self._make_task("B", ["A"]),
            self._make_task("C", ["B"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index("A") < ids.index("B") < ids.index("C")

    def test_fan_out(self):
        tasks = [
            self._make_task("A"),
            self._make_task("B", ["A"]),
            self._make_task("C", ["A"]),
            self._make_task("D", ["A"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids[0] == "A"
        assert set(ids[1:]) == {"B", "C", "D"}

    def test_fan_in(self):
        tasks = [
            self._make_task("A"),
            self._make_task("B"),
            self._make_task("C"),
            self._make_task("D", ["A", "B", "C"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index("D") == 3

    def test_diamond(self):
        tasks = [
            self._make_task("A"),
            self._make_task("B", ["A"]),
            self._make_task("C", ["A"]),
            self._make_task("D", ["B", "C"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index("A") < ids.index("B")
        assert ids.index("A") < ids.index("C")
        assert ids.index("B") < ids.index("D")
        assert ids.index("C") < ids.index("D")

    def test_disconnected_components(self):
        tasks = [
            self._make_task("A"),
            self._make_task("B", ["A"]),
            self._make_task("C"),
            self._make_task("D", ["C"]),
        ]
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index("A") < ids.index("B")
        assert ids.index("C") < ids.index("D")
        assert len(ids) == 4

    def test_nonexistent_dependency(self):
        tasks = [self._make_task("A", ["nonexistent"])]
        result = _topological_sort(tasks)
        assert len(result) == 1

    def test_self_referencing(self):
        tasks = [self._make_task("A", ["A"])]
        result = _topological_sort(tasks)
        assert len(result) == 1

    def test_large_dag(self):
        tasks = [self._make_task("task-0")]
        for i in range(1, 25):
            tasks.append(self._make_task(f"task-{i}", [f"task-{i-1}"]))
        result = _topological_sort(tasks)
        ids = [t.id for t in result]
        for i in range(24):
            assert ids.index(f"task-{i}") < ids.index(f"task-{i+1}")

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
        tasks = [{"id": "a", "name": "A", "action": "log", "parameters": {"message": "ok"}}]
        prev = "a"
        for c in "bcde":
            tasks.append({
                "id": c, "name": c.upper(), "action": "log",
                "parameters": {"message": "ok"}, "depends_on": [prev],
            })
            prev = c
        wf = create_workflow(WorkflowCreate(name="Deep", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert len(ex.task_results) == 5

    def test_diamond_dependencies_execution(self):
        wf = create_workflow(WorkflowCreate(
            name="Diamond",
            tasks=[
                {"id": "A", "name": "A", "action": "log", "parameters": {"message": "a"}},
                {"id": "B", "name": "B", "action": "log", "parameters": {"message": "b"}, "depends_on": ["A"]},
                {"id": "C", "name": "C", "action": "log", "parameters": {"message": "c"}, "depends_on": ["A"]},
                {"id": "D", "name": "D", "action": "log", "parameters": {"message": "d"}, "depends_on": ["B", "C"]},
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
        create_workflow(WorkflowCreate(name="WF"))
        results = list_workflows(offset=100)
        assert results == []

    def test_get_nonexistent_execution(self):
        assert get_execution("nonexistent") is None

    def test_list_executions_all_filters(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        execute_workflow(wf.id)
        results = list_executions(
            workflow_id=wf.id,
            status=WorkflowStatus.COMPLETED,
            limit=10,
        )
        assert len(results) == 1

    def test_list_executions_no_match(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        execute_workflow(wf.id)
        results = list_executions(status=WorkflowStatus.FAILED)
        assert results == []

    def test_execute_not_found(self):
        assert execute_workflow("nonexistent") is None
