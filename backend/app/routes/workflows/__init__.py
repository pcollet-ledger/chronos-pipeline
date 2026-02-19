"""Workflow route sub-package.

Combines CRUD, execution, tagging, versioning, cloning, and dry-run
routers into a single ``router`` that ``main.py`` mounts at
``/api/workflows``.
"""

from __future__ import annotations

from fastapi import APIRouter

from .clone import router as clone_router
from .crud import router as crud_router
from .dry_run import router as dry_run_router
from .execution import router as execution_router
from .tagging import router as tagging_router
from .versioning import router as versioning_router

router = APIRouter()

router.include_router(crud_router)
router.include_router(execution_router)
router.include_router(dry_run_router)
router.include_router(clone_router)
router.include_router(tagging_router)
router.include_router(versioning_router)
