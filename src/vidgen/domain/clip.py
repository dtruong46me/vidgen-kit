"""Clip — a piece of video/image content placed on a VideoTrack (Layer 0)."""

from abc import ABC
from dataclasses import dataclass

from vidgen.domain.animation import Animation
from vidgen.domain.asset import Asset
from vidgen.domain.errors import TimeRangeError
from vidgen.domain.transition import Transition

# All fields are keyword-only (kw_only=True) so subclasses can add
# required fields (e.g. VideoClip.asset) after the base class's
# optional `animation` field without violating dataclass field-ordering
# rules, while still matching how these classes are actually called
# (always by keyword, e.g. VideoClip(asset=..., start=0, end=4)).


@dataclass(kw_only=True)
class Clip(ABC):
    """Base class shared by every item placed on a ``VideoTrack``.

    Attributes:
        start: Start time on the timeline, in seconds.
        end: End time on the timeline, in seconds. ``None`` means "play
            until the asset's natural end" — only the last clip on a
            ``VideoTrack`` may do this (enforced by ``VideoTrack``, not
            here).
        animation: Optional entrance/exit animation for this clip.
    """

    start: float
    end: float | None
    animation: Animation | None = None

    def __post_init__(self) -> None:
        if self.end is not None and self.end <= self.start:
            raise TimeRangeError(
                f"end ({self.end!r}) must be greater than start "
                f"({self.start!r})"
            )


@dataclass(kw_only=True)
class VideoClip(Clip):
    """A clip backed by a video ``Asset``.

    Attributes:
        asset: The underlying video asset (``asset.type`` must be
            ``"video"``).
        trim_in: Seconds to trim off the start of the source asset.
        trim_out: Seconds into the source asset to stop at, or ``None``
            to play to the asset's natural end.
        transition_in: Transition used when this clip follows another
            on the same ``VideoTrack``. Only ``VideoClip`` has this
            field — transitions are specifically clip-to-clip on a
            ``VideoTrack``.
    """

    asset: Asset
    trim_in: float = 0
    trim_out: float | None = None
    transition_in: Transition | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.asset.type != "video":
            raise ValueError(
                f"VideoClip requires an Asset with type='video', got "
                f"{self.asset.type!r}"
            )


@dataclass(kw_only=True)
class ImageClip(Clip):
    """A clip backed by a static image ``Asset``, held for [start, end).

    No ``transition_in`` field — images don't participate in
    clip-to-clip video transitions.

    Attributes:
        asset: The underlying image asset (``asset.type`` must be
            ``"image"``).
    """

    asset: Asset

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.asset.type != "image":
            raise ValueError(
                f"ImageClip requires an Asset with type='image', got "
                f"{self.asset.type!r}"
            )
