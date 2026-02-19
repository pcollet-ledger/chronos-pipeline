"""Comprehensive tests for global exception handlers registered in main.py.

Each handler is tested for: correct HTTP status, response body shape
(``{detail, code}``), specific detail/code values, logging behaviour,
edge cases (empty messages, nested exceptions), and interaction with
existing route-level error handling.

The test strategy uses ``app.dependency_overrides`` and mock routes to
trigger each exception type in isolation, without relying on real
service-layer bugs.
"""

import logging
from typing import Any, Dict
from unittest.mock import patch

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.main import app
from app.services.workflow_engine import clear_all


@pytest.fixture(autouse=True)
def cleanup():
    """Clear all in-memory state before and after each test."""
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    """Provide a ``TestClient`` bound to the application.

    Uses ``raise_server_exceptions=False`` so that unhandled exceptions
    are processed by the global exception handlers instead of being
    re-raised by the test client.
    """
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helper: register a temporary route that raises a specific exception
# ---------------------------------------------------------------------------

_test_router = APIRouter()


@_test_router.get("/_test/value-error")
async def _raise_value_error(msg: str = "bad value") -> None:
    raise ValueError(msg)


@_test_router.get("/_test/key-error")
async def _raise_key_error(key: str = "missing_key") -> None:
    raise KeyError(key)


@_test_router.get("/_test/permission-error")
async def _raise_permission_error(msg: str = "not allowed") -> None:
    raise PermissionError(msg)


@_test_router.get("/_test/generic-error")
async def _raise_generic_error(msg: str = "boom") -> None:
    raise RuntimeError(msg)


@_test_router.get("/_test/zero-division")
async def _raise_zero_division() -> Dict[str, Any]:
    return {"result": 1 / 0}


@_test_router.get("/_test/type-error")
async def _raise_type_error() -> None:
    raise TypeError("unsupported operand")


@_test_router.get("/_test/permission-error-empty")
async def _raise_permission_error_empty() -> None:
    raise PermissionError()


@_test_router.get("/_test/value-error-empty")
async def _raise_value_error_empty() -> None:
    raise ValueError()


@_test_router.get("/_test/key-error-int")
async def _raise_key_error_int() -> None:
    raise KeyError(42)


@_test_router.get("/_test/key-error-empty")
async def _raise_key_error_empty() -> None:
    raise KeyError()


app.include_router(_test_router)


# ===========================================================================
# ValueError handler (400)
# ===========================================================================


