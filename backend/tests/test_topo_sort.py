"""Tests for topological sort edge cases in workflow_engine.

Covers: single task, linear chain, fan-out, fan-in, diamond,
disconnected components, non-existent dependency, self-referencing
task, and large DAG with 20+ tasks.
"""

import pytest

from app.models import TaskDefinition, WorkflowCreate, WorkflowStatus
from app.services.workflow_engine import (
    _topological_sort,
    clear_all,
    create_workflow,
    execute_workflow,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    yield
    clear_all()


def _make_task(tid: str, deps: list[str] | None = None) -> TaskDefinition:
    return TaskDefinition(
        id=tid, name=tid, action="log",
        parameters={"message": tid}, depends_on=deps or [],
    )


class TestTopologicalSort:
    """Edge-case tests for _topological_sort."""

    def test_single_task_no_deps(self):
        tasks = [_make_task("A")]
        order = _topological_sort(tasks)
        assert len(order) == 1
        assert order[0].id == "A"

    def test_linear_chain_abc(self):
        """A -> B -> C: must produce [A, B, C]."""
        tasks = [
            _make_task("A"),
            _make_task("B", ["A"]),
            _make_task("C", ["B"]),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids.index("A") < ids.index("B") < ids.index("C")

    def test_fan_out(self):
        """A -> B, A -> C, A -> D: A must come first."""
        tasks = [
            _make_task("A"),
            _make_task("B", ["A"]),
            _make_task("C", ["A"]),
            _make_task("D", ["A"]),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids[0] == "A"
        assert set(ids[1:]) == {"B", "C", "D"}

    def test_fan_in(self):
        """A -> D, B -> D, C -> D: D must come last."""
        tasks = [
            _make_task("A"),
            _make_task("B"),
            _make_task("C"),
            _make_task("D", ["A", "B", "C"]),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids[-1] == "D"
        assert set(ids[:3]) == {"A", "B", "C"}

    def test_diamond(self):
        """A -> B, A -> C, B -> D, C -> D."""
        tasks = [
            _make_task("A"),
            _make_task("B", ["A"]),
            _make_task("C", ["A"]),
            _make_task("D", ["B", "C"]),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids[0] == "A"
        assert ids[-1] == "D"
        assert ids.index("B") < ids.index("D")
        assert ids.index("C") < ids.index("D")

    def test_disconnected_components(self):
        """A -> B and C -> D with no link between the two pairs."""
        tasks = [
            _make_task("A"),
            _make_task("B", ["A"]),
            _make_task("C"),
            _make_task("D", ["C"]),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert len(ids) == 4
        assert ids.index("A") < ids.index("B")
        assert ids.index("C") < ids.index("D")

    def test_nonexistent_dependency_ignored(self):
        """A task referencing a non-existent dep should still appear."""
        tasks = [
            _make_task("A", ["GHOST"]),
        ]
        order = _topological_sort(tasks)
        assert len(order) == 1
        assert order[0].id == "A"

    def test_self_referencing_task_raises(self):
        """A task depending on itself is a cycle and should raise."""
        tasks = [_make_task("A", ["A"])]
        with pytest.raises(ValueError, match="cycle"):
            _topological_sort(tasks)

    def test_mutual_cycle_raises(self):
        """Two tasks depending on each other should raise."""
        tasks = [
            _make_task("A", ["B"]),
            _make_task("B", ["A"]),
        ]
        with pytest.raises(ValueError, match="cycle"):
            _topological_sort(tasks)

    def test_three_node_cycle_raises(self):
        """A -> B -> C -> A should raise."""
        tasks = [
            _make_task("A", ["C"]),
            _make_task("B", ["A"]),
            _make_task("C", ["B"]),
        ]
        with pytest.raises(ValueError, match="cycle"):
            _topological_sort(tasks)

    def test_large_dag_20_plus_tasks(self):
        """Linear chain of 25 tasks: T0 -> T1 -> ... -> T24."""
        tasks = []
        for i in range(25):
            deps = [f"T{i-1}"] if i > 0 else []
            tasks.append(_make_task(f"T{i}", deps))
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert len(ids) == 25
        for i in range(24):
            assert ids.index(f"T{i}") < ids.index(f"T{i+1}")

    def test_empty_task_list(self):
        order = _topological_sort([])
        assert order == []

    def test_all_independent_tasks(self):
        """Five tasks with no dependencies — all should appear."""
        tasks = [_make_task(f"T{i}") for i in range(5)]
        order = _topological_sort(tasks)
        assert len(order) == 5

    def test_execution_respects_topo_order(self):
        """End-to-end: execute a workflow and verify task order."""
        wf = create_workflow(WorkflowCreate(
            name="Topo WF",
            tasks=[
                {"id": "A", "name": "A", "action": "log", "parameters": {"message": "a"}},
                {"id": "B", "name": "B", "action": "log", "parameters": {"message": "b"}, "depends_on": ["A"]},
                {"id": "C", "name": "C", "action": "log", "parameters": {"message": "c"}, "depends_on": ["B"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        assert ex.status == WorkflowStatus.COMPLETED
        task_ids = [tr.task_id for tr in ex.task_results]
        assert task_ids == ["A", "B", "C"]

    def test_diamond_execution_order(self):
        wf = create_workflow(WorkflowCreate(
            name="Diamond WF",
            tasks=[
                {"id": "A", "name": "A", "action": "log", "parameters": {"message": "a"}},
                {"id": "B", "name": "B", "action": "log", "parameters": {"message": "b"}, "depends_on": ["A"]},
                {"id": "C", "name": "C", "action": "log", "parameters": {"message": "c"}, "depends_on": ["A"]},
                {"id": "D", "name": "D", "action": "log", "parameters": {"message": "d"}, "depends_on": ["B", "C"]},
            ],
        ))
        ex = execute_workflow(wf.id)
        ids = [tr.task_id for tr in ex.task_results]
        assert ids[0] == "A"
        assert ids[-1] == "D"

    def test_deep_chain_5_levels(self):
        """A -> B -> C -> D -> E: deeply nested linear chain."""
        tasks = [
            _make_task("A"),
            _make_task("B", ["A"]),
            _make_task("C", ["B"]),
            _make_task("D", ["C"]),
            _make_task("E", ["D"]),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids == ["A", "B", "C", "D", "E"]

    def test_two_independent_chains(self):
        """A -> B and X -> Y -> Z as two independent chains."""
        tasks = [
            _make_task("A"),
            _make_task("B", ["A"]),
            _make_task("X"),
            _make_task("Y", ["X"]),
            _make_task("Z", ["Y"]),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids.index("A") < ids.index("B")
        assert ids.index("X") < ids.index("Y") < ids.index("Z")

    def test_wide_fan_in_10_deps(self):
        """10 tasks all feeding into a single sink."""
        tasks = [_make_task(f"S{i}") for i in range(10)]
        tasks.append(_make_task("SINK", [f"S{i}" for i in range(10)]))
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids[-1] == "SINK"
        assert len(ids) == 11

    def test_wide_fan_out_10_children(self):
        """Single root with 10 children."""
        tasks = [_make_task("ROOT")]
        for i in range(10):
            tasks.append(_make_task(f"C{i}", ["ROOT"]))
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids[0] == "ROOT"
        assert set(ids[1:]) == {f"C{i}" for i in range(10)}

    def test_duplicate_dependencies_handled(self):
        """A task listing the same dependency twice."""
        tasks = [
            _make_task("A"),
            _make_task("B", ["A", "A"]),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids == ["A", "B"]

    def test_reverse_input_order(self):
        """Tasks provided in reverse dependency order."""
        tasks = [
            _make_task("C", ["B"]),
            _make_task("B", ["A"]),
            _make_task("A"),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids.index("A") < ids.index("B") < ids.index("C")

    def test_complex_dag_with_multiple_paths(self):
        """
        A -> B -> D
        A -> C -> D
        B -> E
        C -> E
        D -> F
        E -> F
        """
        tasks = [
            _make_task("A"),
            _make_task("B", ["A"]),
            _make_task("C", ["A"]),
            _make_task("D", ["B", "C"]),
            _make_task("E", ["B", "C"]),
            _make_task("F", ["D", "E"]),
        ]
        order = _topological_sort(tasks)
        ids = [t.id for t in order]
        assert ids[0] == "A"
        assert ids[-1] == "F"
        assert ids.index("B") < ids.index("D")
        assert ids.index("C") < ids.index("D")
        assert ids.index("B") < ids.index("E")
        assert ids.index("C") < ids.index("E")

    def test_single_task_with_multiple_ghost_deps(self):
        """A task depending on multiple non-existent tasks."""
        tasks = [_make_task("A", ["GHOST1", "GHOST2", "GHOST3"])]
        order = _topological_sort(tasks)
        assert len(order) == 1
        assert order[0].id == "A"

    def test_preserves_all_tasks(self):
        """Ensure no tasks are lost during sorting."""
        tasks = [_make_task(f"T{i}") for i in range(15)]
        order = _topological_sort(tasks)
        assert len(order) == 15
        assert set(t.id for t in order) == {f"T{i}" for i in range(15)}
