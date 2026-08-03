"""MoviePyRenderStrategy — the v1 RenderStrategy implementation (Layer 2).

Walks a ``Timeline``'s tracks, resolving each referenced ``Asset`` via
``AssetLoader`` only now (not at build time), and turns the declared
``Position``/``TextStyle``/``Animation``/``Transition`` data into the
corresponding MoviePy calls. This is the only module that knows *how* an
``Animation``/``Transition`` is actually rendered — the domain classes
themselves stay pure data so Layer 0 never imports MoviePy (see
``domain/animation.py``/``domain/transition.py``: their ``_apply`` stubs
are never called; the dispatch on animation/transition *type* lives here
instead, keeping the domain model ignorant of "how to execute").
"""

import os
from pathlib import Path

from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    afx,
    concatenate_videoclips,
    vfx,
)

from vidgen.domain.animation import Animation, FadeAnimation, SlideAnimation, ZoomAnimation
from vidgen.domain.audio import AudioLayer
from vidgen.domain.clip import Clip
from vidgen.domain.clip import ImageClip as DomainImageClip
from vidgen.domain.clip import VideoClip as DomainVideoClip
from vidgen.domain.overlay import ImageOverlay, Overlay, TextOverlay
from vidgen.domain.position import Alignment, Position
from vidgen.domain.style import TextStyle
from vidgen.domain.timeline import Timeline
from vidgen.domain.track import AudioTrack, CaptionTrack, OverlayTrack, VideoTrack
from vidgen.domain.transition import CutTransition, DissolveTransition, FadeTransition, Transition
from vidgen.strategies.asset.loader import AssetLoader
from vidgen.strategies.errors import RenderError
from vidgen.strategies.render.base import RenderStrategy

# Where to look for a bare system font *name* (as opposed to a path) —
# TextStyle.font defaults to "Arial", which MoviePy/Pillow cannot load
# directly (it wants a .ttf/.otf file). Best-effort only: if a name
# can't be found here, we fall back to MoviePy's bundled default font
# rather than failing the whole render over a missing font file.
_SYSTEM_FONT_DIRS = [
    Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
    Path("/usr/share/fonts/truetype"),
    Path("/Library/Fonts"),
]

# A still image has no natural duration; used only when an open-ended
# (end=None) ImageClip is the last item on a VideoTrack.
_DEFAULT_IMAGE_CLIP_DURATION = 5.0

# Fraction of a preset-aligned overlay's own size to zoom in/out over,
# for ZoomAnimation — a fixed, subtle default depth (not user-tunable
# in v1, matching the "basic presets" scope of Animation).
_ZOOM_SCALE_DEPTH = 0.2

# Alignment -> (x, y) top-left pixel position, given the output
# resolution and the overlay clip's own (already-built) pixel size.
_PRESET_POSITIONS = {
    Alignment.CENTER: lambda w, h, cw, ch: ((w - cw) / 2, (h - ch) / 2),
    Alignment.TOP_LEFT: lambda w, h, cw, ch: (0, 0),
    Alignment.TOP_CENTER: lambda w, h, cw, ch: ((w - cw) / 2, 0),
    Alignment.TOP_RIGHT: lambda w, h, cw, ch: (w - cw, 0),
    Alignment.BOTTOM_LEFT: lambda w, h, cw, ch: (0, h - ch),
    Alignment.BOTTOM_CENTER: lambda w, h, cw, ch: ((w - cw) / 2, h - ch),
    Alignment.BOTTOM_RIGHT: lambda w, h, cw, ch: (w - cw, h - ch),
    Alignment.LEFT: lambda w, h, cw, ch: (0, (h - ch) / 2),
    Alignment.RIGHT: lambda w, h, cw, ch: (w - cw, (h - ch) / 2),
}


