from pathlib import Path

import pytest
from moviepy import VideoFileClip

from vidgen.domain.animation import FadeAnimation
from vidgen.domain.asset import Asset
from vidgen.domain.clip import VideoClip
from vidgen.domain.overlay import TextOverlay
from vidgen.domain.position import Alignment, Position
from vidgen.domain.timeline import Timeline
from vidgen.domain.track import OverlayTrack, VideoTrack
from vidgen.domain.transition import DissolveTransition
from vidgen.strategies.asset.loader import AssetLoader
from vidgen.strategies.render.moviepy_strategy import MoviePyRenderStrategy

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CLIPS = sorted((REPO_ROOT / "assets" / "clips").glob("*.mp4"))
SAMPLE_VIDEO = SAMPLE_CLIPS[0]
SAMPLE_VIDEO_2 = SAMPLE_CLIPS[1]


class RecordingAssetLoader(AssetLoader):
    """A real AssetLoader that also records every path it was asked to resolve."""

    def __init__(self):
        super().__init__()
        self.calls: list[str] = []

    def resolve(self, asset):
        self.calls.append(asset.path)
        return super().resolve(asset)


def _short_video_clip(path: Path, *, start: float = 0, end: float = 1.0, **kwargs) -> VideoClip:
    asset = Asset(path=str(path), type="video")
    return VideoClip(start=start, end=end, asset=asset, trim_in=0, trim_out=1.0, **kwargs)


def test_render_minimal_timeline_produces_expected_output(tmp_path):
    timeline = Timeline(resolution=(320, 240), fps=24)
    timeline.tracks["main"] = VideoTrack(name="main")
    timeline.tracks["main"].add(_short_video_clip(SAMPLE_VIDEO))
    timeline.tracks["overlay"] = OverlayTrack(name="overlay")
    timeline.tracks["overlay"].add(
        TextOverlay(start=0, end=1, position=Position.preset(Alignment.CENTER), text="hi")
    )
    output_path = tmp_path / "out.mp4"

    result = MoviePyRenderStrategy().render(timeline, str(output_path))

    assert result == output_path
    assert output_path.exists()
    written = VideoFileClip(str(output_path))
    try:
        assert tuple(written.size) == (320, 240)
        assert written.duration == pytest.approx(1.0, abs=0.2)
    finally:
        written.close()


def test_asset_loader_resolve_is_called_during_render_not_before(tmp_path):
    timeline = Timeline(resolution=(320, 240), fps=24)
    timeline.tracks["main"] = VideoTrack(name="main")
    timeline.tracks["main"].add(_short_video_clip(SAMPLE_VIDEO))
    loader = RecordingAssetLoader()
    strategy = MoviePyRenderStrategy(asset_loader=loader)

    assert loader.calls == []

    strategy.render(timeline, str(tmp_path / "out.mp4"))

    assert str(SAMPLE_VIDEO) in loader.calls


def test_render_timeline_with_animation_and_transition_completes(tmp_path):
    timeline = Timeline(resolution=(320, 240), fps=24)
    timeline.tracks["main"] = VideoTrack(name="main")
    timeline.tracks["main"].add(_short_video_clip(SAMPLE_VIDEO, start=0, end=1.0))
    timeline.tracks["main"].add(
        _short_video_clip(
            SAMPLE_VIDEO_2, start=1.0, end=2.0, transition_in=DissolveTransition(duration=0.3)
        )
    )
    timeline.tracks["overlay"] = OverlayTrack(name="overlay")
    timeline.tracks["overlay"].add(
        TextOverlay(
            start=0,
            end=1.5,
            position=Position.preset(Alignment.CENTER),
            text="hi",
            animation=FadeAnimation(duration=0.3, direction="in"),
        )
    )
    output_path = tmp_path / "out.mp4"

    MoviePyRenderStrategy().render(timeline, str(output_path))

    assert output_path.exists()
