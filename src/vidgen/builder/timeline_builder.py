"""TimelineBuilder — fluent construction API (Layer 1).

``TimelineBuilder`` is the official, day-to-day entry point for assembling
a ``Timeline``. Every method returns ``self`` so calls chain; the only way
to obtain the finished ``Timeline`` is ``.build()``. This module only
imports from ``vidgen.domain`` (Layer 0) — no ``ffprobe``/MoviePy/
``faster-whisper``/``srt`` import anywhere here. In particular:

- ``.clip()``/``.image()``/``.audio()`` never touch the filesystem; they
  just wrap a bare ``Asset(path=path, ...)`` with metadata fields left
  ``None``. Resolving real duration/resolution/fps is ``AssetLoader``'s
  job (Layer 2), done at render time, not here.
- ``.captions()`` takes a ``SubtitleSource`` *instance* from the caller and
  only references the abstract port from ``domain/ports.py`` — never a
  concrete subtitle implementation.
"""

from __future__ import annotations

from typing import Any, TypeVar, cast

from vidgen.domain.animation import Animation
from vidgen.domain.asset import Asset
from vidgen.domain.audio import AudioLayer
from vidgen.domain.clip import VideoClip
from vidgen.domain.errors import TrackTypeConflictError
from vidgen.domain.overlay import ImageOverlay, TextOverlay
from vidgen.domain.ports import SubtitleSource
from vidgen.domain.position import Alignment, Position
from vidgen.domain.style import TextStyle
from vidgen.domain.timeline import Timeline
from vidgen.domain.track import AudioTrack, CaptionTrack, OverlayTrack, Track, VideoTrack
from vidgen.domain.transition import Transition

# Bound to Track so `_get_or_create_track(name, CaptionTrack)` is known to
# return a `CaptionTrack` (with `.style`), not just the base `Track` —
# without this, static type checkers can't see past the base type and
# `caption_track.style = style` in `.captions()` looks like an error.
TTrack = TypeVar("TTrack", bound=Track)


