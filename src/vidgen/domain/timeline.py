"""Timeline — the root domain object: resolution, fps, and tracks
(Layer 0).

``Timeline`` is plain data with light integrity checks; it has no
``add_*`` methods — those live on ``TimelineBuilder`` (Layer 1). It can
still be constructed/mutated directly (e.g. by tests or an alternate
builder), since it is just a dataclass.
"""

from dataclasses import dataclass, field

from vidgen.domain.errors import TimelineValidationError
from vidgen.domain.track import Track


@dataclass
class Timeline:
    """The root object describing one complete edit.

    Attributes:
        resolution: Output ``(width, height)`` in pixels.
        fps: Output frames per second.
        tracks: Named tracks, keyed by track name.
    """

    resolution: tuple[int, int]
    fps: int = 30
    tracks: dict[str, Track] = field(default_factory=dict)

    def get_track(self, name: str) -> Track | None:
        """Look up a track by name, or ``None`` if it doesn't exist."""
        return self.tracks.get(name)

    def _validate(self) -> None:
        """Check whole-timeline invariants.

        Per-track invariants (item type, clip overlap) are already
        enforced at ``Track.add()`` time by each subclass, so this only
        needs to check cross-cutting/whole-timeline conditions —
        currently just non-emptiness. Future checks (e.g. "at least one
        VideoTrack") extend this method without changing ``Track``.
        """
        if not self.tracks:
            raise TimelineValidationError("Timeline must have at least one track")
