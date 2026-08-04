"""POST /renders — submit a Script-shaped spec for background rendering."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from vidgen.api.models import JobResponse, RenderRequest
from vidgen.api.rendering import submit_render_job
from vidgen.design.script import build_timeline_from_spec

router = APIRouter(tags=["renders"])


@router.post("/renders", response_model=JobResponse, status_code=202)
def create_render(request: RenderRequest, http_request: Request) -> JobResponse:
    """Validate ``request`` as a Script spec, then render it in the background.

    The request body is validated by FastAPI/pydantic before this
    handler runs (``RenderRequest`` extends the same ``ScriptModel`` used
    for on-disk spec files), so a malformed body never reaches here — it
    gets a 422 automatically. What can still fail here is a *domain*-level
    rule (e.g. two tracks with conflicting types), which is reported as a
    422 with the underlying error message.
    """
    try:
        timeline = build_timeline_from_spec(request).build()
    except Exception as exc:  # noqa: BLE001 - surfaced to the client as a validation error
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return submit_render_job(timeline, request.filename, http_request)
