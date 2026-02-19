"""Data models for Chronos Pipeline workflow engine."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    """Definition of a single task within a workflow.

    Hooks allow lightweight actions to run around the main action:
    - ``pre_hook``: action name executed *before* the main action.
    - ``post_hook``: action name executed *after* the main action.

    If a hook is ``None`` it is simply skipped.  Hook actions use the same
    action registry and receive the task's ``parameters``.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    priority: TaskPriority = TaskPriority.MEDIUM
    pre_hook: Optional[str] = None
    post_hook: Optional[str] = None


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
    cancelled_at: Optional[datetime] = None
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


class WorkflowUpdate(BaseModel):
    """Request body for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    tasks: Optional[List[TaskDefinition]] = None
    schedule: Optional[str] = None
    tags: Optional[List[str]] = None


class BulkDeleteRequest(BaseModel):
    """Request body for bulk-deleting workflows by ID.

    Accepts a list of workflow IDs.  IDs that do not correspond to an
    existing workflow are silently counted as ``not_found`` rather than
    raising an error, so callers can fire-and-forget without pre-checking.
    """
    ids: List[str] = Field(
        ...,
        min_length=1,
        description="Non-empty list of workflow IDs to delete.",
    )


class BulkDeleteResponse(BaseModel):
    """Summary returned after a bulk-delete operation.

    ``deleted`` and ``not_found`` always sum to the length of the
    original request list (minus any duplicates that were deduplicated
    server-side).
    """
    deleted: int = 0
    not_found: int = 0
    deleted_ids: List[str] = Field(default_factory=list)
    not_found_ids: List[str] = Field(default_factory=list)


class TagsRequest(BaseModel):
    """Request body for adding tags to a workflow."""
    tags: List[str] = Field(..., min_length=1, description="Tags to add.")


class TaskComparison(BaseModel):
    """Side-by-side comparison of a single task across two executions."""
    task_id: str
    status_a: str
    status_b: str
    duration_diff_ms: Optional[int] = None


class ComparisonSummary(BaseModel):
    """Aggregate summary of an execution comparison."""
    improved_count: int = 0
    regressed_count: int = 0
    unchanged_count: int = 0


class ExecutionComparison(BaseModel):
    """Result of comparing two executions of the same workflow."""
    workflow_id: str
    executions: List[WorkflowExecution]
    task_comparison: List[TaskComparison]
    summary: ComparisonSummary


class AnalyticsSummary(BaseModel):
    """Summary analytics for the dashboard."""
    total_workflows: int = 0
    total_executions: int = 0
    success_rate: float = 0.0
    avg_duration_ms: float = 0.0
    executions_by_status: Dict[str, int] = Field(default_factory=dict)
    recent_executions: List[WorkflowExecution] = Field(default_factory=list)
    top_failing_workflows: List[Dict[str, Any]] = Field(default_factory=list)
