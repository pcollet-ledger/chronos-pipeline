"""Data models for Chronos Pipeline workflow engine."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# Matches alphanumeric chars, underscores, hyphens, and dots — the set of
# characters considered safe for action identifiers throughout the platform.
_ACTION_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.\-]*$")

# Allowed numeric ranges per cron field (minute, hour, dom, month, dow).
_CRON_FIELD_RANGES = [
    (0, 59),   # minute
    (0, 23),   # hour
    (1, 31),   # day of month
    (1, 12),   # month
    (0, 6),    # day of week
]

# Regex that matches a single cron field token: *, a number, a range, a list,
# or any of those with a /step suffix.  Numeric bounds are checked separately.
_CRON_TOKEN_RE = re.compile(
    r"^(\*|\d{1,2}(-\d{1,2})?(,\d{1,2})*)(/\d{1,2})?$"
)

MAX_NAME_LENGTH = 200


def _validate_name(value: str, label: str = "Name") -> str:
    """Shared name validation: non-empty after stripping, max 200 chars."""
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{label} must not be empty")
    if len(stripped) > MAX_NAME_LENGTH:
        raise ValueError(
            f"{label} must be at most {MAX_NAME_LENGTH} characters, "
            f"got {len(stripped)}"
        )
    return stripped


def _validate_cron_field(token: str, lo: int, hi: int) -> bool:
    """Check that a single cron field has valid syntax and in-range values."""
    m = _CRON_TOKEN_RE.match(token)
    if not m:
        return False

    base, step_part = m.group(1), m.group(4)

    # Validate step denominator (the part after '/')
    if step_part is not None:
        step_val = int(step_part[1:])  # strip leading '/'
        if step_val < 1 or step_val > hi:
            return False

    # '*' with optional step is always valid at this point
    if base == "*":
        return True

    # Extract all literal numbers from the base (handles N, N-M, N,M,... forms)
    nums = [int(n) for n in re.findall(r"\d+", base)]
    return all(lo <= n <= hi for n in nums)


def validate_cron_expression(expression: str) -> bool:
    """Validate a 5-field cron expression (minute hour dom month dow).

    Mirrors the logic in ``services.task_scheduler.validate_cron`` so that
    model-level validation stays consistent with the scheduler.
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        return False
    return all(
        _validate_cron_field(part, lo, hi)
        for part, (lo, hi) in zip(parts, _CRON_FIELD_RANGES)
    )


class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskDefinition(BaseModel):
    """Definition of a single task within a workflow."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    priority: TaskPriority = TaskPriority.MEDIUM

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        return _validate_name(v, label="Task name")

    @field_validator("action")
    @classmethod
    def action_must_contain_valid_chars(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Action must not be empty")
        if not _ACTION_NAME_RE.match(stripped):
            raise ValueError(
                f"Action '{stripped}' contains invalid characters. "
                "Use only letters, digits, underscores, hyphens, and dots, "
                "starting with a letter."
            )
        return stripped

    @field_validator("timeout_seconds")
    @classmethod
    def timeout_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(
                f"timeout_seconds must be positive, got {v}"
            )
        return v

    @field_validator("retry_count")
    @classmethod
    def retry_count_must_be_in_range(cls, v: int) -> int:
        if v < 0 or v > 10:
            raise ValueError(
                f"retry_count must be between 0 and 10 inclusive, got {v}"
            )
        return v


class TaskResult(BaseModel):
    """Result of a task execution."""
    task_id: str
    status: WorkflowStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class WorkflowDefinition(BaseModel):
    """Definition of a complete workflow."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    tasks: List[TaskDefinition] = Field(default_factory=list)
    schedule: Optional[str] = None  # Cron expression
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowExecution(BaseModel):
    """Record of a workflow execution."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_results: List[TaskResult] = Field(default_factory=list)
    trigger: str = "manual"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowCreate(BaseModel):
    """Request body for creating a workflow."""
    name: str
    description: str = ""
    tasks: List[TaskDefinition] = Field(default_factory=list)
    schedule: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        return _validate_name(v, label="Workflow name")

    @field_validator("schedule")
    @classmethod
    def schedule_must_be_valid_cron(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            return None
        if not validate_cron_expression(stripped):
            raise ValueError(
                f"Invalid cron expression: '{stripped}'. "
                "Expected 5-field format: minute hour day month weekday"
            )
        return stripped


class WorkflowUpdate(BaseModel):
    """Request body for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    tasks: Optional[List[TaskDefinition]] = None
    schedule: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def name_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_name(v, label="Workflow name")

    @field_validator("schedule")
    @classmethod
    def schedule_must_be_valid_cron(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            return None
        if not validate_cron_expression(stripped):
            raise ValueError(
                f"Invalid cron expression: '{stripped}'. "
                "Expected 5-field format: minute hour day month weekday"
            )
        return stripped


class AnalyticsSummary(BaseModel):
    """Summary analytics for the dashboard."""
    total_workflows: int = 0
    total_executions: int = 0
    success_rate: float = 0.0
    avg_duration_ms: float = 0.0
    executions_by_status: Dict[str, int] = Field(default_factory=dict)
    recent_executions: List[WorkflowExecution] = Field(default_factory=list)
    top_failing_workflows: List[Dict[str, Any]] = Field(default_factory=list)
