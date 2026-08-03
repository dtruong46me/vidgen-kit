"""Layer 0 — Domain Model.

Pure data + integrity rules, zero third-party imports. See
docs/ARCHITECTURE.md and docs/DESIGN.md for the full design.
"""

from vidgen.domain.animation import Animation, FadeAnimation, SlideAnimation, ZoomAnimation
from vidgen.domain.asset import Asset
from vidgen.domain.audio import AudioLayer
from vidgen.domain.caption import Caption
from vidgen.domain.clip import Clip, ImageClip, VideoClip
from vidgen.domain.overlay import ImageOverlay, Overlay, TextOverlay
from vidgen.domain.ports import SubtitleSource
from vidgen.domain.position import Alignment, Position
from vidgen.domain.style import TextStyle
from vidgen.domain.timeline import Timeline
from vidgen.domain.track import AudioTrack, CaptionTrack, OverlayTrack, Track, VideoTrack
from vidgen.domain.transition import (
    CutTransition,
    DissolveTransition,
    FadeTransition,
    Transition,
)

__all__ = [
    "Alignment",
    "Position",
    "TextStyle",
    "Animation",
    "FadeAnimation",
    "SlideAnimation",
    "ZoomAnimation",
    "Transition",
    "CutTransition",
    "FadeTransition",
    "DissolveTransition",
    "Asset",
    "Clip",
    "VideoClip",
    "ImageClip",
    "Overlay",
    "TextOverlay",
    "ImageOverlay",
    "AudioLayer",
    "Caption",
    "SubtitleSource",
    "Track",
    "VideoTrack",
    "OverlayTrack",
    "AudioTrack",
    "CaptionTrack",
    "Timeline",
]
