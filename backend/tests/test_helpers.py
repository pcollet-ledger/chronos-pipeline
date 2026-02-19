"""Tests for utility helpers.

Covers all public functions in ``app.utils.helpers`` including the new
``raise_not_found``, ``raise_conflict``, and ``build_error_response``
helpers used by routes and global exception handlers.
"""

import json
from datetime import datetime

import pytest
from fastapi import HTTPException

from app.utils.helpers import (
    build_error_response,
    clamp,
    compute_checksum,
    format_duration,
    generate_slug,
    paginate,
    raise_conflict,
    raise_not_found,
    safe_get,
    timestamp_to_iso,
)


class TestGenerateSlug:
    def test_basic(self):
        assert generate_slug("Hello World") == "hello-world"

    def test_special_chars(self):
        assert generate_slug("My Workflow! (v2)") == "my-workflow-v2"

    def test_multiple_spaces(self):
        assert generate_slug("too   many   spaces") == "too-many-spaces"

    def test_already_slug(self):
        assert generate_slug("already-a-slug") == "already-a-slug"


class TestComputeChecksum:
    def test_deterministic(self):
        a = compute_checksum("hello")
        b = compute_checksum("hello")
        assert a == b

    def test_different_inputs(self):
        a = compute_checksum("hello")
        b = compute_checksum("world")
        assert a != b


class TestPaginate:
    def test_basic(self):
        items = list(range(100))
        result = paginate(items, offset=0, limit=10)
        assert len(result["items"]) == 10
        assert result["total"] == 100
        assert result["has_more"] is True

    def test_last_page(self):
        items = list(range(25))
        result = paginate(items, offset=20, limit=10)
        assert len(result["items"]) == 5
        assert result["has_more"] is False

    def test_empty(self):
        result = paginate([], offset=0, limit=10)
        assert result["items"] == []
        assert result["total"] == 0


class TestFormatDuration:
    def test_milliseconds(self):
        assert format_duration(500) == "500ms"

    def test_seconds(self):
        assert format_duration(5000) == "5.0s"

    def test_minutes(self):
        assert format_duration(120000) == "2.0m"

    def test_hours(self):
        assert format_duration(7200000) == "2.0h"


class TestSafeGet:
    def test_nested(self):
        data = {"a": {"b": {"c": 42}}}
        assert safe_get(data, "a", "b", "c") == 42

    def test_missing_key(self):
        data = {"a": {"b": 1}}
        assert safe_get(data, "a", "x", default="nope") == "nope"

    def test_none_value(self):
        data = {"a": None}
        assert safe_get(data, "a", "b", default="fallback") == "fallback"


class TestTimestampToIso:
    def test_with_datetime(self):
        dt = datetime(2026, 1, 15, 10, 30, 0)
        assert timestamp_to_iso(dt) == "2026-01-15T10:30:00Z"

    def test_none(self):
        assert timestamp_to_iso(None) is None


class TestClamp:
    def test_within_range(self):
        assert clamp(5, 0, 10) == 5

    def test_below_min(self):
        assert clamp(-5, 0, 10) == 0

    def test_above_max(self):
        assert clamp(15, 0, 10) == 10


class TestRaiseNotFound:
    """Tests for the ``raise_not_found`` helper."""

    def test_raises_http_exception(self):
        with pytest.raises(HTTPException):
            raise_not_found()

    def test_status_code_is_404(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found()
        assert exc_info.value.status_code == 404

    def test_default_detail_message(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found()
        assert exc_info.value.detail == "Resource not found"

    def test_custom_resource_name(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found("Workflow")
        assert exc_info.value.detail == "Workflow not found"

    def test_empty_resource_name(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found("")
        assert exc_info.value.detail == " not found"

    def test_special_characters_in_resource(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found("Workflow<>")
        assert "Workflow<>" in exc_info.value.detail

    def test_long_resource_name(self):
        long_name = "R" * 1000
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found(long_name)
        assert long_name in exc_info.value.detail

    def test_unicode_resource_name(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found("ワークフロー")
        assert "ワークフロー" in exc_info.value.detail


class TestRaiseConflict:
    """Tests for the ``raise_conflict`` helper."""

    def test_raises_http_exception(self):
        with pytest.raises(HTTPException):
            raise_conflict("conflict")

    def test_status_code_is_409(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict("conflict")
        assert exc_info.value.status_code == 409

    def test_detail_matches_message(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict("Only failed executions can be retried")
        assert exc_info.value.detail == "Only failed executions can be retried"

    def test_empty_message(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict("")
        assert exc_info.value.detail == ""

    def test_special_characters(self):
        msg = 'Status is "completed" — cannot retry'
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict(msg)
        assert exc_info.value.detail == msg

    def test_long_message(self):
        long_msg = "x" * 5000
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict(long_msg)
        assert len(exc_info.value.detail) == 5000

    def test_unicode_message(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict("再試行できません")
        assert "再試行" in exc_info.value.detail

    def test_multiline_message(self):
        msg = "line1\nline2\nline3"
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict(msg)
        assert "\n" in exc_info.value.detail


class TestBuildErrorResponse:
    """Tests for the ``build_error_response`` helper."""

    def test_returns_json_response(self):
        resp = build_error_response(500, "error", "internal_server_error")
        assert resp.status_code == 500

    def test_body_has_detail_and_code(self):
        resp = build_error_response(400, "bad input", "bad_request")
        body = json.loads(resp.body)
        assert body["detail"] == "bad input"
        assert body["code"] == "bad_request"

    def test_status_code_is_set(self):
        resp = build_error_response(403, "denied", "forbidden")
        assert resp.status_code == 403

    def test_404_response(self):
        resp = build_error_response(404, "not found", "not_found")
        body = json.loads(resp.body)
        assert resp.status_code == 404
        assert body["code"] == "not_found"

    def test_content_type_is_json(self):
        resp = build_error_response(500, "error", "internal_server_error")
        content_type = dict(resp.headers).get("content-type", "")
        assert "application/json" in content_type

    def test_empty_detail(self):
        resp = build_error_response(500, "", "internal_server_error")
        body = json.loads(resp.body)
        assert body["detail"] == ""

    def test_empty_code(self):
        resp = build_error_response(500, "error", "")
        body = json.loads(resp.body)
        assert body["code"] == ""

    def test_body_has_exactly_two_keys(self):
        resp = build_error_response(500, "error", "code")
        body = json.loads(resp.body)
        assert set(body.keys()) == {"detail", "code"}
