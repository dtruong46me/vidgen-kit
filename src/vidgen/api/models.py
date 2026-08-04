"""Request/response schemas for the HTTP API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from vidgen.design.script import AnimationSpec, CaptionSpec, PositionSpec, ScriptModel, TextStyleSpec, TransitionSpec


class RenderRequest(ScriptModel):
    """A render request body — same shape as a Script spec file (see
    ``vidgen.design.script`` for the full field reference), plus an
    optional output filename."""

    filename: str | None = Field(
        default=None,
        description="Base name (no extension) for the output .mp4 file. Defaults to the job id.",
    )


class JobResponse(BaseModel):
    id: str
    status: str
    error: str | None = None
    download_url: str | None = None


class TemplateParam(BaseModel):
    name: str
    required: bool
    type: str


class TemplateInfo(BaseModel):
    name: str
    description: str
    params: list[TemplateParam]


class TemplateRenderRequest(BaseModel):
    """Body for ``POST /templates/{name}/render``.

    ``params`` is forwarded as keyword arguments to the template's
    ``apply()`` — see ``GET /templates`` for each template's accepted
    parameter names.
    """

    resolution: tuple[int, int] = (1080, 1920)
    fps: int = 30
    filename: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


# --- /edit/* — single-purpose editing operations, no Script/Template needed ---


class _EditRequestBase(BaseModel):
    resolution: tuple[int, int] = (1080, 1920)
    fps: int = 30
    filename: str | None = Field(
        default=None, description="Base name (no extension) for the output .mp4 file."
    )


class ConcatClipSpec(BaseModel):
    path: str
    trim_start: float = 0
    trim_end: float | None = None
    transition_in: TransitionSpec | None = Field(
        default=None, description="Transition from the previous clip into this one; ignored on the first clip."
    )


class ConcatRequest(_EditRequestBase):
    """Body for ``POST /edit/concat`` — join clips end to end, in order."""

    clips: list[ConcatClipSpec] = Field(min_length=1)


class TrimRequest(_EditRequestBase):
    """Body for ``POST /edit/trim`` — extract ``[trim_start, trim_end)`` from one video."""

    path: str
    trim_start: float = 0
    trim_end: float | None = None


class AddAudioRequest(_EditRequestBase):
    """Body for ``POST /edit/add-audio`` — mix background music/audio into a video.

    The video's own original audio (if any) is kept and mixed together
    with ``audio_path``, not replaced.
    """

    video_path: str
    audio_path: str
    volume: float = 1.0
    fade_in: float = 0
    fade_out: float = 0


class OverlayTextRequest(_EditRequestBase):
    """Body for ``POST /edit/overlay-text`` — burn a text overlay onto a video."""

    video_path: str
    text: str
    start: float = 0
    end: float | None = None
    position: PositionSpec | None = None
    style: TextStyleSpec | None = None
    animation: AnimationSpec | None = None


class OverlayImageRequest(_EditRequestBase):
    """Body for ``POST /edit/overlay-image`` — burn an image/watermark onto a video."""

    video_path: str
    image_path: str
    start: float = 0
    end: float | None = None
    position: PositionSpec
    animation: AnimationSpec | None = None


class CaptionsRequest(_EditRequestBase):
    """Body for ``POST /edit/captions`` — burn captions onto a video.

    ``captions`` uses the same shape as a ``Script`` spec's ``captions``
    field (source: file/whisper/hybrid) — see ``docs/API.md``.
    """

    video_path: str
    captions: CaptionSpec