class MoviePyRenderStrategy(RenderStrategy):
    """Renders a ``Timeline`` to a video file using MoviePy.

    Attributes:
        asset_loader: Used to resolve every ``Asset`` referenced by the
            timeline. Defaults to a plain ``AssetLoader()`` — this is
            the only place one gets wired in, so ``TimelineBuilder``
            never has to know it exists.
    """

    def __init__(self, asset_loader: AssetLoader | None = None) -> None:
        self.asset_loader = asset_loader if asset_loader is not None else AssetLoader()

    def render(self, timeline: Timeline, output_path: str) -> Path:
        video_tracks = [t for t in timeline.tracks.values() if isinstance(t, VideoTrack)]
        if not video_tracks:
            raise RenderError("Timeline has no VideoTrack to render")

        try:
            base_video = self._composite_video_tracks(video_tracks, timeline.resolution)
            overlay_clips = self._build_overlay_clips(timeline, base_video.duration)
            caption_clips = self._build_caption_clips(timeline, base_video.duration)
            final_video = CompositeVideoClip(
                [base_video, *overlay_clips, *caption_clips], size=timeline.resolution
            )

            audio_components = ([base_video.audio] if base_video.audio is not None else [])
            audio_components += self._build_audio_clips(timeline)
            if audio_components:
                final_video = final_video.with_audio(CompositeAudioClip(audio_components))

            final_video.write_videofile(output_path, fps=timeline.fps)
            return Path(output_path)
        except RenderError:
            raise
        except Exception as exc:  # noqa: BLE001 - wrap any MoviePy/ffmpeg failure
            raise RenderError(f"failed to render timeline to {output_path!r}: {exc}") from exc

    # --- video tracks (Clip -> one composited base video) ---

    def _composite_video_tracks(self, video_tracks: list[VideoTrack], resolution: tuple[int, int]):
        track_clips = [self._build_video_track(track) for track in video_tracks]
        if len(track_clips) == 1:
            return track_clips[0]
        return CompositeVideoClip(track_clips, size=resolution)

    def _build_video_track(self, track: VideoTrack):
        items = sorted(track.items(), key=lambda item: item.start)
        clip = self._build_single_clip(items[0])
        for item in items[1:]:
            next_clip = self._build_single_clip(item)
            transition = item.transition_in if isinstance(item, DomainVideoClip) else None
            clip = self._concat_with_transition(clip, next_clip, transition)
        return clip

    def _build_single_clip(self, item: Clip):
        asset = self.asset_loader.resolve(item.asset)
        if isinstance(item, DomainVideoClip):
            mp_clip = VideoFileClip(asset.path).subclipped(item.trim_in, item.trim_out)
        elif isinstance(item, DomainImageClip):
            duration = (
                (item.end - item.start)
                if item.end is not None
                else (asset.duration or _DEFAULT_IMAGE_CLIP_DURATION)
            )
            mp_clip = ImageClip(asset.path).with_duration(duration)
        else:  # pragma: no cover - VideoTrack only accepts Clip subclasses
            raise RenderError(f"unsupported clip type: {type(item).__name__}")
        if item.animation is not None:
            mp_clip = self._apply_animation(mp_clip, item.animation)
        return mp_clip

    def _concat_with_transition(self, outgoing, incoming, transition: Transition | None):
        if transition is None or isinstance(transition, CutTransition):
            return concatenate_videoclips([outgoing, incoming], method="compose")
        if isinstance(transition, FadeTransition):
            outgoing = outgoing.with_effects([vfx.FadeOut(transition.duration)])
            incoming = incoming.with_effects([vfx.FadeIn(transition.duration)])
            return concatenate_videoclips([outgoing, incoming], method="compose")
        if isinstance(transition, DissolveTransition):
            incoming = incoming.with_effects([vfx.CrossFadeIn(transition.duration)])
            return concatenate_videoclips(
                [outgoing, incoming], method="compose", padding=-transition.duration
            )
        raise RenderError(f"unsupported transition type: {type(transition).__name__}")  # pragma: no cover

    # --- overlays (Overlay -> positioned/timed clips on top of the base video) ---

    def _build_overlay_clips(self, timeline: Timeline, base_duration: float) -> list:
        clips = []
        for track in timeline.tracks.values():
            if not isinstance(track, OverlayTrack):
                continue
            for item in track.items():
                clips.append(self._build_overlay_clip(item, timeline.resolution, base_duration))
        return clips

    def _build_overlay_clip(self, item: Overlay, resolution: tuple[int, int], base_duration: float):
        if isinstance(item, TextOverlay):
            mp_clip = self._build_text_clip(item.text, item.style)
        elif isinstance(item, ImageOverlay):
            asset = self.asset_loader.resolve(item.asset)
            mp_clip = ImageClip(asset.path)
        else:  # pragma: no cover - OverlayTrack only accepts Overlay subclasses
            raise RenderError(f"unsupported overlay type: {type(item).__name__}")

        duration = (item.end - item.start) if item.end is not None else (base_duration - item.start)
        mp_clip = mp_clip.with_duration(duration).with_start(item.start)
        x, y = self._resolve_position(item.position, resolution, mp_clip.size)
        mp_clip = mp_clip.with_position((x, y))
        if item.animation is not None:
            mp_clip = self._apply_animation(mp_clip, item.animation)
        return mp_clip

    def _build_text_clip(self, text: str, style: TextStyle):
        return TextClip(
            text=text,
            font=self._resolve_font(style.font),
            font_size=style.font_size,
            color=style.color,
            stroke_color=style.outline_color,
            stroke_width=style.outline_width,
            bg_color=style.bg_color,
            text_align=style.align,
            size=(style.max_width, None),
            method="caption" if style.max_width else "label",
        )

    def _resolve_position(
        self, position: Position, resolution: tuple[int, int], clip_size: tuple[int, int]
    ) -> tuple[float, float]:
        width, height = resolution
        clip_w, clip_h = clip_size
        if position.kind == "preset":
            return _PRESET_POSITIONS[position.alignment](width, height, clip_w, clip_h)
        if position.unit == "ratio":
            return (position.x * width, position.y * height)
        return (position.x, position.y)

    def _resolve_font(self, font: str) -> str | None:
        path = Path(font)
        if path.is_file():
            return str(path)
        for font_dir in _SYSTEM_FONT_DIRS:
            candidate = font_dir / f"{font}.ttf"
            if candidate.is_file():
                return str(candidate)
        return None

    # --- captions (Caption -> one styled TextClip per line, bottom-aligned) ---

    def _build_caption_clips(self, timeline: Timeline, base_duration: float) -> list:
        clips = []
        for track in timeline.tracks.values():
            if not isinstance(track, CaptionTrack):
                continue
            for caption in track.items():
                mp_clip = self._build_text_clip(caption.text, track.style)
                mp_clip = mp_clip.with_duration(caption.end - caption.start).with_start(caption.start)
                x, y = self._resolve_position(
                    Position.preset(Alignment.BOTTOM_CENTER), timeline.resolution, mp_clip.size
                )
                clips.append(mp_clip.with_position((x, y)))
        return clips

    # --- audio (AudioLayer -> volume/fade-adjusted, offset clips) ---

    def _build_audio_clips(self, timeline: Timeline) -> list:
        clips = []
        for track in timeline.tracks.values():
            if not isinstance(track, AudioTrack):
                continue
            for layer in track.items():
                clips.append(self._build_single_audio_clip(layer))
        return clips

    def _build_single_audio_clip(self, layer: AudioLayer):
        asset = self.asset_loader.resolve(layer.asset)
        mp_clip = AudioFileClip(asset.path)
        effects = []
        if layer.volume != 1.0:
            effects.append(afx.MultiplyVolume(layer.volume))
        if layer.fade_in:
            effects.append(afx.AudioFadeIn(layer.fade_in))
        if layer.fade_out:
            effects.append(afx.AudioFadeOut(layer.fade_out))
        if effects:
            mp_clip = mp_clip.with_effects(effects)
        return mp_clip.with_start(layer.start)

    # --- animation (shared by video Clips and Overlays) ---

    def _apply_animation(self, mp_clip, animation: Animation):
        if isinstance(animation, FadeAnimation):
            effect = vfx.FadeIn(animation.duration) if animation.direction == "in" else vfx.FadeOut(animation.duration)
            return mp_clip.with_effects([effect])
        if isinstance(animation, SlideAnimation):
            return mp_clip.with_effects([vfx.SlideIn(animation.duration, animation.direction)])
        if isinstance(animation, ZoomAnimation):
            return mp_clip.with_effects([vfx.Resize(self._zoom_scale_fn(animation, mp_clip.duration))])
        raise RenderError(f"unsupported animation type: {type(animation).__name__}")  # pragma: no cover

    @staticmethod
    def _zoom_scale_fn(animation: ZoomAnimation, clip_duration: float | None):
        duration = animation.duration
        depth = _ZOOM_SCALE_DEPTH

        if animation.direction == "in":
            def scale_at(t: float) -> float:
                if t >= duration:
                    return 1.0
                return (1 - depth) + depth * (t / duration)

            return scale_at

        window_start = (clip_duration - duration) if clip_duration is not None else 0

        def scale_at(t: float) -> float:
            if t <= window_start:
                return 1.0
            return 1.0 - depth * ((t - window_start) / duration)

        return scale_at
