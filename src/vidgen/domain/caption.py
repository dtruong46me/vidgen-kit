"""Caption — a single subtitle line (Layer 0)."""

from dataclasses import dataclass

from vidgen.domain.errors import TimeRangeError


@dataclass
class Caption:
    """A single subtitle line with its on-screen time range.

    Deliberately has no ``style`` field — a ``CaptionTrack`` carries one
    shared ``TextStyle`` applied to every ``Caption`` on it, since a
    track's captions are rendered with one consistent look.

    Attributes:
        text: The caption text.
        start: Start time on the timeline, in seconds.
        end: End time on the timeline, in seconds.
    """

    text: str
    start: float
    end: float

    def __post_init__(self) -> None:
        # Same TimeRangeError rule as Clip/Overlay: a caption with no
        # positive duration can never actually be displayed.
        if self.end <= self.start:
            raise TimeRangeError(
                f"end ({self.end!r}) must be greater than start "
                f"({self.start!r})"
            )
