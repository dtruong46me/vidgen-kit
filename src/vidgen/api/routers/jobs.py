"""GET /jobs/{id} and GET /jobs/{id}/file — poll a submitted render job."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from vidgen.api.jobs import JobStatus
from vidgen.api.models import JobResponse

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, http_request: Request) -> JobResponse:
    job = http_request.app.state.job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"no job {job_id!r}")
    return JobResponse(
        id=job.id,
        status=job.status.value,
        error=job.error,
        download_url=f"/jobs/{job.id}/file" if job.status == JobStatus.SUCCEEDED else None,
    )


@router.get("/jobs/{job_id}/file")
def download_job_file(job_id: str, http_request: Request) -> FileResponse:
    job = http_request.app.state.job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"no job {job_id!r}")
    if job.status != JobStatus.SUCCEEDED or job.output_path is None:
        raise HTTPException(
            status_code=409, detail=f"job {job_id!r} is not finished (status={job.status.value})"
        )
    return FileResponse(job.output_path, media_type="video/mp4", filename=job.output_path.name)
