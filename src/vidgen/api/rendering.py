"""Shared helper for submitting a built ``Timeline`` as a background render job.

Every endpoint that ends in "render this timeline" (``/renders``,
``/templates/{name}/render``, every ``/edit/*`` operation) does the exact
same three things afterward: pick an output filename, submit the render
to the job store, and shape the response — factored out here so each
router only has to build the ``Timeline`` itself.
"""

from __future__ import annotations

from fastapi import Request

from vidgen.api.models import JobResponse
from vidgen.domain.timeline import Timeline


def submit_render_job(timeline: Timeline, filename: str | None, http_request: Request) -> JobResponse:
    output_dir = http_request.app.state.output_dir
    render_strategy = http_request.app.state.render_strategy
    job_store = http_request.app.state.job_store

    def _render(job_id: str):
        out_name = filename or job_id
        return render_strategy.render(timeline, str(output_dir / f"{out_name}.mp4"))

    job = job_store.submit(_render)
    return JobResponse(id=job.id, status=job.status.value, download_url=f"/jobs/{job.id}/file")
