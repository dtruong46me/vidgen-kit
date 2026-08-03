"""Overlay — a piece of content composited on top of the video (Layer 0)."""

from abc import ABC
from dataclasses import dataclass, field

from vidgen.domain.animation import Animation
from vidgen.domain.asset import Asset
from vidgen.domain.errors import TimeRangeError
from vidgen.domain.position import Position
from vidgen.domain.style import TextStyle

# kw_only=True for the same field-ordering reason as clip.py: subclasses
# add required fields (text/asset) after the base class's optional
# `animation` field.


@dataclass(kw_only=True)
class Overlay(ABC):
    """Base class shared by every item placed on an ``OverlayTrack``.

    Attributes:
        start: Start time on the timeline, in seconds.
        end: End time on the timeline, in seconds. ``None`` means
            "shown until the end of the timeline".
        position: Where to place this overlay on screen.
        animation: Optional entrance/exit animation for this overlay.
    """

    start: float
    end: float | None
    position: Position
    animation: Animation | None = None

    def __post_init__(self) -> None:
        if self.end is not None and self.end <= self.start:
            raise TimeRangeError(
                f"end ({self.end!r}) must be greater than start "
                f"({self.start!r})"
            )


@dataclass(kw_only=True)
class TextOverlay(Overlay):
    """A text caption/label composited on screen.

    Attributes:
        text: The text to display.
        style: Visual styling for the text (defaults applied if
            omitted).
    """

    text: str
    style: TextStyle = field(default_factory=TextStyle)


@dataclass(kw_only=True)
class ImageOverlay(Overlay):
    """A static image (e.g. a watermark/logo) composited on screen.

    Attributes:
        asset: The underlying image asset (``asset.type`` must be
            ``"image"``).
    """

    asset: Asset

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.asset.type != "image":
            raise ValueError(
                f"ImageOverlay requires an Asset with type='image', got "
                f"{self.asset.type!r}"
            )
