import pytest

from vidgen.builder import TimelineBuilder
from vidgen.design.template import FacelessQuoteTemplate
from vidgen.domain.caption import Caption
from vidgen.domain.ports import SubtitleSource


class FakeSubtitleSource(SubtitleSource):
    """A minimal in-test SubtitleSource — no real subtitle library involved."""

    def __init__(self, captions):
        self._captions = captions

    def generate(self, *, script_text, voice_audio):
        return self._captions


def _builder():
    return TimelineBuilder(resolution=(1080, 1920), fps=30)


def test_apply_returns_same_builder_and_builds_expected_tracks():
    builder = _builder()

    result = FacelessQuoteTemplate().apply(
        builder,
        background_clip="assets/clips/a.mp4",
        quote_text="Be water, my friend.",
        music="assets/music/bg.mp3",
    )

    assert result is builder
    timeline = builder.build()
    assert set(timeline.tracks) == {"main", "overlay", "audio"}

    clip = timeline.get_track("main").items()[0]
    assert clip.asset.path == "assets/clips/a.mp4"
    assert clip.start == 0
    assert clip.end is None

    text = timeline.get_track("overlay").items()[0]
    assert text.text == "Be water, my friend."
    assert text.end is None

    audio = timeline.get_track("audio").items()[0]
    assert audio.asset.path == "assets/music/bg.mp3"
    assert audio.volume == 0.3


def test_apply_without_voice_audio_creates_no_caption_track():
    builder = _builder()

    FacelessQuoteTemplate().apply(
        builder,
        background_clip="a.mp4",
        quote_text="Quote",
        music="m.mp3",
    )

    assert "captions" not in builder.build().tracks


def test_apply_with_voice_audio_generates_captions_via_given_source():
    builder = _builder()
    captions = [Caption(text="Be water", start=0, end=1)]
    source = FakeSubtitleSource(captions)

    FacelessQuoteTemplate().apply(
        builder,
        background_clip="a.mp4",
        quote_text="Be water, my friend.",
        music="m.mp3",
        voice_audio="voice.mp3",
        subtitle_source=source,
    )

    timeline = builder.build()
    assert timeline.get_track("captions").items() == tuple(captions)


def test_apply_missing_required_param_raises_type_error():
    with pytest.raises(TypeError):
        FacelessQuoteTemplate().apply(_builder(), quote_text="x", music="y.mp3")


def test_apply_twice_with_different_params_yields_structurally_equivalent_timelines():
    timeline_a = (
        FacelessQuoteTemplate()
        .apply(_builder(), background_clip="a.mp4", quote_text="Quote A", music="a.mp3")
        .build()
    )
    timeline_b = (
        FacelessQuoteTemplate()
        .apply(_builder(), background_clip="b.mp4", quote_text="Quote B", music="b.mp3")
        .build()
    )

    assert set(timeline_a.tracks) == set(timeline_b.tracks) == {"main", "overlay", "audio"}
    clip_a = timeline_a.get_track("main").items()[0]
    clip_b = timeline_b.get_track("main").items()[0]
    assert clip_a.asset.path != clip_b.asset.path

    text_a = timeline_a.get_track("overlay").items()[0]
    text_b = timeline_b.get_track("overlay").items()[0]
    assert text_a.text != text_b.text
