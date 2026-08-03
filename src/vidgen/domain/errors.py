"""Shared exception hierarchy for the domain layer (Layer 0).

Domain-level validation failures raise one of the exceptions defined
here instead of a bare ``ValueError``/``TypeError``, so callers can
catch domain-specific errors precisely without accidentally swallowing
unrelated bugs.
"""


class TimeRangeError(ValueError):
    """A time range is invalid.

    Covers both a plain ``end <= start`` on a single item, and a
    non-last ``VideoClip`` on a ``VideoTrack`` that has ``end=None``
    (only the last clip on a track may be open-ended).
    """


class TrackItemTypeError(TypeError):
    """``Track.add()`` received an item of the wrong type for that
    track (e.g. adding a ``TextOverlay`` to a ``VideoTrack``)."""


class ClipOverlapError(TimeRangeError):
    """Two ``VideoClip``s on the same ``VideoTrack`` overlap in time."""


class TrackTypeConflictError(TypeError):
    """An existing track name was requested again with a different
    ``Track`` subclass than the one it was originally created with."""


class TimelineValidationError(ValueError):
    """``Timeline._validate()`` failed for a reason not already covered
    by a more specific error above (e.g. a ``Timeline`` with no tracks
    at all)."""
