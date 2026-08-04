"""FastAPI application factory (Layer 5 — HTTP API).

Sits above every other layer: it wires ``design`` (Script/Template) to a
``RenderStrategy`` (Layer 2) behind an async job queue, so a render
request never blocks the HTTP server. Nothing below this package imports
from it — the same one-directional dependency rule as the rest of the
stack, just extended one layer further up.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from vidgen.api.jobs import JobStore
from vidgen.api.routers import edits, jobs, renders, templates
from vidgen.strategies.render.base import RenderStrategy
from vidgen.strategies.render.moviepy_strategy import MoviePyRenderStrategy


def create_app(
    output_dir: str = "output",
    render_strategy: RenderStrategy | None = None,
    max_workers: int = 2,
) -> FastAPI:
    """Build the vidgen FastAPI app.

    Args:
        output_dir: Directory rendered files are written to. Created if
            it doesn't already exist.
        render_strategy: The ``RenderStrategy`` used for every render
            job. Defaults to ``MoviePyRenderStrategy()``.
        max_workers: Size of the background thread pool render jobs run on.
    """
    app = FastAPI(
        title="vidgen API",
        description="HTTP API for the vidgen programmable video editing engine.",
        version="0.1.0",
    )

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    app.state.output_dir = output_dir_path
    app.state.render_strategy = render_strategy if render_strategy is not None else MoviePyRenderStrategy()
    app.state.job_store = JobStore(max_workers=max_workers)

    app.include_router(renders.router)
    app.include_router(templates.router)
    app.include_router(edits.router)
    app.include_router(jobs.router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
