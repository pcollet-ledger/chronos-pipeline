"""Workflow routes - composed from sub-modules.

This module assembles the workflow router from three sub-modules:
- ``workflow_crud``: CRUD + bulk-delete + list/search
- ``workflow_execution``: execute, dry-run, list executions
- ``workflow_extras``: clone, versioning, tagging

The combined ``router`` is mounted in ``main.py`` under ``/api/workflows``.
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
