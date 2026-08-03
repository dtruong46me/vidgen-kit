"""TextStyle — fully customizable text styling (Layer 0)."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class TextStyle:
    """Visual styling applied to a ``TextOverlay`` or a ``CaptionTrack``.

    Every field has a sensible default, so simple usage only needs to
    override what actually matters (e.g. just ``color``). No validation
    is performed here beyond typing — an invalid ``font`` (e.g. a
    missing .ttf path) can only be discovered by ``RenderStrategy`` at
    render time, since Layer 0 has no filesystem access.

    Attributes:
        font: System font name, or a path to a custom .ttf file.
        font_size: Font size in points.
        color: Text fill color.
        outline_color: Text outline color, or ``None`` for no outline.
        outline_width: Outline width in pixels.
        bg_color: Background color behind the text, or ``None`` for no
            background.
        align: Horizontal text alignment within its bounding box.
        max_width: Maximum line width in pixels before auto-wrapping,
            or ``None`` for no wrapping.
    """

    font: str = "Arial"
    font_size: int = 48
    color: str = "white"
    outline_color: str | None = "black"
    outline_width: int = 0
    bg_color: str | None = None
    align: Literal["left", "center", "right"] = "center"
    max_width: int | None = None
