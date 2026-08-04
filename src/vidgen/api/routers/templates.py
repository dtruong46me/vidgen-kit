"""GET /templates and POST /templates/{name}/render."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from vidgen.api.models import JobResponse, TemplateInfo, TemplateRenderRequest
from vidgen.api.rendering import submit_render_job
from vidgen.api.templates_registry import get_template, list_templates
from vidgen.builder import TimelineBuilder
from vidgen.design.script import TextStyleSpec

router = APIRouter(tags=["templates"])


@router.get("/templates", response_model=list[TemplateInfo])
def get_templates() -> list[TemplateInfo]:
    return [TemplateInfo(**info) for info in list_templates()]


@router.post("/templates/{name}/render", response_model=JobResponse, status_code=202)
def render_template(name: str, request: TemplateRenderRequest, http_request: Request) -> JobResponse:
    """Apply the named ``Template`` with ``request.params`` and render it in the background.

    ``request.params`` is forwarded as keyword arguments to the
    template's ``apply()`` — see ``GET /templates`` for the accepted
    names per template. A ``style`` param, if present, is treated as a
    ``TextStyleSpec``-shaped dict (same shape used in a ``Script`` spec)
    and converted to a domain ``TextStyle`` before being passed through.
    """
    template_cls = get_template(name)
    if template_cls is None:
        raise HTTPException(status_code=404, detail=f"unknown template {name!r}")

    builder = TimelineBuilder(resolution=request.resolution, fps=request.fps)
    kwargs = dict(request.params)
    if isinstance(kwargs.get("style"), dict):
        kwargs["style"] = TextStyleSpec.model_validate(kwargs["style"]).to_domain()

    try:
        template_cls().apply(builder, **kwargs)
        timeline = builder.build()
    except TypeError as exc:
        raise HTTPException(status_code=422, detail=f"invalid params for template {name!r}: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - surfaced to the client as a validation error
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return submit_render_job(timeline, request.filename, http_request)
