"""Workflow routes package.

Combines CRUD, execution, versioning, and tag sub-routers into a single
``router`` that is mounted in ``main.py``.
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .execution import router as execution_router
from .tags import router as tags_router
from .versioning import router as versioning_router

router = APIRouter()
router.include_router(crud_router)
router.include_router(execution_router)
router.include_router(versioning_router)
router.include_router(tags_router)
