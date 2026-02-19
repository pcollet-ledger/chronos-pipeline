"""Chronos Pipeline Backend - FastAPI Application Entry Point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import analytics, tasks, workflows
from .utils.middleware import TimingAndTracingMiddleware

app = FastAPI(
    title="Chronos Pipeline",
    description="Data pipeline orchestration and scheduling platform",
    version="0.1.0",
)

app.add_middleware(TimingAndTracingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A dict with service status information.
    """
    return {"status": "healthy", "service": "chronos-pipeline-backend"}
