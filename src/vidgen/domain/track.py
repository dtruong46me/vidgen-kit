"""Track — an ordered collection of items of one kind (Layer 0).

Each ``Track`` subclass enforces which item type it accepts, and any
track-specific integrity rule (e.g. non-overlapping video clips), right
at ``add()`` time — a wrong item is rejected immediately rather than
discovered later at render time.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from vidgen.domain.audio import AudioLayer
from vidgen.domain.caption import Caption
from vidgen.domain.clip import Clip
from vidgen.domain.errors import ClipOverlapError, TrackItemTypeError
from vidgen.domain.overlay import Overlay
from vidgen.domain.style import TextStyle

T = TypeVar("T")


class Track(ABC, Generic[T]):
    """Base class for a named, ordered collection of timeline items.

    Attributes:
        name: The track's name, used to look it up on a ``Timeline``.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._items: list[T] = []

    def add(self, item: T) -> T:
        """Validate and append a single item to this track.

        Returns:
            The same item that was passed in, for convenience.
        """
        self._validate_item(item)
        self._items.append(item)
        return item

    def add_many(self, items: Iterable[T]) -> list[T]:
        """Validate and append multiple items, in order."""
        return [self.add(item) for item in items]

    def items(self) -> tuple[T, ...]:
        """A read-only, ordered view of every item on this track."""
        return tuple(self._items)

    @abstractmethod
    def _validate_item(self, item: T) -> None:
        """Subclass hook: raise if ``item`` is not valid for this track."""
        raise NotImplementedError


class VideoTrack(Track[Clip]):
    """Holds ``Clip``s (``VideoClip``/``ImageClip``) in sequence.

    Unlike the other track kinds, clips here may not overlap in time —
    a ``VideoTrack`` represents a single visible video stream, so two
    clips can't legitimately occupy the same instant.
    """

    def _validate_item(self, item: Clip) -> None:
        if not isinstance(item, Clip):
            raise TrackItemTypeError(
                f"VideoTrack only accepts Clip items, got "
                f"{type(item).__name__}"
            )
        # No explicit "only the last clip may have end=None" check here:
        # an open-ended clip (end=None) is treated by `_overlaps` as
        # extending to infinity, so adding *anything* else that would
        # land at or after it — including a second open-ended clip —
        # already fails the overlap check below, regardless of the order
        # items were added in. That already is the "only the last clip
        # may be open-ended" rule; a separate check here would be
        # redundant, and (since it only looked at insertion order, not
        # time order) would wrongly reject the common case of adding
        # several closed clips and then one open-ended one last.
        for existing in self._items:
            if self._overlaps(existing, item):
                raise ClipOverlapError(
                    f"clip [{item.start}, {item.end}) overlaps existing "
                    f"clip [{existing.start}, {existing.end})"
                )

    @staticmethod
    def _overlaps(a: Clip, b: Clip) -> bool:
        """Whether two clips' [start, end) ranges intersect.

        An open-ended clip (``end=None``) is treated as extending to
        infinity for the purpose of this check.
        """
        a_end = a.end if a.end is not None else float("inf")
        b_end = b.end if b.end is not None else float("inf")
        return a.start < b_end and b.start < a_end


class OverlayTrack(Track[Overlay]):
    """Holds ``Overlay``s (``TextOverlay``/``ImageOverlay``).

    Overlays are allowed to overlap in time — multiple overlays may
    legitimately be on screen at once (e.g. a logo watermark plus a
    text callout), so no overlap check applies here.
    """

    def _validate_item(self, item: Overlay) -> None:
        if not isinstance(item, Overlay):
            raise TrackItemTypeError(
                f"OverlayTrack only accepts Overlay items, got "
                f"{type(item).__name__}"
            )


class AudioTrack(Track[AudioLayer]):
    """Holds ``AudioLayer``s.

    Layered/overlapping audio is normal (e.g. background music under a
    voiceover), so no overlap check applies here.
    """

    def _validate_item(self, item: AudioLayer) -> None:
        if not isinstance(item, AudioLayer):
            raise TrackItemTypeError(
                f"AudioTrack only accepts AudioLayer items, got "
                f"{type(item).__name__}"
            )


class CaptionTrack(Track[Caption]):
    """Holds ``Caption``s, all rendered with one shared ``style``.

    Attributes:
        style: The ``TextStyle`` applied to every caption on this
            track.
    """

    def __init__(self, name: str, style: TextStyle | None = None) -> None:
        super().__init__(name)
        self.style = style if style is not None else TextStyle()

    def _validate_item(self, item: Caption) -> None:
        if not isinstance(item, Caption):
            raise TrackItemTypeError(
                f"CaptionTrack only accepts Caption items, got "
                f"{type(item).__name__}"
            )
