"""Script — declarative JSON/YAML spec that drives a TimelineBuilder
(Layer 3).

``Script(path).parse()`` reads a JSON/YAML file, validates it against a
``pydantic`` model, and maps each field 1-to-1 onto the corresponding
``TimelineBuilder`` (Layer 1) method call — no logic of its own beyond
mapping + validation. It is one of two ways (alongside ``Template``,
``template.py``) to describe a design above the raw ``TimelineBuilder``
calls, useful when the design is produced or edited outside of Python (a
UI, a config file).

This module is allowed to import Layer 2 (``vidgen.strategies``): the
``captions`` field of a spec needs a concrete ``SubtitleSource`` instance,
and constructing one (``FileSubtitleSource``/``WhisperSubtitleSource``/
``HybridSubtitleSource``) is exactly that kind of "outside world" concern
Layer 2 exists for. ``TimelineBuilder`` itself still only ever sees the
abstract ``SubtitleSource`` port from Layer 0 — this module is the caller
that does the injecting.

Spec shape (JSON or YAML, top-level object)::

    {
      "resolution": [1080, 1920],
      "fps": 30,
      "clips": [
        {"path": "a.mp4", "start": 0, "end": 5,
         "transition_in": {"type": "dissolve", "duration": 0.5}}
      ],
      "texts": [
        {"text": "Hello!", "start": 0, "end": 3,
         "position": {"preset": "center"},
         "style": {"font_size": 64, "color": "white"},
         "animation": {"type": "fade", "duration": 0.4, "direction": "in"}}
      ],
      "images": [
        {"path": "logo.png", "start": 0, "end": 5,
         "position": {"x": 0.05, "y": 0.05, "unit": "ratio"}}
      ],
      "audio": [
        {"path": "bg.mp3", "volume": 0.3, "fade_out": 2}
      ],
      "captions": {
        "source": "hybrid", "voice_audio": "voice.mp3", "script_text": "..."
      }
    }

Every field not shown above falls back to the same default
``TimelineBuilder`` uses. Unknown fields anywhere in the spec are
rejected (``extra="forbid"``) rather than silently ignored.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from vidgen.builder import TimelineBuilder
from vidgen.design.errors import ScriptValidationError
from vidgen.domain.animation import Animation, FadeAnimation, SlideAnimation, ZoomAnimation
from vidgen.domain.ports import SubtitleSource
from vidgen.domain.position import Alignment, Position
from vidgen.domain.style import TextStyle
from vidgen.domain.transition import CutTransition, DissolveTransition, FadeTransition, Transition
from vidgen.strategies.subtitle import FileSubtitleSource, HybridSubtitleSource, WhisperSubtitleSource

_ANIMATION_CLASSES: dict[str, type[Animation]] = {
    "fade": FadeAnimation,
    "slide": SlideAnimation,
    "zoom": ZoomAnimation,
}

_TRANSITION_CLASSES: dict[str, type[Transition]] = {
    "cut": CutTransition,
    "fade": FadeTransition,
    "dissolve": DissolveTransition,
}


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PositionSpec(_StrictModel):
    """Either a named ``preset`` or explicit ``x``/``y``, never both."""

    preset: str | None = None
    x: float | None = None
    y: float | None = None
    unit: Literal["ratio", "pixel"] = "ratio"

    @model_validator(mode="after")
    def _check_exactly_one_kind(self) -> "PositionSpec":
        has_preset = self.preset is not None
        has_xy = self.x is not None or self.y is not None
        if has_preset and has_xy:
            raise ValueError("position: specify either 'preset' or 'x'/'y', not both")
        if not has_preset and not has_xy:
            raise ValueError("position: specify either 'preset' or both 'x' and 'y'")
        if has_xy and (self.x is None or self.y is None):
            raise ValueError("position: both 'x' and 'y' are required together")
        return self

    def to_domain(self) -> Position:
        if self.preset is not None:
            return Position.preset(Alignment(self.preset))
        assert self.x is not None and self.y is not None
        return Position.custom(self.x, self.y, unit=self.unit)


class TextStyleSpec(_StrictModel):
    font: str = "Arial"
    font_size: int = 48
    color: str = "white"
    outline_color: str | None = "black"
    outline_width: int = 0
    bg_color: str | None = None
    align: Literal["left", "center", "right"] = "center"
    max_width: int | None = None

    def to_domain(self) -> TextStyle:
        return TextStyle(**self.model_dump())


class AnimationSpec(_StrictModel):
    type: Literal["fade", "slide", "zoom"]
    duration: float
    direction: str

    def to_domain(self) -> Animation:
        return _ANIMATION_CLASSES[self.type](duration=self.duration, direction=self.direction)


class TransitionSpec(_StrictModel):
    type: Literal["cut", "fade", "dissolve"]
    duration: float = 0

    def to_domain(self) -> Transition:
        return _TRANSITION_CLASSES[self.type](duration=self.duration)


class ClipSpec(_StrictModel):
    path: str
    start: float
    end: float | None = None
    track: str = "main"
    transition_in: TransitionSpec | None = None


class TextSpec(_StrictModel):
    text: str
    start: float
    end: float
    track: str = "overlay"
    position: PositionSpec | None = None
    style: TextStyleSpec | None = None
    animation: AnimationSpec | None = None


class ImageSpec(_StrictModel):
    path: str
    start: float
    end: float | None = None
    track: str = "overlay"
    position: PositionSpec
    animation: AnimationSpec | None = None


class AudioSpec(_StrictModel):
    path: str
    start: float = 0
    volume: float = 1.0
    fade_in: float = 0
    fade_out: float = 0
    track: str = "audio"


class CaptionSpec(_StrictModel):
    source: Literal["file", "whisper", "hybrid"]
    voice_audio: str
    script_text: str | None = None
    path: str | None = None
    model_size: str = "base"
    device: str = "cpu"
    track: str = "captions"

    @model_validator(mode="after")
    def _check_source_requirements(self) -> "CaptionSpec":
        if self.source == "file" and self.path is None:
            raise ValueError("captions: source 'file' requires 'path'")
        if self.source == "hybrid" and not self.script_text:
            raise ValueError("captions: source 'hybrid' requires 'script_text'")
        return self

    def to_source(self) -> SubtitleSource:
        if self.source == "file":
            assert self.path is not None
            return FileSubtitleSource(self.path)
        if self.source == "whisper":
            return WhisperSubtitleSource(model_size=self.model_size, device=self.device)
        return HybridSubtitleSource(model_size=self.model_size, device=self.device)


class ScriptModel(_StrictModel):
    """The full validated shape of a spec file."""

    resolution: tuple[int, int]
    fps: int = 30
    clips: list[ClipSpec] = Field(default_factory=list)
    texts: list[TextSpec] = Field(default_factory=list)
    images: list[ImageSpec] = Field(default_factory=list)
    audio: list[AudioSpec] = Field(default_factory=list)
    captions: CaptionSpec | None = None


class Script:
    """Reads a JSON/YAML spec file and drives a ``TimelineBuilder`` from it.

    Attributes:
        path: Filesystem path to the ``.json``/``.yaml``/``.yml`` spec.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def parse(self) -> TimelineBuilder:
        """Validate the spec at ``self.path`` and apply it to a fresh ``TimelineBuilder``.

        Returns the **not-yet-built** ``TimelineBuilder`` so callers may
        chain further manual calls before ``.build()``.

        Raises:
            ScriptValidationError: The spec fails ``pydantic`` validation
                (unknown field, missing required field, wrong type, ...).
        """
        raw = self._read_raw()
        try:
            spec = ScriptModel.model_validate(raw)
        except ValidationError as exc:
            raise ScriptValidationError(f"invalid script {self.path!r}: {exc}") from exc

        builder = TimelineBuilder(resolution=spec.resolution, fps=spec.fps)

        for clip in spec.clips:
            builder.clip(
                clip.path,
                clip.start,
                clip.end,
                track=clip.track,
                transition_in=clip.transition_in.to_domain() if clip.transition_in else None,
            )
        for text in spec.texts:
            builder.text(
                text.text,
                text.start,
                text.end,
                position=text.position.to_domain() if text.position else Position.preset(Alignment.CENTER),
                style=text.style.to_domain() if text.style else None,
                animation=text.animation.to_domain() if text.animation else None,
                track=text.track,
            )
        for image in spec.images:
            builder.image(
                image.path,
                image.start,
                image.end,
                position=image.position.to_domain(),
                animation=image.animation.to_domain() if image.animation else None,
                track=image.track,
            )
        for audio in spec.audio:
            builder.audio(
                audio.path,
                start=audio.start,
                volume=audio.volume,
                fade_in=audio.fade_in,
                fade_out=audio.fade_out,
                track=audio.track,
            )
        if spec.captions is not None:
            builder.captions(
                spec.captions.to_source(),
                script_text=spec.captions.script_text,
                voice_audio=spec.captions.voice_audio,
                track=spec.captions.track,
            )

        return builder

    def _read_raw(self) -> dict:
        text = Path(self.path).read_text(encoding="utf-8")
        if self.path.endswith((".yaml", ".yml")):
            return yaml.safe_load(text)
        return json.loads(text)
