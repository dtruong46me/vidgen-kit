"""Asset — a reference to a media file on disk (Layer 0).

An ``Asset`` is created with only a ``path``/``type`` by
``TimelineBuilder``; its metadata fields stay ``None`` until
``AssetLoader`` (Layer 2) resolves them at render time. No I/O happens
in this module — that is precisely what keeps Layer 1 free of any
``ffprobe``/MoviePy dependency.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Asset:
    """A reference to a video/image/audio file.

    Attributes:
        path: Filesystem path to the media file.
        type: The kind of media this asset refers to.
        duration: Duration in seconds. ``None`` until resolved by
            ``AssetLoader``.
        resolution: ``(width, height)`` in pixels. ``None`` until
            resolved by ``AssetLoader``.
        fps: Frames per second (video only). ``None`` until resolved by
            ``AssetLoader``.
    """

    path: str
    type: Literal["video", "image", "audio"]
    duration: float | None = None
    resolution: tuple[int, int] | None = None
    fps: float | None = None
