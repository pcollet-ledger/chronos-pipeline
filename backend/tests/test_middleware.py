"""Tests for the timing and tracing middleware.

Verifies that X-Request-ID and X-Response-Time headers are present
on every response, that timing values are reasonable, and that the
middleware works with all endpoint types.
"""

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.workflow_engine import clear_all


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    return TestClient(app)


UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
TIMING_PATTERN = re.compile(r"^\d+\.\d+ms$")


class TestRequestIdHeader:
    """Verify X-Request-ID is present and valid."""

    def test_health_has_request_id(self, client):
        resp = client.get("/health")
        assert "x-request-id" in resp.headers
        assert UUID_PATTERN.match(resp.headers["x-request-id"])

    def test_list_workflows_has_request_id(self, client):
        resp = client.get("/api/workflows/")
        assert "x-request-id" in resp.headers

    def test_create_workflow_has_request_id(self, client):
        resp = client.post("/api/workflows/", json={"name": "Test"})
        assert "x-request-id" in resp.headers

    def test_404_has_request_id(self, client):
        resp = client.get("/api/workflows/nonexistent")
        assert resp.status_code == 404
        assert "x-request-id" in resp.headers

    def test_each_request_gets_unique_id(self, client):
        resp1 = client.get("/health")
        resp2 = client.get("/health")
        assert resp1.headers["x-request-id"] != resp2.headers["x-request-id"]


class TestResponseTimeHeader:
    """Verify X-Response-Time is present and reasonable."""

    def test_health_has_response_time(self, client):
        resp = client.get("/health")
        assert "x-response-time" in resp.headers
        assert TIMING_PATTERN.match(resp.headers["x-response-time"])

    def test_response_time_is_positive(self, client):
        resp = client.get("/health")
        time_str = resp.headers["x-response-time"].replace("ms", "")
        assert float(time_str) >= 0

    def test_response_time_is_reasonable(self, client):
        resp = client.get("/health")
        time_str = resp.headers["x-response-time"].replace("ms", "")
        assert float(time_str) < 5000

    def test_list_workflows_has_response_time(self, client):
        resp = client.get("/api/workflows/")
        assert "x-response-time" in resp.headers

    def test_analytics_has_response_time(self, client):
        resp = client.get("/api/analytics/summary")
        assert "x-response-time" in resp.headers


class TestMiddlewareWithAllEndpoints:
    """Verify middleware works across all endpoint types."""

    def test_post_endpoint(self, client):
        resp = client.post("/api/workflows/", json={"name": "Test"})
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

    def test_get_endpoint(self, client):
        resp = client.get("/api/workflows/")
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

    def test_patch_endpoint(self, client):
        create_resp = client.post("/api/workflows/", json={"name": "Test"})
        wf_id = create_resp.json()["id"]
        resp = client.patch(f"/api/workflows/{wf_id}", json={"name": "Updated"})
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

    def test_delete_endpoint(self, client):
        create_resp = client.post("/api/workflows/", json={"name": "Test"})
        wf_id = create_resp.json()["id"]
        resp = client.delete(f"/api/workflows/{wf_id}")
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

    def test_error_response_has_headers(self, client):
        resp = client.get("/api/tasks/executions", params={"status": "invalid"})
        assert resp.status_code == 400
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

    def test_422_response_has_headers(self, client):
        resp = client.post("/api/workflows/", json={})
        assert resp.status_code == 422
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

    def test_bulk_delete_has_headers(self, client):
        resp = client.post("/api/workflows/bulk-delete", json={"ids": ["fake"]})
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

    def test_analytics_timeline_has_headers(self, client):
        resp = client.get("/api/analytics/timeline")
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

    def test_execution_list_has_headers(self, client):
        resp = client.get("/api/tasks/executions")
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers

    def test_response_time_format_consistent(self, client):
        """All endpoints should return timing in the same format."""
        for path in ["/health", "/api/workflows/", "/api/analytics/summary"]:
            resp = client.get(path)
            assert TIMING_PATTERN.match(resp.headers["x-response-time"])
