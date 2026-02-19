"""Workflow routes – composed from sub-modules.

This module re-exports a single ``router`` that aggregates:

* ``workflow_crud``       – CRUD and listing
* ``workflow_execution``  – execute and list executions
* ``workflow_extras``     – clone, versioning, tagging, dry-run
"""

from __future__ import annotations

from fastapi import APIRouter

from .workflow_crud import router as crud_router
from .workflow_execution import router as execution_router
from .workflow_extras import router as extras_router

router = APIRouter()
router.include_router(crud_router)
router.include_router(execution_router)
router.include_router(extras_router)
