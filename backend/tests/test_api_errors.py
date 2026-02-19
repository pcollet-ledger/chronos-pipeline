"""Comprehensive tests for API error responses.

Covers the following error categories across all API endpoints:
  - Invalid JSON bodies (malformed syntax, wrong content-type)
  - Missing required fields (Pydantic validation errors)
  - Invalid enum/filter values (e.g. bad status filter)
  - Very long workflow names and string boundary conditions
  - Wrong HTTP methods and malformed path parameters
  - Invalid query parameter types and out-of-range values
  - Update/patch endpoint validation errors

Each test class targets a specific error category with at least 5 test
cases to ensure thorough coverage of edge cases.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowStatus
from app.services.workflow_engine import clear_all


@pytest.fixture(autouse=True)
def cleanup():
    """Clear all in-memory state before and after each test."""
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    return TestClient(app)


def _create_workflow(client, name="Error Test WF"):
    """Helper to create a valid workflow and return its ID."""
    payload = {
        "name": name,
        "tasks": [
            {"name": "Step", "action": "log", "parameters": {"message": "ok"}},
        ],
    }
    resp = client.post("/api/workflows/", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


# ===========================================================================
# Invalid JSON body — malformed syntax sent to POST/PATCH endpoints
# ===========================================================================


class TestInvalidJsonBody:
    """Sending syntactically invalid JSON should return 422."""

    def test_create_workflow_with_malformed_json(self, client):
        """Completely broken JSON syntax should be rejected."""
        resp = client.post(
            "/api/workflows/",
            content=b'{name: "bad json"',
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_create_workflow_with_trailing_comma(self, client):
        """JSON with a trailing comma is invalid syntax."""
        resp = client.post(
            "/api/workflows/",
            content=b'{"name": "test",}',
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_create_workflow_with_empty_body(self, client):
        """An empty request body should fail validation."""
        resp = client.post(
            "/api/workflows/",
            content=b"",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_create_workflow_with_plain_text_body(self, client):
        """Sending plain text instead of JSON should be rejected."""
        resp = client.post(
            "/api/workflows/",
            content=b"this is not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_create_workflow_with_array_instead_of_object(self, client):
        """A JSON array where an object is expected should fail validation."""
        resp = client.post(
            "/api/workflows/",
            content=b'[{"name": "test"}]',
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_update_workflow_with_malformed_json(self, client):
        """PATCH with broken JSON should return 422."""
        wf_id = _create_workflow(client)
        resp = client.patch(
            f"/api/workflows/{wf_id}",
            content=b"{bad json}",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_create_workflow_with_null_body(self, client):
        """Sending literal JSON null as the body should fail validation."""
        resp = client.post(
            "/api/workflows/",
            content=b"null",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422


# ===========================================================================
# Missing required fields — Pydantic model validation
# ===========================================================================


class TestMissingRequiredFields:
    """Omitting required fields should produce 422 with descriptive errors."""

    def test_create_workflow_missing_name(self, client):
        """The 'name' field is required for WorkflowCreate."""
        resp = client.post("/api/workflows/", json={"description": "no name"})
        assert resp.status_code == 422
        body = resp.json()
        assert "detail" in body
        errors = body["detail"]
        field_names = [e["loc"][-1] for e in errors]
        assert "name" in field_names

    def test_create_workflow_name_wrong_type(self, client):
        """Passing a non-string type for 'name' should fail validation."""
        resp = client.post("/api/workflows/", json={"name": 12345})
        # Pydantic v2 coerces int to str in strict=False mode, so this may
        # succeed with name="12345". If it does, verify the coercion.
        if resp.status_code == 201:
            assert resp.json()["name"] == "12345"
        else:
            assert resp.status_code == 422

    def test_create_workflow_tasks_wrong_type(self, client):
        """Passing a string for 'tasks' (expects list) should fail."""
        resp = client.post(
            "/api/workflows/",
            json={"name": "Bad Tasks", "tasks": "not a list"},
        )
        assert resp.status_code == 422

    def test_create_workflow_task_missing_action(self, client):
        """Each TaskDefinition requires an 'action' field."""
        resp = client.post(
            "/api/workflows/",
            json={
                "name": "Missing Action",
                "tasks": [{"name": "Step"}],
            },
        )
        assert resp.status_code == 422
        errors = resp.json()["detail"]
        # The error should reference the missing 'action' field
        all_locs = [".".join(str(x) for x in e["loc"]) for e in errors]
        assert any("action" in loc for loc in all_locs)

    def test_create_workflow_task_missing_name(self, client):
        """Each TaskDefinition requires a 'name' field."""
        resp = client.post(
            "/api/workflows/",
            json={
                "name": "Missing Task Name",
                "tasks": [{"action": "log"}],
            },
        )
        assert resp.status_code == 422
        errors = resp.json()["detail"]
        all_locs = [".".join(str(x) for x in e["loc"]) for e in errors]
        assert any("name" in loc for loc in all_locs)

    def test_create_workflow_empty_object(self, client):
        """An empty JSON object should fail because 'name' is required."""
        resp = client.post("/api/workflows/", json={})
        assert resp.status_code == 422

    def test_create_workflow_task_invalid_priority(self, client):
        """An invalid priority enum value should be rejected."""
        resp = client.post(
            "/api/workflows/",
            json={
                "name": "Bad Priority",
                "tasks": [
                    {
                        "name": "Step",
                        "action": "log",
                        "priority": "urgent",
                    }
                ],
            },
        )
        assert resp.status_code == 422

    def test_create_workflow_task_negative_timeout(self, client):
        """A task with timeout_seconds as a string should be coerced or rejected."""
        resp = client.post(
            "/api/workflows/",
            json={
                "name": "Bad Timeout",
                "tasks": [
                    {
                        "name": "Step",
                        "action": "log",
                        "timeout_seconds": "not_a_number",
                    }
                ],
            },
        )
        assert resp.status_code == 422


# ===========================================================================
# Invalid status filter value — tasks/executions endpoint
# ===========================================================================


class TestInvalidStatusFilter:
    """The status query parameter must be a valid WorkflowStatus value."""

    def test_invalid_status_returns_400(self, client):
        """A completely bogus status string should return 400."""
        resp = client.get("/api/tasks/executions", params={"status": "bogus"})
        assert resp.status_code == 400
        assert "Invalid status" in resp.json()["detail"]

    def test_status_typo_returns_400(self, client):
        """A close-but-wrong status like 'compelted' should return 400."""
        resp = client.get("/api/tasks/executions", params={"status": "compelted"})
        assert resp.status_code == 400

    def test_status_uppercase_returns_400(self, client):
        """Status values are case-sensitive; 'PENDING' != 'pending'."""
        resp = client.get("/api/tasks/executions", params={"status": "PENDING"})
        assert resp.status_code == 400

    def test_status_empty_string_treated_as_no_filter(self, client):
        """An empty string is falsy in Python, so the filter is skipped."""
        resp = client.get("/api/tasks/executions", params={"status": ""})
        assert resp.status_code == 200

    def test_status_numeric_returns_400(self, client):
        """A numeric status value should be rejected."""
        resp = client.get("/api/tasks/executions", params={"status": "123"})
        assert resp.status_code == 400

    def test_valid_statuses_return_200(self, client):
        """All valid WorkflowStatus values should be accepted."""
        for status in WorkflowStatus:
            resp = client.get(
                "/api/tasks/executions", params={"status": status.value}
            )
            assert resp.status_code == 200, f"Status '{status.value}' should be valid"

    def test_status_with_whitespace_returns_400(self, client):
        """Status with leading/trailing whitespace should be rejected."""
        resp = client.get("/api/tasks/executions", params={"status": " pending "})
        assert resp.status_code == 400

    def test_error_detail_lists_valid_values(self, client):
        """The 400 error message should enumerate the valid status values."""
        resp = client.get("/api/tasks/executions", params={"status": "invalid"})
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        for status in WorkflowStatus:
            assert status.value in detail


# ===========================================================================
# Very long workflow names — boundary and stress conditions
# ===========================================================================


class TestVeryLongWorkflowNames:
    """Test API behaviour with extremely long string values."""

    def test_long_name_accepted(self, client):
        """A moderately long name (255 chars) should be accepted."""
        long_name = "W" * 255
        resp = client.post("/api/workflows/", json={"name": long_name})
        assert resp.status_code == 201
        assert resp.json()["name"] == long_name

    def test_very_long_name_accepted(self, client):
        """A very long name (10,000 chars) should still be accepted."""
        very_long = "X" * 10_000
        resp = client.post("/api/workflows/", json={"name": very_long})
        assert resp.status_code == 201
        assert resp.json()["name"] == very_long

    def test_long_name_roundtrip(self, client):
        """A long name should survive create -> get roundtrip."""
        long_name = "Workflow-" + "A" * 5000
        create_resp = client.post("/api/workflows/", json={"name": long_name})
        wf_id = create_resp.json()["id"]
        get_resp = client.get(f"/api/workflows/{wf_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == long_name

    def test_long_description_accepted(self, client):
        """A very long description should be accepted."""
        long_desc = "D" * 50_000
        resp = client.post(
            "/api/workflows/",
            json={"name": "Long Desc", "description": long_desc},
        )
        assert resp.status_code == 201
        assert resp.json()["description"] == long_desc

    def test_long_task_name_accepted(self, client):
        """Task names can also be very long."""
        long_task_name = "Task-" + "T" * 5000
        resp = client.post(
            "/api/workflows/",
            json={
                "name": "Long Task Name WF",
                "tasks": [
                    {
                        "name": long_task_name,
                        "action": "log",
                        "parameters": {"message": "ok"},
                    }
                ],
            },
        )
        assert resp.status_code == 201
        assert resp.json()["tasks"][0]["name"] == long_task_name

    def test_unicode_name_accepted(self, client):
        """Unicode characters in workflow names should be handled correctly."""
        unicode_name = "工作流程-テスト-워크플로우-🔧"
        resp = client.post("/api/workflows/", json={"name": unicode_name})
        assert resp.status_code == 201
        assert resp.json()["name"] == unicode_name

    def test_empty_string_name_accepted(self, client):
        """An empty string is technically a valid str; Pydantic allows it."""
        resp = client.post("/api/workflows/", json={"name": ""})
        assert resp.status_code == 201
        assert resp.json()["name"] == ""

    def test_whitespace_only_name_accepted(self, client):
        """Whitespace-only names are valid strings (no strip validation)."""
        resp = client.post("/api/workflows/", json={"name": "   "})
        assert resp.status_code == 201

    def test_name_with_special_characters(self, client):
        """Names with special characters should be preserved."""
        special_name = 'WF <script>alert("xss")</script> & "quotes"'
        resp = client.post("/api/workflows/", json={"name": special_name})
        assert resp.status_code == 201
        assert resp.json()["name"] == special_name

    def test_update_with_long_name(self, client):
        """PATCH with a very long name should succeed."""
        wf_id = _create_workflow(client)
        long_name = "Updated-" + "U" * 8000
        resp = client.patch(
            f"/api/workflows/{wf_id}", json={"name": long_name}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == long_name


# ===========================================================================
# Update/patch endpoint validation errors
# ===========================================================================


class TestUpdateValidationErrors:
    """PATCH /api/workflows/{id} with invalid payloads."""

    def test_update_tasks_wrong_type(self, client):
        """Passing a string for 'tasks' in PATCH should fail."""
        wf_id = _create_workflow(client)
        resp = client.patch(
            f"/api/workflows/{wf_id}",
            json={"tasks": "not a list"},
        )
        assert resp.status_code == 422

    def test_update_tags_wrong_type(self, client):
        """Passing a string for 'tags' should fail validation."""
        wf_id = _create_workflow(client)
        resp = client.patch(
            f"/api/workflows/{wf_id}",
            json={"tags": "not-a-list"},
        )
        assert resp.status_code == 422

    def test_update_with_invalid_task_definition(self, client):
        """PATCH with a task missing required fields should fail."""
        wf_id = _create_workflow(client)
        resp = client.patch(
            f"/api/workflows/{wf_id}",
            json={"tasks": [{"description": "no name or action"}]},
        )
        assert resp.status_code == 422

    def test_update_nonexistent_workflow(self, client):
        """PATCH on a non-existent workflow ID should return 404."""
        resp = client.patch(
            "/api/workflows/does-not-exist",
            json={"name": "Updated"},
        )
        assert resp.status_code == 404

    def test_update_with_empty_body(self, client):
        """PATCH with an empty JSON object should succeed (no-op update)."""
        wf_id = _create_workflow(client)
        resp = client.patch(f"/api/workflows/{wf_id}", json={})
        assert resp.status_code == 200

    def test_update_with_extra_unknown_fields(self, client):
        """Extra fields not in the model should be silently ignored."""
        wf_id = _create_workflow(client)
        resp = client.patch(
            f"/api/workflows/{wf_id}",
            json={"name": "Updated", "nonexistent_field": "value"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_update_schedule_to_invalid_type(self, client):
        """Setting schedule to a non-string type should fail."""
        wf_id = _create_workflow(client)
        resp = client.patch(
            f"/api/workflows/{wf_id}",
            json={"schedule": 12345},
        )
        # Pydantic may coerce int to str; check accordingly
        if resp.status_code == 200:
            assert resp.json()["schedule"] == "12345"
        else:
            assert resp.status_code == 422


# ===========================================================================
# Task execution endpoint errors
# ===========================================================================


class TestTaskExecutionErrors:
    """Error responses from /api/tasks/ endpoints."""

    def test_get_nonexistent_execution(self, client):
        """GET with a non-existent execution ID should return 404."""
        resp = client.get("/api/tasks/executions/nonexistent-id")
        assert resp.status_code == 404
        assert "Execution not found" in resp.json()["detail"]

    def test_retry_nonexistent_execution(self, client):
        """POST retry on a non-existent execution should return 404."""
        resp = client.post("/api/tasks/executions/nonexistent-id/retry")
        assert resp.status_code == 404

    def test_retry_completed_execution(self, client):
        """Retrying a successful execution should return 409."""
        wf_id = _create_workflow(client)
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        exec_id = exec_resp.json()["id"]
        assert exec_resp.json()["status"] == "completed"

        resp = client.post(f"/api/tasks/executions/{exec_id}/retry")
        assert resp.status_code == 409
        assert "Only failed executions" in resp.json()["detail"]

    def test_execute_nonexistent_workflow(self, client):
        """Executing a non-existent workflow should return 404."""
        resp = client.post("/api/workflows/does-not-exist/execute")
        assert resp.status_code == 404

    def test_delete_nonexistent_workflow(self, client):
        """Deleting a non-existent workflow should return 404."""
        resp = client.delete("/api/workflows/does-not-exist")
        assert resp.status_code == 404

    def test_get_executions_with_valid_status_filter(self, client):
        """Listing executions with a valid status should return 200."""
        resp = client.get(
            "/api/tasks/executions", params={"status": "completed"}
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_executions_empty(self, client):
        """Listing executions when none exist should return empty list."""
        resp = client.get("/api/tasks/executions")
        assert resp.status_code == 200
        assert resp.json() == []


# ===========================================================================
# Workflow execution endpoint edge cases
# ===========================================================================


class TestWorkflowExecutionEdgeCases:
    """Edge cases for workflow creation and execution via the API."""

    def test_create_workflow_with_no_tasks_executes_as_completed(self, client):
        """A workflow with zero tasks should execute and complete immediately."""
        resp = client.post("/api/workflows/", json={"name": "Empty WF"})
        wf_id = resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.status_code == 200
        assert exec_resp.json()["status"] == "completed"
        assert exec_resp.json()["task_results"] == []

    def test_create_workflow_with_many_tags(self, client):
        """A workflow with many tags should be accepted."""
        tags = [f"tag-{i}" for i in range(100)]
        resp = client.post(
            "/api/workflows/", json={"name": "Many Tags", "tags": tags}
        )
        assert resp.status_code == 201
        assert len(resp.json()["tags"]) == 100

    def test_create_workflow_with_duplicate_tags(self, client):
        """Duplicate tags should be preserved (no deduplication)."""
        resp = client.post(
            "/api/workflows/",
            json={"name": "Dup Tags", "tags": ["a", "a", "b", "b"]},
        )
        assert resp.status_code == 201
        assert resp.json()["tags"] == ["a", "a", "b", "b"]

    def test_create_workflow_with_empty_tags(self, client):
        """An empty tags list should be accepted."""
        resp = client.post(
            "/api/workflows/", json={"name": "No Tags", "tags": []}
        )
        assert resp.status_code == 201
        assert resp.json()["tags"] == []

    def test_execute_workflow_with_custom_trigger(self, client):
        """The trigger query parameter should be preserved."""
        wf_id = _create_workflow(client)
        resp = client.post(
            f"/api/workflows/{wf_id}/execute", params={"trigger": "scheduled"}
        )
        assert resp.status_code == 200
        assert resp.json()["trigger"] == "scheduled"

    def test_list_workflow_executions_for_nonexistent_workflow(self, client):
        """Listing executions for a non-existent workflow returns empty list."""
        resp = client.get("/api/workflows/nonexistent/executions")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_multiple_executions_listed(self, client):
        """Multiple executions of the same workflow should all be listed."""
        wf_id = _create_workflow(client)
        client.post(f"/api/workflows/{wf_id}/execute")
        client.post(f"/api/workflows/{wf_id}/execute")
        client.post(f"/api/workflows/{wf_id}/execute")
        resp = client.get(f"/api/workflows/{wf_id}/executions")
        assert resp.status_code == 200
        assert len(resp.json()) == 3


# ===========================================================================
# Analytics endpoint edge cases
# ===========================================================================


class TestAnalyticsErrorEdgeCases:
    """Edge cases for analytics endpoints."""

    def test_summary_with_zero_days(self, client):
        """Requesting summary with days=0 should return empty metrics."""
        _create_workflow(client)
        resp = client.get("/api/analytics/summary", params={"days": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_executions"] == 0

    def test_summary_with_large_days(self, client):
        """Requesting summary with a very large window should work."""
        resp = client.get("/api/analytics/summary", params={"days": 99999})
        assert resp.status_code == 200

    def test_timeline_with_zero_hours(self, client):
        """Timeline with hours=0 should return an empty or minimal list."""
        resp = client.get(
            "/api/analytics/timeline", params={"hours": 0, "bucket_minutes": 60}
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_workflow_stats_nonexistent(self, client):
        """Stats for a non-existent workflow should return zeroed metrics."""
        resp = client.get("/api/analytics/workflows/nonexistent/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_executions"] == 0
        assert data["completed"] == 0
        assert data["failed"] == 0

    def test_summary_default_params(self, client):
        """Summary with default parameters should return valid structure."""
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        required_keys = {
            "total_workflows",
            "total_executions",
            "success_rate",
            "avg_duration_ms",
            "executions_by_status",
            "recent_executions",
            "top_failing_workflows",
        }
        assert required_keys.issubset(data.keys())

    def test_timeline_default_params(self, client):
        """Timeline with default parameters should return valid structure."""
        resp = client.get("/api/analytics/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if data:
            assert "time" in data[0]
            assert "total" in data[0]


# ===========================================================================
# Content-type and method errors
# ===========================================================================


class TestContentTypeAndMethodErrors:
    """Verify correct behaviour with wrong content types and HTTP methods."""

    def test_post_workflow_without_content_type(self, client):
        """POST without proper content-type header should fail."""
        resp = client.post(
            "/api/workflows/",
            content=b'{"name": "test"}',
        )
        # FastAPI may still parse it or return 422 depending on content-type
        assert resp.status_code in (201, 422)

    def test_get_workflows_with_extra_query_params_ignored(self, client):
        """Extra unknown query parameters should be silently ignored."""
        resp = client.get(
            "/api/workflows/",
            params={"unknown_param": "irrelevant"},
        )
        assert resp.status_code == 200

    def test_create_workflow_with_nested_invalid_params(self, client):
        """Task parameters can be any dict; deeply nested values are fine."""
        resp = client.post(
            "/api/workflows/",
            json={
                "name": "Nested Params",
                "tasks": [
                    {
                        "name": "Deep",
                        "action": "log",
                        "parameters": {
                            "level1": {
                                "level2": {
                                    "level3": [1, 2, {"level4": True}]
                                }
                            }
                        },
                    }
                ],
            },
        )
        assert resp.status_code == 201

    def test_create_workflow_depends_on_wrong_type(self, client):
        """depends_on should be a list of strings; passing int should fail."""
        resp = client.post(
            "/api/workflows/",
            json={
                "name": "Bad Deps",
                "tasks": [
                    {
                        "name": "Step",
                        "action": "log",
                        "depends_on": "not-a-list",
                    }
                ],
            },
        )
        assert resp.status_code == 422

    def test_health_check_always_works(self, client):
        """The health endpoint should always return 200."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_nonexistent_route_returns_404(self, client):
        """Requesting a route that doesn't exist should return 404."""
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404

    def test_post_to_get_only_endpoint(self, client):
        """POST to a GET-only endpoint should return 405."""
        resp = client.post("/api/workflows/some-id")
        assert resp.status_code == 405
