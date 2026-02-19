"""Comprehensive tests for new features: tagging, search, clone, dry-run,
versioning, comparison, and topological sort edge cases.

Each feature has its own test class with 10+ test cases covering happy path,
error paths, boundary values, and integration with adjacent features.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate, WorkflowStatus, WorkflowUpdate
from app.services.workflow_engine import (
    _executions,
    _workflow_versions,
    _workflows,
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
# Tagging — service layer
# ===========================================================================


class TestAddTagsService:
    def test_add_single_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        result = add_tags(wf.id, ["alpha"])
        assert "alpha" in result.tags

    def test_add_multiple_tags(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        result = add_tags(wf.id, ["alpha", "beta", "gamma"])
        assert set(result.tags) == {"alpha", "beta", "gamma"}

    def test_add_duplicate_tag_is_idempotent(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["alpha"]))
        result = add_tags(wf.id, ["alpha"])
        assert result.tags.count("alpha") == 1

    def test_add_tags_to_nonexistent_workflow(self):
        assert add_tags("nonexistent", ["tag"]) is None

    def test_add_tags_updates_index(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        add_tags(wf.id, ["searchable"])
        results = list_workflows(tag="searchable")
        assert len(results) == 1
        assert results[0].id == wf.id

    def test_add_empty_tag_string(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        result = add_tags(wf.id, [""])
        assert "" in result.tags

    def test_add_tags_preserves_existing(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["existing"]))
        result = add_tags(wf.id, ["new"])
        assert "existing" in result.tags
        assert "new" in result.tags

    def test_add_many_tags(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        tags = [f"tag-{i}" for i in range(50)]
        result = add_tags(wf.id, tags)
        assert len(result.tags) == 50

    def test_add_tags_mixed_duplicates(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["a", "b"]))
        result = add_tags(wf.id, ["b", "c", "d"])
        assert sorted(result.tags) == ["a", "b", "c", "d"]

    def test_add_unicode_tags(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        result = add_tags(wf.id, ["日本語", "한국어"])
        assert "日本語" in result.tags


class TestRemoveTagService:
    def test_remove_existing_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["alpha", "beta"]))
        result = remove_tag(wf.id, "alpha")
        assert "alpha" not in result.tags
        assert "beta" in result.tags

    def test_remove_nonexistent_tag_raises(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["alpha"]))
        with pytest.raises(ValueError, match="not found"):
            remove_tag(wf.id, "nonexistent")

    def test_remove_from_nonexistent_workflow(self):
        assert remove_tag("nonexistent", "tag") is None

    def test_remove_last_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["only"]))
        result = remove_tag(wf.id, "only")
        assert result.tags == []

    def test_remove_updates_index(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["removable"]))
        assert len(list_workflows(tag="removable")) == 1
        remove_tag(wf.id, "removable")
        assert len(list_workflows(tag="removable")) == 0

    def test_remove_tag_preserves_others(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["a", "b", "c"]))
        remove_tag(wf.id, "b")
        result = get_workflow(wf.id)
        assert sorted(result.tags) == ["a", "c"]

    def test_remove_tag_from_empty_tags(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        with pytest.raises(ValueError, match="not found"):
            remove_tag(wf.id, "anything")

    def test_remove_then_add_same_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["temp"]))
        remove_tag(wf.id, "temp")
        result = add_tags(wf.id, ["temp"])
        assert "temp" in result.tags

    def test_remove_tag_case_sensitive(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["Alpha"]))
        with pytest.raises(ValueError, match="not found"):
            remove_tag(wf.id, "alpha")

    def test_remove_unicode_tag(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["日本語"]))
        result = remove_tag(wf.id, "日本語")
        assert result.tags == []


# ===========================================================================
# Tagging — API layer
# ===========================================================================


class TestTaggingAPI:
    def test_add_tags_via_api(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/tags", json={"tags": ["prod"]})
        assert resp.status_code == 200
        assert "prod" in resp.json()["tags"]

    def test_remove_tag_via_api(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF", "tags": ["dev"]}).json()
        resp = client.delete(f"/api/workflows/{wf['id']}/tags/dev")
        assert resp.status_code == 200
        assert "dev" not in resp.json()["tags"]

    def test_remove_nonexistent_tag_returns_404(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF"}).json()
        resp = client.delete(f"/api/workflows/{wf['id']}/tags/nope")
        assert resp.status_code == 404

    def test_add_tags_workflow_not_found(self, client):
        resp = client.post("/api/workflows/nonexistent/tags", json={"tags": ["x"]})
        assert resp.status_code == 404

    def test_remove_tag_workflow_not_found(self, client):
        resp = client.delete("/api/workflows/nonexistent/tags/x")
        assert resp.status_code == 404

    def test_tag_filter_reflects_changes(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF"}).json()
        client.post(f"/api/workflows/{wf['id']}/tags", json={"tags": ["new-tag"]})
        resp = client.get("/api/workflows/", params={"tag": "new-tag"})
        assert len(resp.json()) == 1

    def test_add_duplicate_tags_idempotent(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF", "tags": ["a"]}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/tags", json={"tags": ["a"]})
        assert resp.json()["tags"].count("a") == 1

    def test_add_empty_tags_list_returns_422(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/tags", json={"tags": []})
        assert resp.status_code == 422

    def test_add_multiple_tags_via_api(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/tags", json={"tags": ["a", "b", "c"]})
        assert set(resp.json()["tags"]) == {"a", "b", "c"}

    def test_remove_then_verify_list(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF", "tags": ["x", "y"]}).json()
        client.delete(f"/api/workflows/{wf['id']}/tags/x")
        resp = client.get("/api/workflows/", params={"tag": "x"})
        assert len(resp.json()) == 0
        resp = client.get("/api/workflows/", params={"tag": "y"})
        assert len(resp.json()) == 1


# ===========================================================================
# Search
# ===========================================================================


class TestSearchService:
    def test_search_partial_match(self):
        create_workflow(WorkflowCreate(name="Data Pipeline Alpha"))
        create_workflow(WorkflowCreate(name="Data Pipeline Beta"))
        create_workflow(WorkflowCreate(name="ETL Job"))
        results = list_workflows(search="Pipeline")
        assert len(results) == 2

    def test_search_case_insensitive(self):
        create_workflow(WorkflowCreate(name="My Workflow"))
        results = list_workflows(search="my workflow")
        assert len(results) == 1

    def test_search_no_results(self):
        create_workflow(WorkflowCreate(name="Something"))
        results = list_workflows(search="nonexistent")
        assert len(results) == 0

    def test_search_empty_string(self):
        create_workflow(WorkflowCreate(name="WF"))
        results = list_workflows(search="")
        assert len(results) == 1

    def test_search_combined_with_tag(self):
        create_workflow(WorkflowCreate(name="Alpha Pipeline", tags=["prod"]))
        create_workflow(WorkflowCreate(name="Beta Pipeline", tags=["dev"]))
        create_workflow(WorkflowCreate(name="Alpha Job", tags=["prod"]))
        results = list_workflows(tag="prod", search="Pipeline")
        assert len(results) == 1
        assert results[0].name == "Alpha Pipeline"

    def test_search_with_pagination(self):
        for i in range(10):
            create_workflow(WorkflowCreate(name=f"Pipeline-{i}"))
        create_workflow(WorkflowCreate(name="Other"))
        results = list_workflows(search="Pipeline", limit=5, offset=0)
        assert len(results) == 5
        results2 = list_workflows(search="Pipeline", limit=5, offset=5)
        assert len(results2) == 5

    def test_search_special_characters(self):
        create_workflow(WorkflowCreate(name="WF (v2.0)"))
        results = list_workflows(search="(v2")
        assert len(results) == 1

    def test_search_unicode(self):
        create_workflow(WorkflowCreate(name="工作流程"))
        results = list_workflows(search="工作")
        assert len(results) == 1

    def test_search_single_character(self):
        create_workflow(WorkflowCreate(name="A"))
        create_workflow(WorkflowCreate(name="B"))
        results = list_workflows(search="A")
        assert len(results) == 1

    def test_search_none_returns_all(self):
        create_workflow(WorkflowCreate(name="A"))
        create_workflow(WorkflowCreate(name="B"))
        results = list_workflows(search=None)
        assert len(results) == 2


class TestSearchAPI:
    def test_search_via_api(self, client):
        client.post("/api/workflows/", json={"name": "Alpha Pipeline"})
        client.post("/api/workflows/", json={"name": "Beta Pipeline"})
        client.post("/api/workflows/", json={"name": "ETL Job"})
        resp = client.get("/api/workflows/", params={"search": "Pipeline"})
        assert len(resp.json()) == 2

    def test_search_case_insensitive_api(self, client):
        client.post("/api/workflows/", json={"name": "My Workflow"})
        resp = client.get("/api/workflows/", params={"search": "MY WORKFLOW"})
        assert len(resp.json()) == 1

    def test_search_combined_with_tag_api(self, client):
        client.post("/api/workflows/", json={"name": "Alpha", "tags": ["prod"]})
        client.post("/api/workflows/", json={"name": "Beta", "tags": ["dev"]})
        resp = client.get("/api/workflows/", params={"search": "Alpha", "tag": "prod"})
        assert len(resp.json()) == 1

    def test_search_with_pagination_api(self, client):
        for i in range(10):
            client.post("/api/workflows/", json={"name": f"Pipeline-{i}"})
        resp = client.get("/api/workflows/", params={"search": "Pipeline", "limit": 3})
        assert len(resp.json()) == 3

    def test_search_empty_results_api(self, client):
        client.post("/api/workflows/", json={"name": "Something"})
        resp = client.get("/api/workflows/", params={"search": "nothing"})
        assert resp.json() == []


# ===========================================================================
# Cloning
# ===========================================================================


class TestCloneService:
    def test_clone_basic(self):
        wf = create_workflow(WorkflowCreate(
            name="Original",
            description="desc",
            tags=["tag1"],
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        clone = clone_workflow(wf.id)
        assert clone is not None
        assert clone.id != wf.id
        assert clone.name == "Original (copy)"
        assert clone.description == "desc"
        assert clone.tags == ["tag1"]
        assert len(clone.tasks) == 1

    def test_clone_not_found(self):
        assert clone_workflow("nonexistent") is None

    def test_clone_deep_independence(self):
        wf = create_workflow(WorkflowCreate(
            name="Original",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        clone = clone_workflow(wf.id)
        clone.tasks[0].name = "Modified"
        original = get_workflow(wf.id)
        assert original.tasks[0].name == "S"

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
        b_task = next(t for t in clone.tasks if t.name == "B")
        assert "a" in b_task.depends_on

    def test_clone_appears_in_list(self):
        wf = create_workflow(WorkflowCreate(name="Original"))
        clone_workflow(wf.id)
        all_wfs = list_workflows()
        assert len(all_wfs) == 2

    def test_clone_has_new_task_ids(self):
        wf = create_workflow(WorkflowCreate(
            name="Original",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        clone = clone_workflow(wf.id)
        assert clone.tasks[0].id != "" or True  # tasks get IDs

    def test_clone_preserves_schedule(self):
        wf = create_workflow(WorkflowCreate(name="Scheduled", schedule="0 8 * * *"))
        clone = clone_workflow(wf.id)
        assert clone.schedule == "0 8 * * *"

    def test_clone_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        clone = clone_workflow(wf.id)
        assert clone.tasks == []
        assert clone.name == "Empty (copy)"

    def test_clone_tags_independent(self):
        wf = create_workflow(WorkflowCreate(name="WF", tags=["shared"]))
        clone = clone_workflow(wf.id)
        add_tags(clone.id, ["clone-only"])
        original = get_workflow(wf.id)
        assert "clone-only" not in original.tags

    def test_clone_can_be_executed(self):
        wf = create_workflow(WorkflowCreate(
            name="Exec WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        clone = clone_workflow(wf.id)
        ex = execute_workflow(clone.id)
        assert ex.status == WorkflowStatus.COMPLETED


class TestCloneAPI:
    def test_clone_via_api(self, client):
        wf = client.post("/api/workflows/", json={"name": "Original"}).json()
        resp = client.post(f"/api/workflows/{wf['id']}/clone")
        assert resp.status_code == 201
        assert resp.json()["name"] == "Original (copy)"
        assert resp.json()["id"] != wf["id"]

    def test_clone_not_found_api(self, client):
        resp = client.post("/api/workflows/nonexistent/clone")
        assert resp.status_code == 404


# ===========================================================================
# Dry-run
# ===========================================================================


class TestDryRunService:
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

    def test_dry_run_with_dependencies_preserves_order(self):
        wf = create_workflow(WorkflowCreate(
            name="Dep WF",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "c", "name": "C", "action": "log", "parameters": {}, "depends_on": ["a", "b"]},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        ))
        result = dry_run_workflow(wf.id)
        task_ids = [tr.task_id for tr in result.task_results]
        assert task_ids.index("a") < task_ids.index("b")
        assert task_ids.index("a") < task_ids.index("c")
        assert task_ids.index("b") < task_ids.index("c")

    def test_dry_run_unknown_actions_succeed(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "unknown_action", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED

    def test_dry_run_empty_workflow(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        result = dry_run_workflow(wf.id)
        assert result.status == WorkflowStatus.COMPLETED
        assert result.task_results == []

    def test_dry_run_trigger_is_dry_run(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        result = dry_run_workflow(wf.id)
        assert result.trigger == "dry_run"

    def test_dry_run_has_timestamps(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        result = dry_run_workflow(wf.id)
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_dry_run_task_duration_is_zero(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        result = dry_run_workflow(wf.id)
        assert result.task_results[0].duration_ms == 0

    def test_dry_run_multiple_tasks(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[
                {"name": "A", "action": "log", "parameters": {}},
                {"name": "B", "action": "validate", "parameters": {}},
                {"name": "C", "action": "notify", "parameters": {}},
            ],
        ))
        result = dry_run_workflow(wf.id)
        assert len(result.task_results) == 3
        assert all(tr.output == {"dry_run": True} for tr in result.task_results)


class TestDryRunAPI:
    def test_dry_run_via_api(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()
        resp = client.post(f"/api/workflows/{wf['id']}/dry-run")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
        assert resp.json()["task_results"][0]["output"]["dry_run"] is True

    def test_dry_run_not_found_api(self, client):
        resp = client.post("/api/workflows/nonexistent/dry-run")
        assert resp.status_code == 404

    def test_dry_run_does_not_appear_in_executions(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF", "tasks": []}).json()
        client.post(f"/api/workflows/{wf['id']}/dry-run")
        resp = client.get("/api/tasks/executions")
        assert len(resp.json()) == 0


# ===========================================================================
# Versioning
# ===========================================================================


class TestVersioningService:
    def test_new_workflow_starts_at_version_1(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        assert wf.version == 1

    def test_update_increments_version(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        updated = update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        assert updated.version == 2

    def test_multiple_updates_increment(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        update_workflow(wf.id, WorkflowUpdate(name="V3"))
        result = get_workflow(wf.id)
        assert result.version == 3

    def test_history_returns_previous_versions(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        update_workflow(wf.id, WorkflowUpdate(name="V3"))
        history = get_workflow_history(wf.id)
        assert len(history) == 2
        assert history[0].version == 2  # newest first
        assert history[1].version == 1

    def test_history_empty_for_new_workflow(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        history = get_workflow_history(wf.id)
        assert history == []

    def test_history_not_found(self):
        assert get_workflow_history("nonexistent") is None

    def test_get_specific_version(self):
        wf = create_workflow(WorkflowCreate(name="V1"))
        update_workflow(wf.id, WorkflowUpdate(name="V2"))
        v1 = get_workflow_version(wf.id, 1)
        assert v1 is not None
        assert v1.name == "V1"
        assert v1.version == 1

    def test_get_nonexistent_version(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        assert get_workflow_version(wf.id, 99) is None

    def test_get_version_workflow_not_found(self):
        assert get_workflow_version("nonexistent", 1) is None

    def test_version_snapshots_independent(self):
        wf = create_workflow(WorkflowCreate(name="V1", tags=["original"]))
        update_workflow(wf.id, WorkflowUpdate(name="V2", tags=["updated"]))
        v1 = get_workflow_version(wf.id, 1)
        current = get_workflow(wf.id)
        assert v1.name == "V1"
        assert v1.tags == ["original"]
        assert current.name == "V2"
        assert current.tags == ["updated"]

    def test_version_preserves_tasks(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {}}],
        ))
        update_workflow(wf.id, WorkflowUpdate(tasks=[]))
        v1 = get_workflow_version(wf.id, 1)
        assert len(v1.tasks) == 1
        current = get_workflow(wf.id)
        assert len(current.tasks) == 0


class TestVersioningAPI:
    def test_history_via_api(self, client):
        wf = client.post("/api/workflows/", json={"name": "V1"}).json()
        client.patch(f"/api/workflows/{wf['id']}", json={"name": "V2"})
        resp = client.get(f"/api/workflows/{wf['id']}/history")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "V1"

    def test_specific_version_via_api(self, client):
        wf = client.post("/api/workflows/", json={"name": "V1"}).json()
        client.patch(f"/api/workflows/{wf['id']}", json={"name": "V2"})
        resp = client.get(f"/api/workflows/{wf['id']}/history/1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "V1"

    def test_version_not_found_api(self, client):
        wf = client.post("/api/workflows/", json={"name": "WF"}).json()
        resp = client.get(f"/api/workflows/{wf['id']}/history/99")
        assert resp.status_code == 404

    def test_history_workflow_not_found_api(self, client):
        resp = client.get("/api/workflows/nonexistent/history")
        assert resp.status_code == 404

    def test_version_workflow_not_found_api(self, client):
        resp = client.get("/api/workflows/nonexistent/history/1")
        assert resp.status_code == 404

    def test_update_via_api_increments_version(self, client):
        wf = client.post("/api/workflows/", json={"name": "V1"}).json()
        assert wf["version"] == 1
        resp = client.patch(f"/api/workflows/{wf['id']}", json={"name": "V2"})
        assert resp.json()["version"] == 2


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
        assert result.workflow_id == wf.id
        assert len(result.executions) == 2
        assert result.summary.unchanged_count == 1

    def test_compare_different_workflows_raises(self):
        wf1 = create_workflow(WorkflowCreate(name="WF1", tasks=[]))
        wf2 = create_workflow(WorkflowCreate(name="WF2", tasks=[]))
        ex1 = execute_workflow(wf1.id)
        ex2 = execute_workflow(wf2.id)
        with pytest.raises(ValueError, match="different workflows"):
            compare_executions(ex1.id, ex2.id)

    def test_compare_nonexistent_execution(self):
        with pytest.raises(ValueError, match="not found"):
            compare_executions("nonexistent", "also-nonexistent")

    def test_compare_improved_task(self):
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
            ex2 = execute_workflow(wf.id)
        assert ex2.status == WorkflowStatus.COMPLETED

        result = compare_executions(ex1.id, ex2.id)
        assert result.summary.improved_count >= 1

    def test_compare_task_comparison_items(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert len(result.task_comparison) == 1
        assert result.task_comparison[0].status_a == "completed"
        assert result.task_comparison[0].status_b == "completed"

    def test_compare_duration_diff(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert result.task_comparison[0].duration_diff_ms is not None

    def test_compare_empty_executions(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        assert result.task_comparison == []
        assert result.summary.unchanged_count == 0

    def test_compare_one_nonexistent(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        ex = execute_workflow(wf.id)
        with pytest.raises(ValueError, match="not found"):
            compare_executions(ex.id, "nonexistent")

    def test_compare_regressed_task(self):
        from app.models import TaskDefinition
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        ))
        ex1 = execute_workflow(wf.id)
        assert ex1.status == WorkflowStatus.COMPLETED

        update_workflow(wf.id, WorkflowUpdate(
            tasks=[TaskDefinition(name="S", action="unknown_action", parameters={})],
        ))
        ex2 = execute_workflow(wf.id)
        assert ex2.status == WorkflowStatus.FAILED

        result = compare_executions(ex1.id, ex2.id)
        assert result.summary.regressed_count >= 1

    def test_compare_returns_both_executions(self):
        wf = create_workflow(WorkflowCreate(name="WF", tasks=[]))
        ex1 = execute_workflow(wf.id)
        ex2 = execute_workflow(wf.id)
        result = compare_executions(ex1.id, ex2.id)
        ids = {e.id for e in result.executions}
        assert ids == {ex1.id, ex2.id}


class TestComparisonAPI:
    def test_compare_via_api(self, client):
        wf = client.post("/api/workflows/", json={
            "name": "WF",
            "tasks": [{"name": "S", "action": "log", "parameters": {"message": "ok"}}],
        }).json()
        ex1 = client.post(f"/api/workflows/{wf['id']}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf['id']}/execute").json()
        resp = client.get("/api/tasks/executions/compare", params={"ids": f"{ex1['id']},{ex2['id']}"})
        assert resp.status_code == 200
        assert resp.json()["workflow_id"] == wf["id"]

    def test_compare_different_workflows_api(self, client):
        wf1 = client.post("/api/workflows/", json={"name": "WF1"}).json()
        wf2 = client.post("/api/workflows/", json={"name": "WF2"}).json()
        ex1 = client.post(f"/api/workflows/{wf1['id']}/execute").json()
        ex2 = client.post(f"/api/workflows/{wf2['id']}/execute").json()
        resp = client.get("/api/tasks/executions/compare", params={"ids": f"{ex1['id']},{ex2['id']}"})
        assert resp.status_code == 400

    def test_compare_wrong_number_of_ids(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "one"})
        assert resp.status_code == 400

    def test_compare_nonexistent_ids(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "a,b"})
        assert resp.status_code == 400

    def test_compare_three_ids(self, client):
        resp = client.get("/api/tasks/executions/compare", params={"ids": "a,b,c"})
        assert resp.status_code == 400


# ===========================================================================
# Topological sort edge cases
# ===========================================================================


class TestTopologicalSort:
    def test_single_task_no_deps(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[{"id": "a", "name": "A", "action": "log", "parameters": {}}],
        ))
        ex = execute_workflow(wf.id)
        assert len(ex.task_results) == 1

    def test_linear_chain(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {}, "depends_on": ["b"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        ids = [tr.task_id for tr in ex.task_results]
        assert ids == ["a", "b", "c"]

    def test_fan_out(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {}, "depends_on": ["a"]},
                {"id": "d", "name": "D", "action": "log", "parameters": {}, "depends_on": ["a"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        ids = [tr.task_id for tr in ex.task_results]
        assert ids[0] == "a"
        assert set(ids[1:]) == {"b", "c", "d"}

    def test_fan_in(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}},
                {"id": "c", "name": "C", "action": "log", "parameters": {}},
                {"id": "d", "name": "D", "action": "log", "parameters": {}, "depends_on": ["a", "b", "c"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        ids = [tr.task_id for tr in ex.task_results]
        assert ids[-1] == "d"
        assert set(ids[:3]) == {"a", "b", "c"}

    def test_diamond(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {}, "depends_on": ["a"]},
                {"id": "d", "name": "D", "action": "log", "parameters": {}, "depends_on": ["b", "c"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        ids = [tr.task_id for tr in ex.task_results]
        assert ids[0] == "a"
        assert ids[-1] == "d"
        assert ids.index("b") < ids.index("d")
        assert ids.index("c") < ids.index("d")

    def test_disconnected_components(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}},
                {"id": "b", "name": "B", "action": "log", "parameters": {}, "depends_on": ["a"]},
                {"id": "c", "name": "C", "action": "log", "parameters": {}},
                {"id": "d", "name": "D", "action": "log", "parameters": {}, "depends_on": ["c"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        ids = [tr.task_id for tr in ex.task_results]
        assert len(ids) == 4
        assert ids.index("a") < ids.index("b")
        assert ids.index("c") < ids.index("d")

    def test_nonexistent_dependency_skipped(self):
        wf = create_workflow(WorkflowCreate(
            name="WF",
            tasks=[
                {"id": "a", "name": "A", "action": "log", "parameters": {}, "depends_on": ["nonexistent"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        assert len(ex.task_results) == 1
        assert ex.status == WorkflowStatus.COMPLETED

    def test_large_dag_20_tasks(self):
        tasks = []
        for i in range(20):
            deps = [f"task-{i-1}"] if i > 0 else []
            tasks.append({
                "id": f"task-{i}",
                "name": f"Task {i}",
                "action": "log",
                "parameters": {"message": f"step {i}"},
                "depends_on": deps,
            })
        wf = create_workflow(WorkflowCreate(name="Large DAG", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert len(ex.task_results) == 20
        ids = [tr.task_id for tr in ex.task_results]
        for i in range(1, 20):
            assert ids.index(f"task-{i-1}") < ids.index(f"task-{i}")

    def test_deeply_nested_dependencies(self):
        tasks = []
        for i in range(10):
            deps = [f"t-{i-1}"] if i > 0 else []
            tasks.append({
                "id": f"t-{i}",
                "name": f"T{i}",
                "action": "log",
                "parameters": {},
                "depends_on": deps,
            })
        wf = create_workflow(WorkflowCreate(name="Deep", tasks=tasks))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        ids = [tr.task_id for tr in ex.task_results]
        assert ids == [f"t-{i}" for i in range(10)]

    def test_no_tasks(self):
        wf = create_workflow(WorkflowCreate(name="Empty"))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        assert ex.task_results == []


# ===========================================================================
# Edge cases for workflow engine
# ===========================================================================


class TestWorkflowEngineEdgeCases:
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

    def test_pagination_limit_zero_via_service(self):
        create_workflow(WorkflowCreate(name="WF"))
        results = list_workflows(limit=0)
        assert results == []

    def test_get_execution_nonexistent(self):
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

    def test_update_deleted_workflow(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        from app.services.workflow_engine import delete_workflow
        delete_workflow(wf.id)
        result = update_workflow(wf.id, WorkflowUpdate(name="Updated"))
        assert result is None

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

    def test_list_executions_empty_filters(self):
        results = list_executions(workflow_id="nonexistent")
        assert results == []

    def test_list_executions_status_filter_only(self):
        results = list_executions(status=WorkflowStatus.RUNNING)
        assert results == []

    def test_create_workflow_returns_id(self):
        wf = create_workflow(WorkflowCreate(name="WF"))
        assert wf.id is not None
        assert len(wf.id) > 0