class TestValueErrorHandler:
    """Tests for the ``ValueError`` -> 400 global exception handler."""

    def test_returns_400_status(self, client: TestClient) -> None:
        """A bare ``ValueError`` should produce HTTP 400."""
        resp = client.get("/_test/value-error")
        assert resp.status_code == 400

    def test_response_has_detail_and_code(self, client: TestClient) -> None:
        """The response body must contain both ``detail`` and ``code``."""
        resp = client.get("/_test/value-error")
        body = resp.json()
        assert "detail" in body
        assert "code" in body

    def test_code_is_bad_request(self, client: TestClient) -> None:
        """The ``code`` field should be ``'bad_request'``."""
        resp = client.get("/_test/value-error")
        assert resp.json()["code"] == "bad_request"

    def test_detail_contains_message(self, client: TestClient) -> None:
        """The ``detail`` field should contain the exception message."""
        resp = client.get("/_test/value-error", params={"msg": "invalid input"})
        assert "invalid input" in resp.json()["detail"]

    def test_empty_message(self, client: TestClient) -> None:
        """A ``ValueError`` with no message should still return 400."""
        resp = client.get("/_test/value-error-empty")
        assert resp.status_code == 400
        assert resp.json()["code"] == "bad_request"

    def test_content_type_is_json(self, client: TestClient) -> None:
        """The response content-type should be ``application/json``."""
        resp = client.get("/_test/value-error")
        assert "application/json" in resp.headers["content-type"]

    def test_special_characters_in_message(self, client: TestClient) -> None:
        """Special characters in the message should be preserved."""
        resp = client.get("/_test/value-error", params={"msg": '<script>"xss"</script>'})
        assert resp.status_code == 400
        assert "<script>" in resp.json()["detail"]

    def test_long_message(self, client: TestClient) -> None:
        """A very long error message should be returned in full."""
        long_msg = "x" * 5000
        resp = client.get("/_test/value-error", params={"msg": long_msg})
        assert resp.status_code == 400
        assert len(resp.json()["detail"]) >= 5000

    def test_logs_warning(self, client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """The handler should log at WARNING level."""
        with caplog.at_level(logging.WARNING, logger="chronos_pipeline"):
            client.get("/_test/value-error", params={"msg": "logged value"})
        assert any("logged value" in r.message for r in caplog.records)

    def test_does_not_interfere_with_route_level_handling(self, client: TestClient) -> None:
        """Route-level ``ValueError`` catches (e.g. status filter) should
        still work via ``HTTPException``, not the global handler."""
        resp = client.get("/api/tasks/executions", params={"status": "bogus"})
        assert resp.status_code == 400
        assert "Invalid status" in resp.json()["detail"]


# ===========================================================================
# KeyError handler (404)
# ===========================================================================


class TestKeyErrorHandler:
    """Tests for the ``KeyError`` -> 404 global exception handler."""

    def test_returns_404_status(self, client: TestClient) -> None:
        """A bare ``KeyError`` should produce HTTP 404."""
        resp = client.get("/_test/key-error")
        assert resp.status_code == 404

    def test_response_has_detail_and_code(self, client: TestClient) -> None:
        """The response body must contain both ``detail`` and ``code``."""
        resp = client.get("/_test/key-error")
        body = resp.json()
        assert "detail" in body
        assert "code" in body

    def test_code_is_not_found(self, client: TestClient) -> None:
        """The ``code`` field should be ``'not_found'``."""
        resp = client.get("/_test/key-error")
        assert resp.json()["code"] == "not_found"

    def test_detail_contains_key_name(self, client: TestClient) -> None:
        """The ``detail`` field should mention the missing key."""
        resp = client.get("/_test/key-error", params={"key": "workflow_42"})
        assert "workflow_42" in resp.json()["detail"]

    def test_integer_key(self, client: TestClient) -> None:
        """A ``KeyError`` with an integer key should still return 404."""
        resp = client.get("/_test/key-error-int")
        assert resp.status_code == 404
        assert "42" in resp.json()["detail"]

    def test_empty_key(self, client: TestClient) -> None:
        """A ``KeyError`` with no arguments should return 404 with 'unknown'."""
        resp = client.get("/_test/key-error-empty")
        assert resp.status_code == 404
        assert "unknown" in resp.json()["detail"]

    def test_content_type_is_json(self, client: TestClient) -> None:
        """The response content-type should be ``application/json``."""
        resp = client.get("/_test/key-error")
        assert "application/json" in resp.headers["content-type"]

    def test_detail_starts_with_resource_not_found(self, client: TestClient) -> None:
        """The detail message should start with 'Resource not found:'."""
        resp = client.get("/_test/key-error")
        assert resp.json()["detail"].startswith("Resource not found:")

    def test_logs_warning(self, client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """The handler should log at WARNING level."""
        with caplog.at_level(logging.WARNING, logger="chronos_pipeline"):
            client.get("/_test/key-error", params={"key": "logged_key"})
        assert any("logged_key" in r.message for r in caplog.records)

    def test_does_not_interfere_with_route_404(self, client: TestClient) -> None:
        """Route-level 404s (via ``raise_not_found``) should still work."""
        resp = client.get("/api/workflows/nonexistent")
        assert resp.status_code == 404
        assert "Workflow not found" in resp.json()["detail"]


# ===========================================================================
# PermissionError handler (403)
# ===========================================================================


class TestPermissionErrorHandler:
    """Tests for the ``PermissionError`` -> 403 global exception handler."""

    def test_returns_403_status(self, client: TestClient) -> None:
        """A ``PermissionError`` should produce HTTP 403."""
        resp = client.get("/_test/permission-error")
        assert resp.status_code == 403

    def test_response_has_detail_and_code(self, client: TestClient) -> None:
        """The response body must contain both ``detail`` and ``code``."""
        resp = client.get("/_test/permission-error")
        body = resp.json()
        assert "detail" in body
        assert "code" in body

    def test_code_is_forbidden(self, client: TestClient) -> None:
        """The ``code`` field should be ``'forbidden'``."""
        resp = client.get("/_test/permission-error")
        assert resp.json()["code"] == "forbidden"

    def test_detail_contains_message(self, client: TestClient) -> None:
        """The ``detail`` field should contain the exception message."""
        resp = client.get("/_test/permission-error", params={"msg": "admin only"})
        assert "admin only" in resp.json()["detail"]

    def test_empty_message_uses_default(self, client: TestClient) -> None:
        """A ``PermissionError()`` with no message should use the fallback."""
        resp = client.get("/_test/permission-error-empty")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Permission denied"

    def test_content_type_is_json(self, client: TestClient) -> None:
        """The response content-type should be ``application/json``."""
        resp = client.get("/_test/permission-error")
        assert "application/json" in resp.headers["content-type"]

    def test_special_characters_in_message(self, client: TestClient) -> None:
        """Special characters in the message should be preserved."""
        resp = client.get("/_test/permission-error", params={"msg": "role='admin' required"})
        assert resp.status_code == 403
        assert "role='admin'" in resp.json()["detail"]

    def test_long_message(self, client: TestClient) -> None:
        """A very long permission error message should be returned in full."""
        long_msg = "denied-" * 1000
        resp = client.get("/_test/permission-error", params={"msg": long_msg})
        assert resp.status_code == 403
        assert len(resp.json()["detail"]) >= 7000

    def test_logs_warning(self, client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """The handler should log at WARNING level."""
        with caplog.at_level(logging.WARNING, logger="chronos_pipeline"):
            client.get("/_test/permission-error", params={"msg": "logged perm"})
        assert any("logged perm" in r.message for r in caplog.records)


# ===========================================================================
# Unhandled exception handler (500)
# ===========================================================================


class TestUnhandledExceptionHandler:
    """Tests for the catch-all ``Exception`` -> 500 global handler."""

    def test_returns_500_status(self, client: TestClient) -> None:
        """An unhandled ``RuntimeError`` should produce HTTP 500."""
        resp = client.get("/_test/generic-error")
        assert resp.status_code == 500

    def test_response_has_detail_and_code(self, client: TestClient) -> None:
        """The response body must contain both ``detail`` and ``code``."""
        resp = client.get("/_test/generic-error")
        body = resp.json()
        assert "detail" in body
        assert "code" in body

    def test_code_is_internal_server_error(self, client: TestClient) -> None:
        """The ``code`` field should be ``'internal_server_error'``."""
        resp = client.get("/_test/generic-error")
        assert resp.json()["code"] == "internal_server_error"

    def test_detail_is_generic(self, client: TestClient) -> None:
        """The detail should be generic to avoid leaking internals."""
        resp = client.get("/_test/generic-error", params={"msg": "secret info"})
        assert resp.json()["detail"] == "Internal server error"
        assert "secret info" not in resp.json()["detail"]

    def test_zero_division_returns_500(self, client: TestClient) -> None:
        """A ``ZeroDivisionError`` should be caught by the catch-all."""
        resp = client.get("/_test/zero-division")
        assert resp.status_code == 500
        assert resp.json()["code"] == "internal_server_error"

    def test_type_error_returns_500(self, client: TestClient) -> None:
        """A ``TypeError`` should be caught by the catch-all."""
        resp = client.get("/_test/type-error")
        assert resp.status_code == 500
        assert resp.json()["code"] == "internal_server_error"

    def test_content_type_is_json(self, client: TestClient) -> None:
        """The response content-type should be ``application/json``."""
        resp = client.get("/_test/generic-error")
        assert "application/json" in resp.headers["content-type"]

    def test_does_not_leak_exception_message(self, client: TestClient) -> None:
        """The original exception message must not appear in the response."""
        resp = client.get("/_test/generic-error", params={"msg": "database password is xyz"})
        body_text = resp.text
        assert "database password" not in body_text

    def test_logs_error(self, client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """The handler should log at ERROR level with the exception message."""
        with caplog.at_level(logging.ERROR, logger="chronos_pipeline"):
            client.get("/_test/generic-error", params={"msg": "logged boom"})
        assert any("logged boom" in r.message for r in caplog.records)

    def test_logs_traceback(self, client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
        """The log record should include the traceback."""
        with caplog.at_level(logging.ERROR, logger="chronos_pipeline"):
            client.get("/_test/generic-error")
        assert any("Traceback" in r.message or "RuntimeError" in r.message for r in caplog.records)


# ===========================================================================
# Response format consistency
# ===========================================================================


class TestErrorResponseFormat:
    """Verify that all exception handlers produce the same JSON shape."""

    @pytest.mark.parametrize(
        "path,expected_status",
        [
            ("/_test/value-error", 400),
            ("/_test/key-error", 404),
            ("/_test/permission-error", 403),
            ("/_test/generic-error", 500),
        ],
    )
    def test_all_handlers_return_detail_and_code(
        self, client: TestClient, path: str, expected_status: int
    ) -> None:
        """Every handler should return ``{detail: str, code: str}``."""
        resp = client.get(path)
        assert resp.status_code == expected_status
        body = resp.json()
        assert isinstance(body["detail"], str)
        assert isinstance(body["code"], str)

    @pytest.mark.parametrize(
        "path,expected_status",
        [
            ("/_test/value-error", 400),
            ("/_test/key-error", 404),
            ("/_test/permission-error", 403),
            ("/_test/generic-error", 500),
        ],
    )
    def test_all_handlers_return_json_content_type(
        self, client: TestClient, path: str, expected_status: int
    ) -> None:
        """Every handler should set ``application/json`` content-type."""
        resp = client.get(path)
        assert "application/json" in resp.headers["content-type"]

    def test_body_has_exactly_two_keys(self, client: TestClient) -> None:
        """The error body should contain only ``detail`` and ``code``."""
        resp = client.get("/_test/generic-error")
        assert set(resp.json().keys()) == {"detail", "code"}


# ===========================================================================
# Integration: exception handlers + existing features
# ===========================================================================


class TestExceptionHandlerIntegration:
    """Verify that global exception handlers coexist correctly with
    route-level error handling across all existing feature areas."""

    def test_workflow_not_found_still_returns_404(self, client: TestClient) -> None:
        """Route-level 404 for missing workflow should still work."""
        resp = client.get("/api/workflows/nonexistent-id")
        assert resp.status_code == 404
        assert "Workflow not found" in resp.json()["detail"]

    def test_execution_not_found_still_returns_404(self, client: TestClient) -> None:
        """Route-level 404 for missing execution should still work."""
        resp = client.get("/api/tasks/executions/nonexistent-id")
        assert resp.status_code == 404
        assert "Execution not found" in resp.json()["detail"]

    def test_retry_conflict_still_returns_409(self, client: TestClient) -> None:
        """Retrying a completed execution should still return 409."""
        wf_resp = client.post("/api/workflows/", json={
            "name": "Good WF",
            "tasks": [{"name": "Log", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = wf_resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        exec_id = exec_resp.json()["id"]
        assert exec_resp.json()["status"] == "completed"

        resp = client.post(f"/api/tasks/executions/{exec_id}/retry")
        assert resp.status_code == 409
        assert "Only failed executions" in resp.json()["detail"]

    def test_invalid_status_filter_still_returns_400(self, client: TestClient) -> None:
        """The route-level 400 for invalid status filter should still work."""
        resp = client.get("/api/tasks/executions", params={"status": "bogus"})
        assert resp.status_code == 400
        assert "Invalid status" in resp.json()["detail"]

    def test_pydantic_validation_still_returns_422(self, client: TestClient) -> None:
        """Pydantic validation errors should still return 422, not 400."""
        resp = client.post("/api/workflows/", json={"description": "no name"})
        assert resp.status_code == 422

    def test_health_endpoint_unaffected(self, client: TestClient) -> None:
        """The health check should still work normally."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_workflow_crud_unaffected(self, client: TestClient) -> None:
        """Full CRUD cycle should work without triggering global handlers."""
        create_resp = client.post("/api/workflows/", json={"name": "CRUD Test"})
        assert create_resp.status_code == 201
        wf_id = create_resp.json()["id"]

        get_resp = client.get(f"/api/workflows/{wf_id}")
        assert get_resp.status_code == 200

        patch_resp = client.patch(f"/api/workflows/{wf_id}", json={"name": "Updated"})
        assert patch_resp.status_code == 200
        assert patch_resp.json()["name"] == "Updated"

        del_resp = client.delete(f"/api/workflows/{wf_id}")
        assert del_resp.status_code == 204

    def test_analytics_unaffected(self, client: TestClient) -> None:
        """Analytics endpoints should work without triggering global handlers."""
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 200
        assert "total_workflows" in resp.json()

    def test_execution_flow_unaffected(self, client: TestClient) -> None:
        """A full create -> execute -> list flow should work normally."""
        wf_resp = client.post("/api/workflows/", json={
            "name": "Exec Test",
            "tasks": [{"name": "Log", "action": "log", "parameters": {"message": "ok"}}],
        })
        wf_id = wf_resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        assert exec_resp.status_code == 200
        assert exec_resp.json()["status"] == "completed"

        list_resp = client.get("/api/tasks/executions")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1

    def test_bulk_delete_unaffected(self, client: TestClient) -> None:
        """Bulk delete should work without triggering global handlers."""
        wf1 = client.post("/api/workflows/", json={"name": "WF1"}).json()["id"]
        wf2 = client.post("/api/workflows/", json={"name": "WF2"}).json()["id"]
        resp = client.post("/api/workflows/bulk-delete", json={"ids": [wf1, wf2]})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 2

    def test_delete_nonexistent_workflow_still_404(self, client: TestClient) -> None:
        """Deleting a non-existent workflow should return 404."""
        resp = client.delete("/api/workflows/does-not-exist")
        assert resp.status_code == 404

    def test_retry_deleted_workflow_still_409(self, client: TestClient) -> None:
        """Retrying an execution whose workflow was deleted should return 409."""
        wf_resp = client.post("/api/workflows/", json={
            "name": "Delete Me",
            "tasks": [{"name": "Bad", "action": "unknown_action", "parameters": {}}],
        })
        wf_id = wf_resp.json()["id"]
        exec_resp = client.post(f"/api/workflows/{wf_id}/execute")
        exec_id = exec_resp.json()["id"]
        assert exec_resp.json()["status"] == "failed"

        client.delete(f"/api/workflows/{wf_id}")
        resp = client.post(f"/api/tasks/executions/{exec_id}/retry")
        assert resp.status_code == 409
        assert "no longer exists" in resp.json()["detail"]
