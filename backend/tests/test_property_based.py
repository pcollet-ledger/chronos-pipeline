"""Property-based tests using Hypothesis.

Validates invariants that must hold for all valid inputs, not just
hand-picked examples.
"""

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.utils.helpers import (
    clamp,
    compute_checksum,
    format_duration,
    generate_slug,
    paginate,
    safe_get,
)
from app.utils.validators import (
    validate_workflow_name,
    validate_action_name,
    validate_tags,
    validate_limit,
    validate_offset,
    validate_non_negative_int,
    is_valid_uuid,
    is_valid_slug,
    VALID_ACTIONS,
    MAX_WORKFLOW_NAME_LENGTH,
    MAX_TAG_LENGTH,
    MAX_TAGS_COUNT,
    MIN_LIMIT,
    MAX_LIMIT,
)
from app.utils.formatters import (
    format_duration as fmt_duration,
    format_timestamp,
)
from app.models import TaskDefinition, WorkflowCreate, WorkflowStatus
from app.services.workflow_engine import (
    _topological_sort,
    clear_all,
    create_workflow,
    execute_workflow,
    get_workflow,
    delete_workflow,
    list_workflows,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    yield
    clear_all()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestGenerateSlugProperties:
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_slug_is_lowercase(self, name: str):
        slug = generate_slug(name)
        assert slug == slug.lower()

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_slug_has_no_consecutive_dashes(self, name: str):
        slug = generate_slug(name)
        assert "--" not in slug

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_slug_no_leading_trailing_dashes(self, name: str):
        slug = generate_slug(name)
        if slug:
            assert not slug.startswith("-")
            assert not slug.endswith("-")


class TestComputeChecksumProperties:
    @given(st.text(min_size=0, max_size=500))
    @settings(max_examples=50)
    def test_checksum_is_deterministic(self, data: str):
        assert compute_checksum(data) == compute_checksum(data)

    @given(st.text(min_size=0, max_size=500))
    @settings(max_examples=50)
    def test_checksum_is_64_hex_chars(self, data: str):
        cs = compute_checksum(data)
        assert len(cs) == 64
        assert all(c in "0123456789abcdef" for c in cs)


class TestClampProperties:
    @given(
        st.floats(allow_nan=False, allow_infinity=False),
        st.floats(allow_nan=False, allow_infinity=False),
        st.floats(allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_clamp_within_bounds(self, value: float, lo: float, hi: float):
        assume(lo <= hi)
        result = clamp(value, lo, hi)
        assert lo <= result <= hi

    @given(
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
        st.floats(min_value=-1e6, max_value=0, allow_nan=False),
        st.floats(min_value=0, max_value=1e6, allow_nan=False),
    )
    @settings(max_examples=50)
    def test_clamp_identity_when_in_range(self, value: float, lo: float, hi: float):
        assume(lo <= hi)
        assume(lo <= value <= hi)
        assert clamp(value, lo, hi) == value


class TestPaginateProperties:
    @given(
        st.lists(st.integers(), min_size=0, max_size=200),
        st.integers(min_value=0, max_value=200),
        st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50)
    def test_paginate_total_is_correct(self, items: list, offset: int, limit: int):
        result = paginate(items, offset=offset, limit=limit)
        assert result["total"] == len(items)

    @given(
        st.lists(st.integers(), min_size=0, max_size=200),
        st.integers(min_value=0, max_value=200),
        st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50)
    def test_paginate_items_within_limit(self, items: list, offset: int, limit: int):
        result = paginate(items, offset=offset, limit=limit)
        assert len(result["items"]) <= limit

    @given(
        st.lists(st.integers(), min_size=0, max_size=200),
        st.integers(min_value=0, max_value=200),
        st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50)
    def test_paginate_has_more_consistency(self, items: list, offset: int, limit: int):
        result = paginate(items, offset=offset, limit=limit)
        expected_has_more = (offset + limit) < len(items)
        assert result["has_more"] == expected_has_more


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

class TestValidateWorkflowNameProperties:
    @given(st.text(min_size=1, max_size=MAX_WORKFLOW_NAME_LENGTH).filter(lambda s: s.strip()))
    @settings(max_examples=50)
    def test_valid_names_pass(self, name: str):
        assert validate_workflow_name(name) is None

    @given(st.text(min_size=MAX_WORKFLOW_NAME_LENGTH + 1, max_size=MAX_WORKFLOW_NAME_LENGTH + 50))
    @settings(max_examples=20)
    def test_over_max_length_fails(self, name: str):
        assert validate_workflow_name(name) is not None


class TestValidateLimitProperties:
    @given(st.integers(min_value=MIN_LIMIT, max_value=MAX_LIMIT))
    @settings(max_examples=50)
    def test_valid_limits_pass(self, limit: int):
        assert validate_limit(limit) is None

    @given(st.integers(max_value=MIN_LIMIT - 1))
    @settings(max_examples=20)
    def test_below_min_fails(self, limit: int):
        assert validate_limit(limit) is not None

    @given(st.integers(min_value=MAX_LIMIT + 1, max_value=MAX_LIMIT + 1000))
    @settings(max_examples=20)
    def test_above_max_fails(self, limit: int):
        assert validate_limit(limit) is not None


class TestValidateOffsetProperties:
    @given(st.integers(min_value=0, max_value=100000))
    @settings(max_examples=50)
    def test_non_negative_offsets_pass(self, offset: int):
        assert validate_offset(offset) is None

    @given(st.integers(max_value=-1))
    @settings(max_examples=20)
    def test_negative_offsets_fail(self, offset: int):
        assert validate_offset(offset) is not None


class TestValidateNonNegativeIntProperties:
    @given(st.integers(min_value=0, max_value=1000000))
    @settings(max_examples=50)
    def test_non_negative_passes(self, value: int):
        assert validate_non_negative_int(value, "x") is None

    @given(st.integers(max_value=-1))
    @settings(max_examples=20)
    def test_negative_fails(self, value: int):
        result = validate_non_negative_int(value, "x")
        assert result is not None
        assert "x" in result


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

class TestFormatDurationProperties:
    @given(st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
    @settings(max_examples=50)
    def test_format_duration_returns_string(self, ms: float):
        result = fmt_duration(ms)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_duration_none_returns_na(self):
        assert fmt_duration(None) == "N/A"

    @given(st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False))
    @settings(max_examples=20)
    def test_format_duration_negative_returns_zero(self, ms: float):
        assert fmt_duration(ms) == "0ms"


# ---------------------------------------------------------------------------
# Workflow CRUD properties
# ---------------------------------------------------------------------------

class TestWorkflowCRUDProperties:
    @given(st.text(min_size=1, max_size=50).filter(lambda s: s.strip()))
    @settings(max_examples=20)
    def test_create_then_get_roundtrip(self, name: str):
        clear_all()
        wf = create_workflow(WorkflowCreate(name=name))
        retrieved = get_workflow(wf.id)
        assert retrieved is not None
        assert retrieved.name == name

    @given(st.text(min_size=1, max_size=50).filter(lambda s: s.strip()))
    @settings(max_examples=20)
    def test_create_then_delete(self, name: str):
        clear_all()
        wf = create_workflow(WorkflowCreate(name=name))
        assert delete_workflow(wf.id) is True
        assert get_workflow(wf.id) is None

    @given(st.lists(
        st.text(min_size=1, max_size=20).filter(lambda s: s.strip()),
        min_size=0,
        max_size=10,
    ))
    @settings(max_examples=20)
    def test_list_count_matches_created(self, names: list):
        clear_all()
        for name in names:
            create_workflow(WorkflowCreate(name=name))
        all_wfs = list_workflows(limit=1000)
        assert len(all_wfs) == len(names)


# ---------------------------------------------------------------------------
# Topological sort properties
# ---------------------------------------------------------------------------

class TestTopologicalSortProperties:
    @given(st.integers(min_value=1, max_value=15))
    @settings(max_examples=20)
    def test_linear_chain_preserves_order(self, n: int):
        """A linear chain of n tasks should produce them in order."""
        tasks = []
        for i in range(n):
            deps = [f"T{i-1}"] if i > 0 else []
            tasks.append(TaskDefinition(
                id=f"T{i}", name=f"T{i}", action="log",
                parameters={"message": f"T{i}"}, depends_on=deps,
            ))
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert len(ids) == n
        for i in range(n - 1):
            assert ids.index(f"T{i}") < ids.index(f"T{i+1}")

    @given(st.integers(min_value=1, max_value=20))
    @settings(max_examples=20)
    def test_independent_tasks_all_present(self, n: int):
        """n independent tasks should all appear in the output."""
        tasks = [
            TaskDefinition(
                id=f"T{i}", name=f"T{i}", action="log",
                parameters={"message": f"T{i}"},
            )
            for i in range(n)
        ]
        order = _topological_sort(tasks)
        assert len(order) == n
        assert set(t.id for t in order) == {f"T{i}" for i in range(n)}
