"""Exhaustive tests for the validators module.

Covers every public function with happy path, error paths, boundary
values, empty input, and edge cases.
"""

import pytest

from app.utils.validators import (
    MAX_LIMIT,
    MAX_TAG_LENGTH,
    MAX_TAGS_COUNT,
    MAX_WORKFLOW_NAME_LENGTH,
    MIN_LIMIT,
    VALID_ACTIONS,
    is_valid_slug,
    is_valid_uuid,
    validate_action_name,
    validate_limit,
    validate_offset,
    validate_positive_int,
    validate_tags,
    validate_workflow_name,
)


class TestValidateWorkflowName:
    def test_valid_name(self):
        assert validate_workflow_name("My Workflow") is None

    def test_empty_name(self):
        assert validate_workflow_name("") is not None

    def test_whitespace_only(self):
        assert validate_workflow_name("   ") is not None

    def test_max_length_name(self):
        assert validate_workflow_name("A" * MAX_WORKFLOW_NAME_LENGTH) is None

    def test_over_max_length(self):
        result = validate_workflow_name("A" * (MAX_WORKFLOW_NAME_LENGTH + 1))
        assert result is not None
        assert str(MAX_WORKFLOW_NAME_LENGTH) in result

    def test_single_char(self):
        assert validate_workflow_name("X") is None

    def test_unicode_name(self):
        assert validate_workflow_name("工作流程") is None

    def test_name_with_special_chars(self):
        assert validate_workflow_name("WF <test> & 'quotes'") is None

    def test_name_with_newlines(self):
        assert validate_workflow_name("WF\nwith\nnewlines") is None

    def test_exactly_max_length(self):
        assert validate_workflow_name("B" * MAX_WORKFLOW_NAME_LENGTH) is None

    def test_one_over_max(self):
        assert validate_workflow_name("B" * (MAX_WORKFLOW_NAME_LENGTH + 1)) is not None


class TestValidateActionName:
    def test_valid_actions(self):
        for action in VALID_ACTIONS:
            assert validate_action_name(action) is None

    def test_unknown_action(self):
        result = validate_action_name("unknown")
        assert result is not None
        assert "unknown" in result.lower() or "Unknown" in result

    def test_empty_action(self):
        assert validate_action_name("") is not None

    def test_case_sensitive(self):
        assert validate_action_name("Log") is not None
        assert validate_action_name("LOG") is not None

    def test_action_with_spaces(self):
        assert validate_action_name(" log ") is not None

    def test_all_five_actions(self):
        assert len(VALID_ACTIONS) == 5
        for a in ["log", "transform", "validate", "notify", "aggregate"]:
            assert a in VALID_ACTIONS


class TestValidateTags:
    def test_valid_tags(self):
        assert validate_tags(["alpha", "beta"]) is None

    def test_empty_list(self):
        assert validate_tags([]) is None

    def test_too_many_tags(self):
        tags = [f"tag-{i}" for i in range(MAX_TAGS_COUNT + 1)]
        result = validate_tags(tags)
        assert result is not None

    def test_exactly_max_tags(self):
        tags = [f"tag-{i}" for i in range(MAX_TAGS_COUNT)]
        assert validate_tags(tags) is None

    def test_tag_too_long(self):
        tags = ["A" * (MAX_TAG_LENGTH + 1)]
        result = validate_tags(tags)
        assert result is not None

    def test_tag_exactly_max_length(self):
        tags = ["A" * MAX_TAG_LENGTH]
        assert validate_tags(tags) is None

    def test_single_tag(self):
        assert validate_tags(["single"]) is None

    def test_duplicate_tags(self):
        assert validate_tags(["a", "a", "b"]) is None

    def test_empty_string_tag(self):
        assert validate_tags([""]) is None

    def test_unicode_tags(self):
        assert validate_tags(["日本語", "한국어"]) is None


class TestValidateLimit:
    def test_valid_limit(self):
        assert validate_limit(50) is None

    def test_min_limit(self):
        assert validate_limit(MIN_LIMIT) is None

    def test_max_limit(self):
        assert validate_limit(MAX_LIMIT) is None

    def test_below_min(self):
        assert validate_limit(0) is not None

    def test_above_max(self):
        assert validate_limit(MAX_LIMIT + 1) is not None

    def test_negative(self):
        assert validate_limit(-1) is not None


class TestValidateOffset:
    def test_valid_offset(self):
        assert validate_offset(0) is None

    def test_positive_offset(self):
        assert validate_offset(100) is None

    def test_negative_offset(self):
        assert validate_offset(-1) is not None


class TestValidatePositiveInt:
    def test_zero(self):
        assert validate_positive_int(0, "value") is None

    def test_positive(self):
        assert validate_positive_int(42, "value") is None

    def test_negative(self):
        result = validate_positive_int(-1, "days")
        assert result is not None
        assert "days" in result

    def test_large_value(self):
        assert validate_positive_int(999999, "big") is None


class TestIsValidUuid:
    def test_valid_uuid(self):
        assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_uppercase_uuid(self):
        assert is_valid_uuid("550E8400-E29B-41D4-A716-446655440000") is True

    def test_invalid_uuid(self):
        assert is_valid_uuid("not-a-uuid") is False

    def test_empty_string(self):
        assert is_valid_uuid("") is False

    def test_partial_uuid(self):
        assert is_valid_uuid("550e8400-e29b") is False

    def test_uuid_without_dashes(self):
        assert is_valid_uuid("550e8400e29b41d4a716446655440000") is False


class TestIsValidSlug:
    def test_valid_slug(self):
        assert is_valid_slug("my-workflow") is True

    def test_single_word(self):
        assert is_valid_slug("workflow") is True

    def test_with_numbers(self):
        assert is_valid_slug("workflow-v2") is True

    def test_uppercase_invalid(self):
        assert is_valid_slug("My-Workflow") is False

    def test_spaces_invalid(self):
        assert is_valid_slug("my workflow") is False

    def test_empty_string(self):
        assert is_valid_slug("") is False

    def test_leading_dash(self):
        assert is_valid_slug("-workflow") is False

    def test_trailing_dash(self):
        assert is_valid_slug("workflow-") is False

    def test_consecutive_dashes(self):
        assert is_valid_slug("my--workflow") is False

    def test_numbers_only(self):
        assert is_valid_slug("123") is True
