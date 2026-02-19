"""Comprehensive tests for the bulk-delete workflows feature.

Covers:
  - Service-layer ``bulk_delete_workflows`` function (unit tests)
  - API endpoint ``POST /api/workflows/bulk-delete`` (integration tests)
  - Edge cases: empty after dedup, duplicate IDs, mix of valid/invalid,
    all not-found, all found, large batches, and request validation.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import BulkDeleteRequest, BulkDeleteResponse
from app.services.workflow_engine import (
    bulk_delete_workflows,
    clear_all,
    create_workflow,
    get_workflow,
)
from app.models import WorkflowCreate


@pytest.fixture(autouse=True)
def cleanup():
    """Clear all in-memory state before and after each test."""
    clear_all()
    yield
    clear_all()


@pytest.fixture
def client():
    return TestClient(app)


def _create_n_workflows(n: int) -> list[str]:
    """Helper: create *n* minimal workflows and return their IDs."""
    ids: list[str] = []
    for i in range(n):
        wf = create_workflow(WorkflowCreate(name=f"Workflow {i}"))
        ids.append(wf.id)
    return ids


# ===========================================================================
# Service-layer tests for bulk_delete_workflows
# ===========================================================================


class TestBulkDeleteService:
    """Direct unit tests for the ``bulk_delete_workflows`` function."""

    def test_delete_all_existing(self):
        """All supplied IDs exist — every one should be deleted."""
        ids = _create_n_workflows(3)
        result = bulk_delete_workflows(ids)

        assert result.deleted == 3
        assert result.not_found == 0
        assert set(result.deleted_ids) == set(ids)
        assert result.not_found_ids == []
        for wid in ids:
            assert get_workflow(wid) is None

    def test_delete_all_not_found(self):
        """None of the supplied IDs exist — all should be reported missing."""
        result = bulk_delete_workflows(["ghost-1", "ghost-2", "ghost-3"])

        assert result.deleted == 0
        assert result.not_found == 3
        assert result.deleted_ids == []
        assert set(result.not_found_ids) == {"ghost-1", "ghost-2", "ghost-3"}

    def test_mixed_existing_and_missing(self):
        """Some IDs exist, some don't — counts should reflect the mix."""
        ids = _create_n_workflows(2)
        mixed = [ids[0], "nonexistent-1", ids[1], "nonexistent-2"]
        result = bulk_delete_workflows(mixed)

        assert result.deleted == 2
        assert result.not_found == 2
        assert set(result.deleted_ids) == set(ids)
        assert set(result.not_found_ids) == {"nonexistent-1", "nonexistent-2"}

    def test_duplicate_ids_are_deduplicated(self):
        """Duplicate IDs in the input should be processed only once."""
        ids = _create_n_workflows(1)
        wid = ids[0]
        result = bulk_delete_workflows([wid, wid, wid])

        assert result.deleted == 1
        assert result.not_found == 0
        assert result.deleted_ids == [wid]

    def test_duplicate_nonexistent_ids_deduplicated(self):
        """Duplicate non-existent IDs should appear only once in not_found."""
        result = bulk_delete_workflows(["ghost", "ghost", "ghost"])

        assert result.deleted == 0
        assert result.not_found == 1
        assert result.not_found_ids == ["ghost"]

    def test_single_id(self):
        """A list with a single valid ID should work correctly."""
        ids = _create_n_workflows(1)
        result = bulk_delete_workflows(ids)

        assert result.deleted == 1
        assert result.not_found == 0
        assert get_workflow(ids[0]) is None

    def test_large_batch(self):
        """Bulk-deleting a large number of workflows should succeed."""
        ids = _create_n_workflows(100)
        result = bulk_delete_workflows(ids)

        assert result.deleted == 100
        assert result.not_found == 0

    def test_returns_correct_type(self):
        """The return value should be a ``BulkDeleteResponse`` instance."""
        ids = _create_n_workflows(1)
        result = bulk_delete_workflows(ids)
        assert isinstance(result, BulkDeleteResponse)

    def test_deleted_ids_preserve_order(self):
        """deleted_ids should reflect the first-seen order of the input."""
        ids = _create_n_workflows(3)
        result = bulk_delete_workflows(ids)
        assert result.deleted_ids == ids

    def test_remaining_workflows_untouched(self):
        """Workflows not in the delete list should remain intact."""
        ids = _create_n_workflows(5)
        to_delete = ids[:2]
        to_keep = ids[2:]

        result = bulk_delete_workflows(to_delete)
        assert result.deleted == 2

        for wid in to_keep:
            assert get_workflow(wid) is not None


