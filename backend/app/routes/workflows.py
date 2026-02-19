"""Workflow CRUD and execution endpoints.

All endpoints return Pydantic models directly; FastAPI handles
serialisation.  ``None`` from services maps to 404, ``ValueError``
maps to 409.

This module aggregates the sub-routers from ``workflow_crud``,
``workflow_execution``, and ``workflow_extras`` into a single router
so that ``main.py`` can mount them under ``/api/workflows``.
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