class TimelineBuilder:
    """Fluent, chainable API for assembling a ``Timeline``.

    Internally delegates to ``Track``/``Clip``/``Overlay`` (Layer 0) — a
    regular user doesn't need to know those classes exist to use this API.

    Attributes:
        _timeline: The ``Timeline`` instance being assembled. Private —
            callers interact with it only through this builder's methods
            and ``.build()``.
    """

    def __init__(self, resolution: tuple[int, int], fps: int = 30) -> None:
        self._timeline = Timeline(resolution=resolution, fps=fps)

    def track(self, name: str, track_cls: type[Track] = VideoTrack) -> "TimelineBuilder":
        """Ensure a track named ``name`` of type ``track_cls`` exists.

        Useful to pre-create a track before referencing it by name
        elsewhere, or to pre-create a ``CaptionTrack`` with a custom
        ``style``. The created/existing track itself is discarded here —
        this method only exists for its side effect, kept chainable.
        """
        self._get_or_create_track(name, track_cls)
        return self

    def clip(
        self,
        path: str,
        start: float,
        end: float | None = None,
        *,
        track: str = "main",
        transition_in: Transition | None = None,
    ) -> "TimelineBuilder":
        """Add a video clip to ``track`` (created as a ``VideoTrack`` if needed)."""
        asset = Asset(path=path, type="video")
        clip = VideoClip(start=start, end=end, asset=asset, transition_in=transition_in)
        self._get_or_create_track(track, VideoTrack).add(clip)
        return self

    def clips(self, specs: list[dict[str, Any]], *, track: str = "main") -> "TimelineBuilder":
        """Add multiple clips at once; each dict in ``specs`` is forwarded to ``.clip()``."""
        for spec in specs:
            self.clip(track=track, **spec)
        return self

    def text(
        self,
        text: str,
        start: float,
        end: float,
        *,
        position: Position = Position.preset(Alignment.CENTER),
        style: TextStyle | None = None,
        animation: Animation | None = None,
        track: str = "overlay",
    ) -> "TimelineBuilder":
        """Add a text overlay to ``track`` (created as an ``OverlayTrack`` if needed)."""
        overlay = TextOverlay(
            start=start,
            end=end,
            position=position,
            animation=animation,
            text=text,
            # `style` defaults to TextStyle() rather than being left None,
            # so downstream code (RenderStrategy) never has to handle a
            # missing style.
            style=style if style is not None else TextStyle(),
        )
        self._get_or_create_track(track, OverlayTrack).add(overlay)
        return self

    def image(
        self,
        path: str,
        start: float,
        end: float | None = None,
        *,
        position: Position,
        animation: Animation | None = None,
        track: str = "overlay",
    ) -> "TimelineBuilder":
        """Add an image overlay to ``track`` (created as an ``OverlayTrack`` if needed).

        ``position`` is required (no default) — Python raises ``TypeError``
        if it's omitted, same as any other required keyword-only argument.
        """
        asset = Asset(path=path, type="image")
        overlay = ImageOverlay(start=start, end=end, position=position, animation=animation, asset=asset)
        self._get_or_create_track(track, OverlayTrack).add(overlay)
        return self

    def audio(
        self,
        path: str,
        *,
        start: float = 0,
        volume: float = 1.0,
        fade_in: float = 0,
        fade_out: float = 0,
        track: str = "audio",
    ) -> "TimelineBuilder":
        """Add an audio layer to ``track`` (created as an ``AudioTrack`` if needed)."""
        asset = Asset(path=path, type="audio")
        layer = AudioLayer(asset=asset, start=start, volume=volume, fade_in=fade_in, fade_out=fade_out)
        self._get_or_create_track(track, AudioTrack).add(layer)
        return self

    def captions(
        self,
        source: SubtitleSource,
        *,
        script_text: str | None = None,
        voice_audio: str,
        style: TextStyle | None = None,
        track: str = "captions",
    ) -> "TimelineBuilder":
        """Generate captions via ``source`` and add them to ``track``.

        Calls ``source.generate(script_text=script_text,
        voice_audio=voice_audio)`` and adds the resulting ``Caption``\\ s to
        a ``CaptionTrack``. Whatever ``source.generate()`` raises (e.g. a
        ``ValueError`` from a hybrid source when ``script_text`` is
        missing) propagates unchanged — this method does not wrap or
        suppress it.
        """
        # Track a "did it already exist" flag *before* creating it, since
        # `style` should only apply when this call is the one creating the
        # CaptionTrack — an existing track keeps whatever style it already
        # has.
        track_existed = track in self._timeline.tracks
        caption_track = self._get_or_create_track(track, CaptionTrack)
        captions = source.generate(script_text=script_text, voice_audio=voice_audio)
        caption_track.add_many(captions)
        if style is not None and not track_existed:
            caption_track.style = style
        return self

    def build(self) -> Timeline:
        """Validate and return the assembled ``Timeline``.

        Safe to call more than once — each call re-validates and returns
        the same underlying ``Timeline`` reflecting whatever has been
        chained so far.
        """
        self._timeline._validate()
        return self._timeline

    def _get_or_create_track(self, name: str, track_cls: type[TTrack]) -> TTrack:
        """Look up track ``name``, creating it as ``track_cls`` if absent.

        Raises:
            TrackTypeConflictError: ``name`` already exists as a different
                ``Track`` subclass than ``track_cls``.
        """
        existing = self._timeline.tracks.get(name)
        if existing is None:
            new_track = track_cls(name=name)
            self._timeline.tracks[name] = new_track
            return new_track
        if type(existing) is not track_cls:
            raise TrackTypeConflictError(
                f"track {name!r} already exists as {type(existing).__name__}, "
                f"cannot reuse it as {track_cls.__name__}"
            )
        # The `type(existing) is track_cls` check above proves this at
        # runtime; `cast` tells the type checker what it can't infer from
        # `self._timeline.tracks: dict[str, Track]` alone.
        return cast(TTrack, existing)