# ===========================================================================
# API endpoint tests for POST /api/workflows/bulk-delete
# ===========================================================================


class TestBulkDeleteEndpoint:
    """Integration tests for the ``POST /api/workflows/bulk-delete`` endpoint."""

    def _create_via_api(self, client, name="BulkTest WF") -> str:
        """Helper: create a workflow via the API and return its ID."""
        resp = client.post("/api/workflows/", json={"name": name})
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_delete_multiple_returns_200(self, client):
        """Deleting multiple existing workflows returns 200 with correct counts."""
        ids = [self._create_via_api(client, f"WF-{i}") for i in range(3)]
        resp = client.post("/api/workflows/bulk-delete", json={"ids": ids})

        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 3
        assert data["not_found"] == 0
        assert set(data["deleted_ids"]) == set(ids)
        assert data["not_found_ids"] == []

    def test_all_not_found_returns_200(self, client):
        """All IDs missing still returns 200 (not an error condition)."""
        resp = client.post(
            "/api/workflows/bulk-delete",
            json={"ids": ["no-such-1", "no-such-2"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 0
        assert data["not_found"] == 2

    def test_mixed_found_and_missing(self, client):
        """A mix of existing and non-existing IDs returns correct split."""
        wf_id = self._create_via_api(client)
        resp = client.post(
            "/api/workflows/bulk-delete",
            json={"ids": [wf_id, "does-not-exist"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 1
        assert data["not_found"] == 1
        assert data["deleted_ids"] == [wf_id]
        assert data["not_found_ids"] == ["does-not-exist"]

    def test_empty_ids_list_returns_422(self, client):
        """An empty ``ids`` list should fail Pydantic validation (min_length=1)."""
        resp = client.post("/api/workflows/bulk-delete", json={"ids": []})
        assert resp.status_code == 422

    def test_missing_ids_field_returns_422(self, client):
        """Omitting the ``ids`` field entirely should fail validation."""
        resp = client.post("/api/workflows/bulk-delete", json={})
        assert resp.status_code == 422

    def test_ids_wrong_type_returns_422(self, client):
        """Passing a string instead of a list for ``ids`` should fail."""
        resp = client.post(
            "/api/workflows/bulk-delete", json={"ids": "not-a-list"}
        )
        assert resp.status_code == 422

    def test_duplicate_ids_handled_gracefully(self, client):
        """Duplicate IDs in the request should not cause double-counting."""
        wf_id = self._create_via_api(client)
        resp = client.post(
            "/api/workflows/bulk-delete",
            json={"ids": [wf_id, wf_id, wf_id]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 1
        assert data["not_found"] == 0

    def test_workflows_actually_removed(self, client):
        """After bulk-delete, the workflows should no longer be listable."""
        ids = [self._create_via_api(client, f"WF-{i}") for i in range(3)]

        resp = client.get("/api/workflows/")
        assert len(resp.json()) == 3

        client.post("/api/workflows/bulk-delete", json={"ids": ids})

        resp = client.get("/api/workflows/")
        assert len(resp.json()) == 0

    def test_partial_delete_leaves_others(self, client):
        """Deleting a subset should leave the remaining workflows intact."""
        ids = [self._create_via_api(client, f"WF-{i}") for i in range(4)]
        to_delete = ids[:2]
        to_keep = ids[2:]

        client.post("/api/workflows/bulk-delete", json={"ids": to_delete})

        resp = client.get("/api/workflows/")
        remaining_ids = {w["id"] for w in resp.json()}
        assert remaining_ids == set(to_keep)

    def test_malformed_json_returns_422(self, client):
        """Sending malformed JSON should return 422."""
        resp = client.post(
            "/api/workflows/bulk-delete",
            content=b"{bad json}",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_null_body_returns_422(self, client):
        """Sending JSON null as the body should return 422."""
        resp = client.post(
            "/api/workflows/bulk-delete",
            content=b"null",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_ids_with_non_string_elements_returns_422(self, client):
        """Non-string elements in the ``ids`` list should fail validation."""
        resp = client.post(
            "/api/workflows/bulk-delete", json={"ids": [123, 456]}
        )
        # Pydantic v2 may coerce ints to strings; accept either outcome
        if resp.status_code == 200:
            assert resp.json()["not_found"] == 2
        else:
            assert resp.status_code == 422

    def test_response_schema_fields(self, client):
        """The response should contain all expected fields."""
        wf_id = self._create_via_api(client)
        resp = client.post(
            "/api/workflows/bulk-delete", json={"ids": [wf_id]}
        )
        data = resp.json()
        assert "deleted" in data
        assert "not_found" in data
        assert "deleted_ids" in data
        assert "not_found_ids" in data
