"""Comprehensive tests for new backend features.

Covers: workflow cloning, versioning, tagging, search, dry-run,
execution comparison, topological sort edge cases, and formatters.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowUpdate, WorkflowStatus
from app.services.workflow_engine import (
    _topological_sort,
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
    search_workflows,
    update_workflow,
)
from app.models import TaskDefinition


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
        resp = client.post("/api/workflows/", json={"name": "Original", "tags": ["prod"]})
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        assert clone_resp.status_code == 201
        data = clone_resp.json()
        assert data["name"] == "Original (copy)"
        assert data["id"] != wf_id
        assert data["tags"] == ["prod"]

    def test_clone_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/clone")
        assert resp.status_code == 404

    def test_clone_deep_independence(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Deep",
            "tasks": [{"name": "T1", "action": "log", "parameters": {"msg": "hi"}}],
        })
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        clone_id = clone_resp.json()["id"]

        client.patch(f"/api/workflows/{clone_id}", json={"name": "Modified Clone"})
        original = client.get(f"/api/workflows/{wf_id}").json()
        assert original["name"] == "Deep"

    def test_clone_with_dependencies(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Dep WF",
            "tasks": [
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        })
        wf_id = resp.json()["id"]
        clone_resp = client.post(f"/api/workflows/{wf_id}/clone")
        assert clone_resp.status_code == 201
        clone_tasks = clone_resp.json()["tasks"]
        assert len(clone_tasks) == 2
        a_task = next(t for t in clone_tasks if t["name"] == "A")
        b_task = next(t for t in clone_tasks if t["name"] == "B")
        assert a_task["id"] in b_task["depends_on"]

    def test_clone_service_layer(self):
        wf = create_workflow(WorkflowCreate(name="SVC", tags=["x"]))
        clone = clone_workflow(wf.id)
        assert clone is not None
        assert clone.name == "SVC (copy)"
        assert clone.id != wf.id

    def test_clone_nonexistent_service(self):
        assert clone_workflow("nope") is None

    def test_clone_preserves_description(self):
        wf = create_workflow(WorkflowCreate(name="Desc", description="A desc"))
        clone = clone_workflow(wf.id)
        assert clone.description == "A desc"

    def test_clone_preserves_schedule(self):
        wf = create_workflow(WorkflowCreate(name="Sched", schedule="0 * * * *"))
        clone = clone_workflow(wf.id)
        assert clone.schedule == "0 * * * *"

    def test_clone_appears_in_list(self, client):
        resp = client.post("/api/workflows/", json={"name": "Listed"})
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/clone")
        all_wfs = client.get("/api/workflows/").json()
        assert len(all_wfs) == 2

    def test_clone_task_ids_differ(self):
        wf = create_workflow(WorkflowCreate(
            name="IDs",
            tasks=[{"name": "T", "action": "log", "parameters": {}}],
        ))
        clone = clone_workflow(wf.id)
        orig_ids = {t.id for t in wf.tasks}
        clone_ids = {t.id for t in clone.tasks}
        assert orig_ids != clone_ids


# ===========================================================================
# Workflow Versioning
# ===========================================================================


class TestWorkflowVersioning:
    def test_version_increments_on_update(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V3"})
        history = client.get(f"/api/workflows/{wf_id}/history").json()
        assert len(history) == 2

    def test_history_newest_first(self, client):
        resp = client.post("/api/workflows/", json={"name": "First"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "Second"})
        client.patch(f"/api/workflows/{wf_id}", json={"name": "Third"})
        history = client.get(f"/api/workflows/{wf_id}/history").json()
        assert history[0]["name"] == "Second"
        assert history[1]["name"] == "First"

    def test_fetch_specific_version(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "V2"})
        v1 = client.get(f"/api/workflows/{wf_id}/history/1").json()
        assert v1["name"] == "V1"

    def test_history_empty_for_new_workflow(self, client):
        resp = client.post("/api/workflows/", json={"name": "New"})
        wf_id = resp.json()["id"]
        history = client.get(f"/api/workflows/{wf_id}/history").json()
        assert history == []

    def test_history_not_found(self, client):
        resp = client.get("/api/workflows/nonexistent/history")
        assert resp.status_code == 404

    def test_version_not_found(self, client):
        resp = client.post("/api/workflows/", json={"name": "V1"})
        wf_id = resp.json()["id"]
        resp = client.get(f"/api/workflows/{wf_id}/history/99")
        assert resp.status_code == 404

    def test_version_snapshots_independent(self, client):
        resp = client.post("/api/workflows/", json={"name": "Orig", "tags": ["a"]})
        wf_id = resp.json()["id"]
        client.patch(f"/api/workflows/{wf_id}", json={"name": "Updated", "tags": ["b"]})
        v1 = client.get(f"/api/workflows/{wf_id}/history/1").json()
        assert v1["name"] == "Orig"
        assert v1["tags"] == ["a"]

    def test_service_layer_history(self):
        wf = create_workflow(WorkflowCreate(name="SVC"))
        update_workflow(wf.id, WorkflowUpdate(name="SVC2"))
        history = get_workflow_history(wf.id)
        assert history is not None
        assert len(history) == 1
        assert history[0]["name"] == "SVC"

    def test_service_layer_version(self):
        wf = create_workflow(WorkflowCreate(name="SVC"))
        update_workflow(wf.id, WorkflowUpdate(name="SVC2"))
        v1 = get_workflow_version(wf.id, 1)
        assert v1 is not None
        assert v1["name"] == "SVC"

    def test_service_layer_nonexistent(self):
        assert get_workflow_history("nope") is None
        assert get_workflow_version("nope", 1) is None


# ===========================================================================
# Workflow Tagging
# ===========================================================================


class TestWorkflowTagging:
    def test_add_single_tag(self, client):
        resp = client.post("/api/workflows/", json={"name": "Tag WF"})
        wf_id = resp.json()["id"]
        tag_resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["new"]})
        assert tag_resp.status_code == 200
        assert "new" in tag_resp.json()["tags"]

    def test_add_multiple_tags(self, client):
        resp = client.post("/api/workflows/", json={"name": "Tag WF"})
        wf_id = resp.json()["id"]
        tag_resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["a", "b", "c"]})
        tags = tag_resp.json()["tags"]
        assert "a" in tags and "b" in tags and "c" in tags

    def test_add_duplicate_tag_idempotent(self, client):
        resp = client.post("/api/workflows/", json={"name": "Tag WF", "tags": ["existing"]})
        wf_id = resp.json()["id"]
        tag_resp = client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["existing"]})
        assert tag_resp.json()["tags"].count("existing") == 1

    def test_remove_existing_tag(self, client):
        resp = client.post("/api/workflows/", json={"name": "Tag WF", "tags": ["remove-me"]})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/remove-me")
        assert del_resp.status_code == 200
        assert "remove-me" not in del_resp.json()["tags"]

    def test_remove_nonexistent_tag(self, client):
        resp = client.post("/api/workflows/", json={"name": "Tag WF"})
        wf_id = resp.json()["id"]
        del_resp = client.delete(f"/api/workflows/{wf_id}/tags/nope")
        assert del_resp.status_code == 404

    def test_tag_workflow_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/tags", json={"tags": ["x"]})
        assert resp.status_code == 404

    def test_remove_tag_workflow_not_found(self, client):
        resp = client.delete("/api/workflows/nonexistent/tags/x")
        assert resp.status_code == 404

    def test_tag_filter_reflects_changes(self, client):
        resp = client.post("/api/workflows/", json={"name": "Tag WF"})
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/tags", json={"tags": ["filterable"]})
        filtered = client.get("/api/workflows/", params={"tag": "filterable"}).json()
        assert len(filtered) == 1

    def test_service_add_tags(self):
        wf = create_workflow(WorkflowCreate(name="SVC"))
        result = add_tags(wf.id, ["x", "y"])
        assert result is not None
        assert "x" in result.tags

    def test_service_remove_tag(self):
        wf = create_workflow(WorkflowCreate(name="SVC", tags=["a"]))
        assert remove_tag(wf.id, "a") is True
        assert "a" not in get_workflow(wf.id).tags

    def test_service_remove_tag_not_found(self):
        wf = create_workflow(WorkflowCreate(name="SVC"))
        assert remove_tag(wf.id, "nope") is False

    def test_service_tag_nonexistent_workflow(self):
        assert add_tags("nope", ["x"]) is None
        assert remove_tag("nope", "x") is None


# ===========================================================================
# Workflow Search
# ===========================================================================


class TestWorkflowSearch:
    def test_search_empty_results(self, client):
        create_workflow(WorkflowCreate(name="Alpha"))
        resp = client.get("/api/workflows/", params={"search": "zzz"})
        assert resp.json() == []

    def test_search_partial_match(self, client):
        create_workflow(WorkflowCreate(name="Data Pipeline"))
        create_workflow(WorkflowCreate(name="ETL Job"))
        resp = client.get("/api/workflows/", params={"search": "pipe"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Data Pipeline"

    def test_search_case_insensitive(self, client):
        create_workflow(WorkflowCreate(name="MyWorkflow"))
        resp = client.get("/api/workflows/", params={"search": "myworkflow"})
        assert len(resp.json()) == 1

    def test_search_combined_with_tag(self, client):
        create_workflow(WorkflowCreate(name="Alpha Prod", tags=["prod"]))
        create_workflow(WorkflowCreate(name="Alpha Dev", tags=["dev"]))
        create_workflow(WorkflowCreate(name="Beta Prod", tags=["prod"]))
        resp = client.get("/api/workflows/", params={"search": "alpha", "tag": "prod"})
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "Alpha Prod"

    def test_search_with_pagination(self, client):
        for i in range(10):
            create_workflow(WorkflowCreate(name=f"Search-{i}"))
        resp = client.get("/api/workflows/", params={"search": "Search", "limit": 3, "offset": 0})
        assert len(resp.json()) == 3

    def test_search_special_characters(self, client):
        create_workflow(WorkflowCreate(name="WF (v2.0)"))
        resp = client.get("/api/workflows/", params={"search": "(v2"})
        assert len(resp.json()) == 1

    def test_search_empty_string_returns_all(self, client):
        create_workflow(WorkflowCreate(name="A"))
        create_workflow(WorkflowCreate(name="B"))
        resp = client.get("/api/workflows/", params={"search": ""})
        assert len(resp.json()) == 2

    def test_service_search(self):
        create_workflow(WorkflowCreate(name="Findable"))
        create_workflow(WorkflowCreate(name="Other"))
        results = list_workflows(search="find")
        assert len(results) == 1

    def test_service_search_with_tag(self):
        create_workflow(WorkflowCreate(name="A", tags=["x"]))
        create_workflow(WorkflowCreate(name="AB", tags=["y"]))
        results = list_workflows(search="A", tag="x")
        assert len(results) == 1

    def test_search_unicode(self, client):
        create_workflow(WorkflowCreate(name="工作流程"))
        resp = client.get("/api/workflows/", params={"search": "工作"})
        assert len(resp.json()) == 1


# ===========================================================================
# Dry-Run Execution
# ===========================================================================


class TestDryRunExecution:
    def test_basic_dry_run(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "DryRun WF",
            "tasks": [{"name": "T1", "action": "log", "parameters": {"msg": "hi"}}],
        })
        wf_id = resp.json()["id"]
        dr_resp = client.post(f"/api/workflows/{wf_id}/dry-run")
        assert dr_resp.status_code == 200
        data = dr_resp.json()
        assert data["status"] == "completed"
        assert data["trigger"] == "dry_run"
        assert data["task_results"][0]["output"]["dry_run"] is True

    def test_dry_run_with_dependencies(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Dep DryRun",
            "tasks": [
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        })
        wf_id = resp.json()["id"]
        dr_resp = client.post(f"/api/workflows/{wf_id}/dry-run")
        data = dr_resp.json()
        assert data["status"] == "completed"
        assert data["task_results"][0]["task_id"] == "a"
        assert data["task_results"][1]["task_id"] == "b"

    def test_dry_run_unknown_actions_succeed(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Unknown Action DryRun",
            "tasks": [{"name": "T1", "action": "nonexistent_action", "parameters": {}}],
        })
        wf_id = resp.json()["id"]
        dr_resp = client.post(f"/api/workflows/{wf_id}/dry-run")
        assert dr_resp.json()["status"] == "completed"

    def test_dry_run_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/dry-run")
        assert resp.status_code == 404

    def test_dry_run_not_stored(self, client):
        resp = client.post("/api/workflows/", json={"name": "NotStored"})
        wf_id = resp.json()["id"]
        client.post(f"/api/workflows/{wf_id}/dry-run")
        execs = client.get(f"/api/workflows/{wf_id}/executions").json()
        assert len(execs) == 0

    def test_dry_run_empty_workflow(self, client):
        resp = client.post("/api/workflows/", json={"name": "Empty"})
        wf_id = resp.json()["id"]
        dr_resp = client.post(f"/api/workflows/{wf_id}/dry-run")
        assert dr_resp.json()["status"] == "completed"
        assert dr_resp.json()["task_results"] == []

    def test_service_dry_run(self):
        wf = create_workflow(WorkflowCreate(
            name="SVC",
            tasks=[{"name": "T", "action": "log", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result is not None
        assert result.status == WorkflowStatus.COMPLETED

    def test_service_dry_run_nonexistent(self):
        assert dry_run_workflow("nope") is None

    def test_dry_run_has_timestamps(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Timed",
            "tasks": [{"name": "T", "action": "log", "parameters": {}}],
        })
        wf_id = resp.json()["id"]
        dr = client.post(f"/api/workflows/{wf_id}/dry-run").json()
        assert dr["started_at"] is not None
        assert dr["completed_at"] is not None

    def test_dry_run_task_duration_is_zero(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "ZeroDur",
            "tasks": [{"name": "T", "action": "log", "parameters": {}}],
        })
        wf_id = resp.json()["id"]
        dr = client.post(f"/api/workflows/{wf_id}/dry-run").json()
        assert dr["task_results"][0]["duration_ms"] == 0


# ===========================================================================
# Execution Comparison
# ===========================================================================


class TestExecutionComparison:
    def test_compare_same_workflow(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Compare WF",
            "tasks": [{"name": "T", "action": "log", "parameters": {"msg": "ok"}}],
        })
        wf_id = resp.json()["id"]
        e1 = client.post(f"/api/workflows/{wf_id}/execute").json()
        e2 = client.post(f"/api/workflows/{wf_id}/execute").json()

        cmp_resp = client.get("/api/tasks/executions/compare", params={"ids": f"{e1['id']},{e2['id']}"})
        assert cmp_resp.status_code == 200
        data = cmp_resp.json()
        assert data["workflow_id"] == wf_id
        assert len(data["executions"]) == 2
        assert len(data["task_comparison"]) >= 1

    def test_compare_different_workflows_returns_400(self, client):
        r1 = client.post("/api/workflows/", json={"name": "WF1", "tasks": [{"name": "T", "action": "log", "parameters": {}}]})
        r2 = client.post("/api/workflows/", json={"name": "WF2", "tasks": [{"name": "T", "action": "log", "parameters": {}}]})
        e1 = client.post(f"/api/workflows/{r1.json()['id']}/execute").json()
        e2 = client.post(f"/api/workflows/{r2.json()['id']}/execute").json()

        cmp_resp = client.get("/api/tasks/executions/compare", params={"ids": f"{e1['id']},{e2['id']}"})
        assert cmp_resp.status_code == 400

    def test_compare_nonexistent_execution(self, client):
        cmp_resp = client.get("/api/tasks/executions/compare", params={"ids": "a,b"})
        assert cmp_resp.status_code == 404

    def test_compare_wrong_count(self, client):
        cmp_resp = client.get("/api/tasks/executions/compare", params={"ids": "only-one"})
        assert cmp_resp.status_code == 400

    def test_compare_summary_counts(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "CMP",
            "tasks": [{"name": "T", "action": "log", "parameters": {"msg": "ok"}}],
        })
        wf_id = resp.json()["id"]
        e1 = client.post(f"/api/workflows/{wf_id}/execute").json()
        e2 = client.post(f"/api/workflows/{wf_id}/execute").json()

        data = client.get("/api/tasks/executions/compare", params={"ids": f"{e1['id']},{e2['id']}"}).json()
        summary = data["summary"]
        assert "improved_count" in summary
        assert "regressed_count" in summary
        assert "unchanged_count" in summary

    def test_service_compare(self):
        wf = create_workflow(WorkflowCreate(
            name="SVC",
            tasks=[{"name": "T", "action": "log", "parameters": {"msg": "ok"}}],
        ))
        e1 = execute_workflow(wf.id)
        e2 = execute_workflow(wf.id)
        result = compare_executions(e1.id, e2.id)
        assert result is not None
        assert result["workflow_id"] == wf.id

    def test_service_compare_nonexistent(self):
        assert compare_executions("a", "b") is None

    def test_service_compare_different_workflows(self):
        wf1 = create_workflow(WorkflowCreate(name="A", tasks=[{"name": "T", "action": "log", "parameters": {}}]))
        wf2 = create_workflow(WorkflowCreate(name="B", tasks=[{"name": "T", "action": "log", "parameters": {}}]))
        e1 = execute_workflow(wf1.id)
        e2 = execute_workflow(wf2.id)
        with pytest.raises(ValueError, match="different workflows"):
            compare_executions(e1.id, e2.id)

    def test_compare_mixed_statuses(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Mixed",
            "tasks": [
                {"name": "Good", "action": "log", "parameters": {"msg": "ok"}},
                {"name": "Bad", "action": "unknown_action", "parameters": {}},
            ],
        })
        wf_id = resp.json()["id"]
        e1 = client.post(f"/api/workflows/{wf_id}/execute").json()

        from app.services.workflow_engine import LogOutput
        with patch(
            "app.services.workflow_engine._run_action",
            side_effect=lambda action, params: LogOutput(message="fixed"),
        ):
            client.patch(f"/api/workflows/{wf_id}", json={"name": "Mixed"})
            e2 = client.post(f"/api/workflows/{wf_id}/execute").json()

        data = client.get("/api/tasks/executions/compare", params={"ids": f"{e1['id']},{e2['id']}"}).json()
        assert data["summary"]["improved_count"] >= 0

    def test_compare_three_ids_returns_400(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "a,b,c"})
        assert resp.status_code == 400


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

    def test_all_independent(self):
        tasks = [TaskDefinition(id=f"t{i}", name=f"T{i}", action="log") for i in range(10)]
        result = _topological_sort(tasks)
        assert len(result) == 10


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

    def test_format_timestamp_valid(self):
        from app.utils.formatters import format_timestamp
        from datetime import datetime
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert "2026" in format_timestamp(dt)

    def test_format_task_summary(self):
        from app.utils.formatters import format_task_summary
        result = format_task_summary({"task_id": "abc", "status": "completed", "duration_ms": 100})
        assert "abc" in result
        assert "completed" in result

    def test_format_execution_report(self):
        from app.utils.formatters import format_execution_report
        report = format_execution_report({
            "id": "exec-1",
            "status": "completed",
            "started_at": "2026-01-15",
            "completed_at": "2026-01-15",
            "task_results": [{"task_id": "t1", "status": "completed", "duration_ms": 50}],
        })
        assert "exec-1" in report
        assert "completed" in report

    def test_format_workflow_tree(self):
        from app.utils.formatters import format_workflow_tree
        tree = format_workflow_tree([
            {"id": "a", "name": "A", "action": "log", "depends_on": []},
            {"id": "b", "name": "B", "action": "validate", "depends_on": ["a"]},
        ])
        assert "A" in tree
        assert "B" in tree

    def test_format_workflow_tree_empty(self):
        from app.utils.formatters import format_workflow_tree
        assert format_workflow_tree([]) == ""


# ===========================================================================
# Edge case tests for workflow engine
# ===========================================================================


class TestWorkflowEngineEdgeCases:
    def test_empty_workflow_execution(self, client):
        resp = client.post("/api/workflows/", json={"name": "Empty"})
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.json()["status"] == "completed"
        assert exec_resp.json()["task_results"] == []

    def test_deeply_nested_dependencies(self, client):
        tasks = []
        for i in range(5):
            deps = [f"step-{i-1}"] if i > 0 else []
            tasks.append({"id": f"step-{i}", "name": f"Step {i}", "action": "log", "parameters": {"msg": str(i)}, "depends_on": deps})
        resp = client.post("/api/workflows/", json={"name": "Deep", "tasks": tasks})
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.json()["status"] == "completed"
        assert len(exec_resp.json()["task_results"]) == 5

    def test_diamond_dependencies(self, client):
        tasks = [
            {"id": "a", "name": "A", "action": "log", "parameters": {}},
            {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            {"id": "c", "name": "C", "action": "log", "parameters": {}, "depends_on": ["a"]},
            {"id": "d", "name": "D", "action": "log", "parameters": {}, "depends_on": ["b", "c"]},
        ]
        resp = client.post("/api/workflows/", json={"name": "Diamond", "tasks": tasks})
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.json()["status"] == "completed"
        assert len(exec_resp.json()["task_results"]) == 4

    def test_execute_same_workflow_twice_independent(self, client):
        resp = client.post("/api/workflows/", json={
            "name": "Twice",
            "tasks": [{"name": "T", "action": "log", "parameters": {"msg": "ok"}}],
        })
        wf_id = resp.json()["id"]
        e1 = client.post(f"/api/workflows/{wf_id}/execute").json()
        e2 = client.post(f"/api/workflows/{wf_id}/execute").json()
        assert e1["id"] != e2["id"]
        assert e1["status"] == "completed"
        assert e2["status"] == "completed"

    def test_pagination_offset_beyond_total(self, client):
        create_workflow(WorkflowCreate(name="Only"))
        resp = client.get("/api/workflows/", params={"offset": 100})
        assert resp.json() == []

    def test_get_nonexistent_execution(self, client):
        resp = client.get("/api/tasks/executions/nonexistent")
        assert resp.status_code == 404

    def test_list_executions_all_filters(self, client):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "T", "action": "log", "parameters": {"msg": "ok"}}],
        ))
        execute_workflow(wf.id)
        from app.services.workflow_engine import list_executions
        results = list_executions(workflow_id=wf.id, status=WorkflowStatus.COMPLETED, limit=10)
        assert len(results) == 1

    def test_update_deleted_workflow(self, client):
        resp = client.post("/api/workflows/", json={"name": "Del"})
        wf_id = resp.json()["id"]
        client.delete(f"/api/workflows/{wf_id}")
        update_resp = client.patch(f"/api/workflows/{wf_id}", json={"name": "Updated"})
        assert update_resp.status_code == 404

    def test_pagination_limit_1(self, client):
        for i in range(3):
            create_workflow(WorkflowCreate(name=f"WF-{i}"))
        resp = client.get("/api/workflows/", params={"limit": 1})
        assert len(resp.json()) == 1

    def test_workflow_with_all_actions(self, client):
        tasks = [
            {"name": f"T-{a}", "action": a, "parameters": {"message": "ok", "channel": "test"}}
            for a in ["log", "transform", "validate", "notify", "aggregate"]
        ]
        resp = client.post("/api/workflows/", json={"name": "All Actions", "tasks": tasks})
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.json()["status"] == "completed"
        assert len(exec_resp.json()["task_results"]) == 5
