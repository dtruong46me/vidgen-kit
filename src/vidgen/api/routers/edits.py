"""``/edit/*`` — single-purpose editing operations.

Unlike ``/renders`` and ``/templates/*/render``, these don't require the
caller to assemble a full ``Script``/``Template`` — each endpoint here is
one concrete operation a video editor actually reaches for (join clips,
trim a clip, add background music, overlay text/image, burn captions).
Under the hood every one of these still builds a ``Timeline`` and submits
it through the same background job queue as the rest of the API — the
render itself is just as slow either way — but the request shape is a
single flat operation instead of a whole spec.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from vidgen.api.models import (
    AddAudioRequest,
    CaptionsRequest,
    ConcatRequest,
    JobResponse,
    OverlayImageRequest,
    OverlayTextRequest,
    TrimRequest,
)
from vidgen.api.rendering import submit_render_job
from vidgen.builder import TimelineBuilder
from vidgen.domain.asset import Asset
from vidgen.domain.clip import VideoClip
from vidgen.domain.position import Alignment, Position
from vidgen.domain.timeline import Timeline
from vidgen.domain.track import VideoTrack

router = APIRouter(prefix="/edit", tags=["edit"])


def _run(build, http_request: Request, filename: str | None) -> JobResponse:
    """Build a Timeline via ``build()``, translating any domain-level
    validation failure (e.g. overlapping clips) into a 422, then submit it."""
    try:
        timeline = build()
    except Exception as exc:  # noqa: BLE001 - surfaced to the client as a validation error
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return submit_render_job(timeline, filename, http_request)


@router.post("/concat", response_model=JobResponse, status_code=202)
def concat(request: ConcatRequest, http_request: Request) -> JobResponse:
    """Join ``request.clips`` end to end, in the order given.

    Clip ``start``/``end`` values only need to be non-overlapping for
    domain validation to pass — the actual rendered output is a plain
    sequential concatenation (each clip's real duration comes from its
    own ``trim_start``/``trim_end``, resolved at render time), so
    placeholder indices (0, 1, 2, ...) are used here rather than asking
    the caller for real timeline positions they can't know in advance.
    """

    def build() -> Timeline:
        timeline = Timeline(resolution=request.resolution, fps=request.fps)
        track = VideoTrack(name="main")
        last_index = len(request.clips) - 1
        for i, clip in enumerate(request.clips):
            track.add(
                VideoClip(
                    start=i,
                    end=None if i == last_index else i + 1,
                    asset=Asset(path=clip.path, type="video"),
                    trim_in=clip.trim_start,
                    trim_out=clip.trim_end,
                    transition_in=clip.transition_in.to_domain() if clip.transition_in else None,
                )
            )
        timeline.tracks["main"] = track
        timeline._validate()
        return timeline

    return _run(build, http_request, request.filename)


@router.post("/trim", response_model=JobResponse, status_code=202)
def trim(request: TrimRequest, http_request: Request) -> JobResponse:
    """Extract ``[trim_start, trim_end)`` from ``request.path`` as a standalone clip."""

    def build() -> Timeline:
        timeline = Timeline(resolution=request.resolution, fps=request.fps)
        track = VideoTrack(name="main")
        track.add(
            VideoClip(
                start=0,
                end=None,
                asset=Asset(path=request.path, type="video"),
                trim_in=request.trim_start,
                trim_out=request.trim_end,
            )
        )
        timeline.tracks["main"] = track
        timeline._validate()
        return timeline

    return _run(build, http_request, request.filename)


@router.post("/add-audio", response_model=JobResponse, status_code=202)
def add_audio(request: AddAudioRequest, http_request: Request) -> JobResponse:
    """Mix background music/audio into ``request.video_path``."""

    def build() -> Timeline:
        builder = TimelineBuilder(resolution=request.resolution, fps=request.fps)
        builder.clip(request.video_path, start=0)
        builder.audio(
            request.audio_path,
            volume=request.volume,
            fade_in=request.fade_in,
            fade_out=request.fade_out,
        )
        return builder.build()

    return _run(build, http_request, request.filename)


@router.post("/overlay-text", response_model=JobResponse, status_code=202)
def overlay_text(request: OverlayTextRequest, http_request: Request) -> JobResponse:
    """Burn a text overlay onto ``request.video_path``."""

    def build() -> Timeline:
        builder = TimelineBuilder(resolution=request.resolution, fps=request.fps)
        builder.clip(request.video_path, start=0)
        builder.text(
            request.text,
            request.start,
            request.end,
            position=request.position.to_domain() if request.position else Position.preset(Alignment.CENTER),
            style=request.style.to_domain() if request.style else None,
            animation=request.animation.to_domain() if request.animation else None,
        )
        return builder.build()

    return _run(build, http_request, request.filename)


@router.post("/overlay-image", response_model=JobResponse, status_code=202)
def overlay_image(request: OverlayImageRequest, http_request: Request) -> JobResponse:
    """Burn an image/watermark overlay onto ``request.video_path``."""

    def build() -> Timeline:
        builder = TimelineBuilder(resolution=request.resolution, fps=request.fps)
        builder.clip(request.video_path, start=0)
        builder.image(
            request.image_path,
            request.start,
            request.end,
            position=request.position.to_domain(),
            animation=request.animation.to_domain() if request.animation else None,
        )
        return builder.build()

    return _run(build, http_request, request.filename)


@router.post("/captions", response_model=JobResponse, status_code=202)
def captions(request: CaptionsRequest, http_request: Request) -> JobResponse:
    """Burn captions (file/whisper/hybrid) onto ``request.video_path``."""

    def build() -> Timeline:
        builder = TimelineBuilder(resolution=request.resolution, fps=request.fps)
        builder.clip(request.video_path, start=0)
        builder.captions(
            request.captions.to_source(),
            script_text=request.captions.script_text,
            voice_audio=request.captions.voice_audio,
        )
        return builder.build()

    return _run(build, http_request, request.filename)
