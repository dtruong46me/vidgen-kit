import subprocess
import sys

import pytest

from vidgen.builder import TimelineBuilder
from vidgen.domain import Alignment, AudioTrack, Caption, OverlayTrack, Position, TextStyle, VideoTrack
from vidgen.domain.errors import TimelineValidationError, TrackTypeConflictError
from vidgen.domain.ports import SubtitleSource


class FakeSubtitleSource(SubtitleSource):
    """A minimal in-test SubtitleSource — no real subtitle library involved."""

    def __init__(self, captions):
        self._captions = captions
        self.calls = []

    def generate(self, *, script_text, voice_audio):
        self.calls.append({"script_text": script_text, "voice_audio": voice_audio})
        return self._captions


def _builder():
    return TimelineBuilder(resolution=(1080, 1920), fps=30)


def test_track_returns_same_builder():
    builder = _builder()

    assert builder.track("main") is builder


def test_clip_returns_same_builder():
    builder = _builder()

    assert builder.clip("a.mp4", start=0, end=5) is builder


def test_text_returns_same_builder():
    builder = _builder()

    assert builder.text("hi", 0, 1, position=Position.preset(Alignment.CENTER)) is builder


def test_image_returns_same_builder():
    builder = _builder()

    assert builder.image("logo.png", 0, 1, position=Position.preset(Alignment.TOP_LEFT)) is builder


def test_audio_returns_same_builder():
    builder = _builder()

    assert builder.audio("bg.mp3") is builder


def test_clip_stores_asset_without_touching_filesystem():
    builder = _builder()

    # A path that does not exist on disk — if .clip() ever performed I/O
    # (e.g. ffprobe/MoviePy) this would raise; it must not.
    builder.clip("does/not/exist.mp4", start=0, end=5)
    timeline = builder.build()

    clip = timeline.get_track("main").items()[0]
    assert clip.asset.path == "does/not/exist.mp4"
    assert clip.asset.type == "video"
    assert clip.asset.duration is None
    assert clip.asset.resolution is None
    assert clip.asset.fps is None


def test_captions_calls_source_generate_and_attaches_to_caption_track():
    captions = [Caption(text="hi", start=0, end=1), Caption(text="there", start=1, end=2)]
    source = FakeSubtitleSource(captions)
    builder = _builder()

    builder.captions(source, script_text="hi there", voice_audio="voice.mp3")
    timeline = builder.build()

    assert source.calls == [{"script_text": "hi there", "voice_audio": "voice.mp3"}]
    caption_track = timeline.get_track("captions")
    assert caption_track.items() == tuple(captions)


def test_captions_style_applied_only_when_track_is_newly_created():
    builder = _builder()
    style_a = TextStyle(font_size=40)
    style_b = TextStyle(font_size=99)

    builder.captions(FakeSubtitleSource([]), voice_audio="v1.mp3", style=style_a)
    builder.captions(FakeSubtitleSource([]), voice_audio="v2.mp3", style=style_b)

    assert builder.build().get_track("captions").style is style_a


def test_build_validates_and_returns_matching_timeline():
    builder = _builder()
    builder.clip("a.mp4", start=0, end=5)
    builder.text("hi", 0, 1, position=Position.preset(Alignment.CENTER))
    builder.audio("bg.mp3")

    timeline = builder.build()

    assert timeline.resolution == (1080, 1920)
    assert timeline.fps == 30
    assert isinstance(timeline.get_track("main"), VideoTrack)
    assert isinstance(timeline.get_track("overlay"), OverlayTrack)
    assert isinstance(timeline.get_track("audio"), AudioTrack)


def test_build_raises_when_timeline_has_no_tracks():
    builder = _builder()

    with pytest.raises(TimelineValidationError):
        builder.build()


def test_build_is_idempotent():
    builder = _builder()
    builder.clip("a.mp4", start=0, end=5)

    first = builder.build()
    second = builder.build()

    assert first is second


def test_reusing_track_name_with_different_track_cls_raises():
    builder = _builder()
    builder.clip("a.mp4", start=0, end=5)  # creates "main" as a VideoTrack

    with pytest.raises(TrackTypeConflictError):
        builder.audio("bg.mp3", track="main")


def test_builder_package_imports_without_pulling_in_heavy_third_party_libs():
    """Layer test: Layer 1 must depend only on Layer 0 (domain).

    Importing `vidgen.builder` must never, as a side effect, import any of
    the heavy libraries reserved for Layer 2 (`moviepy`, `faster_whisper`,
    `srt`) — those are only ever imported by concrete RenderStrategy /
    SubtitleSource implementations, not by the Builder itself.

    Run in a fresh subprocess rather than checking `sys.modules` in-process:
    other test files in this same suite legitimately import `moviepy`/`srt`
    (Layer 2 tests) — checking the current process's `sys.modules` would give
    a false failure depending on test execution order.
    """
    code = (
        "import sys\n"
        "import vidgen.builder\n"
        "heavy_libs = {'moviepy', 'faster_whisper', 'srt'}\n"
        "assert not heavy_libs & set(sys.modules), sys.modules.keys()\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
