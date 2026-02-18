"""Tests for utility helpers."""

from datetime import datetime

from app.utils.helpers import (
    clamp,
    compute_checksum,
    format_duration,
    generate_slug,
    paginate,
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
