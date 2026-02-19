"""Workflow endpoints aggregation module.

Composes the workflow router from four focused sub-modules:
  - ``workflow_crud``: create, list, get, update, delete, bulk-delete
  - ``workflow_execution``: execute, list executions, dry-run
  - ``workflow_tags``: add / remove tags
  - ``workflow_history``: version history, get version, clone

``main.py`` mounts the single ``router`` exported here under
``/api/workflows``.
"""

from __future__ import annotations

from fastapi import APIRouter

from .workflow_crud import router as crud_router
from .workflow_execution import router as execution_router
from .workflow_history import router as history_router
from .workflow_tags import router as tags_router

router = APIRouter()
router.include_router(crud_router)
router.include_router(execution_router)
router.include_router(tags_router)
router.include_router(history_router)
