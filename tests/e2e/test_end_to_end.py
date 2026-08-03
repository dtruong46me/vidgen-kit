"""End-to-end integration tests (PLAN.md §3.6).

Unlike every other test in this suite, these exercise the *real*
``MoviePyRenderStrategy`` against real files in ``assets/`` — no stub
strategies, no fake timelines. They are slower than a unit test but are
the only tests that actually prove the full stack (Script/Template ->
TimelineBuilder -> RenderStrategy -> a playable file) works together.
"""

import json
from pathlib import Path

import pytest
from moviepy import VideoFileClip

from vidgen.automation.batch_producer import BatchProducer
from vidgen.builder import TimelineBuilder
from vidgen.design.template import FacelessQuoteTemplate
from vidgen.strategies.render.moviepy_strategy import MoviePyRenderStrategy

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_VIDEO = sorted((REPO_ROOT / "assets" / "clips").glob("*.mp4"))[0]
SAMPLE_MUSIC = min((REPO_ROOT / "assets" / "music").glob("*.mp3"), key=lambda p: p.stat().st_size)
VOICE_DIR = REPO_ROOT / "assets" / "voice"
SAMPLE_VOICE = next(VOICE_DIR.glob("*"), None) if VOICE_DIR.is_dir() else None


def _real_video_duration(path: Path) -> float:
    clip = VideoFileClip(str(path))
    try:
        return clip.duration
    finally:
        clip.close()


@pytest.mark.slow
@pytest.mark.skipif(SAMPLE_VOICE is None, reason="no sample voice audio in assets/voice/")
def test_script_with_hybrid_captions_renders_matching_spec(tmp_path):
    """A real Script (clip + text + audio + hybrid captions) -> BatchProducer.run()
    produces a playable file matching the spec's declared resolution/duration.

    Assumes the sample voice clip in assets/voice/ is no longer than
    SAMPLE_VIDEO, so the hybrid captions it generates never push the
    rendered duration past the base video's.
    """
    resolution = [720, 1280]
    video_duration = _real_video_duration(SAMPLE_VIDEO)
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    output_dir = tmp_path / "output"
    (spec_dir / "quote.json").write_text(
        json.dumps(
            {
                "resolution": resolution,
                "fps": 24,
                "clips": [{"path": str(SAMPLE_VIDEO), "start": 0}],
                "texts": [
                    {
                        "text": "Hello!",
                        "start": 0,
                        "end": video_duration,
                        "position": {"preset": "center"},
                    }
                ],
                "audio": [{"path": str(SAMPLE_MUSIC), "volume": 0.3}],
                "captions": {
                    "source": "hybrid",
                    "voice_audio": str(SAMPLE_VOICE),
                    "script_text": "this is a placeholder script matching the sample voice clip",
                },
            }
        ),
        encoding="utf-8",
    )

    result = BatchProducer(str(spec_dir)).run(str(output_dir))

    assert result.failed == []
    assert len(result.succeeded) == 1
    output_path = result.succeeded[0]
    assert output_path.exists()

    written = VideoFileClip(str(output_path))
    try:
        assert tuple(written.size) == tuple(resolution)
        assert written.duration == pytest.approx(video_duration, abs=0.5)
    finally:
        written.close()


def test_faceless_quote_template_with_real_assets_renders_successfully(tmp_path):
    """A real Template applied with real assets -> TimelineBuilder ->
    MoviePyRenderStrategy renders successfully."""
    builder = TimelineBuilder(resolution=(720, 1280), fps=24)
    FacelessQuoteTemplate().apply(
        builder,
        background_clip=str(SAMPLE_VIDEO),
        quote_text="Be water, my friend.",
        music=str(SAMPLE_MUSIC),
    )
    timeline = builder.build()
    output_path = tmp_path / "quote.mp4"

    result = MoviePyRenderStrategy().render(timeline, str(output_path))

    assert result == output_path
    assert output_path.exists()

    written = VideoFileClip(str(output_path))
    try:
        assert written.duration > 0
        assert tuple(written.size) == (720, 1280)
    finally:
        written.close()
