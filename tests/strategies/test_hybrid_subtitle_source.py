from pathlib import Path
from types import SimpleNamespace

import pytest

from vidgen.strategies.subtitle.hybrid_source import HybridSubtitleSource

REPO_ROOT = Path(__file__).resolve().parents[2]
VOICE_DIR = REPO_ROOT / "assets" / "voice"
SAMPLE_VOICE = next(VOICE_DIR.glob("*"), None) if VOICE_DIR.is_dir() else None


def _segment(text: str, start: float, end: float) -> SimpleNamespace:
    """A minimal stand-in for faster-whisper's Segment — only the
    attributes HybridSubtitleSource._align() actually reads."""
    return SimpleNamespace(text=text, start=start, end=end)


def test_generate_raises_when_script_text_is_missing():
    source = HybridSubtitleSource()

    with pytest.raises(ValueError, match="script_text"):
        source.generate(script_text=None, voice_audio="unused.mp3")


def test_generate_raises_when_script_text_is_empty():
    source = HybridSubtitleSource()

    with pytest.raises(ValueError, match="script_text"):
        source.generate(script_text="", voice_audio="unused.mp3")


def test_align_takes_text_from_script_not_from_segments():
    segments = [_segment("foo bar", 0.0, 1.0), _segment("baz", 1.0, 2.0)]

    captions = HybridSubtitleSource._align("hello world quux", segments)

    assert [c.text for c in captions] == ["hello world", "quux"]
    assert [(c.start, c.end) for c in captions] == [(0.0, 1.0), (1.0, 2.0)]


def test_align_appends_leftover_script_words_to_last_caption():
    segments = [_segment("one", 0.0, 1.0)]

    captions = HybridSubtitleSource._align("uno dos tres", segments)

    assert len(captions) == 1
    assert captions[0].text == "uno dos tres"


def test_align_stops_when_script_words_run_out():
    segments = [_segment("one", 0.0, 1.0), _segment("two words", 1.0, 2.0), _segment("x", 2.0, 3.0)]

    captions = HybridSubtitleSource._align("only two", segments)

    assert [c.text for c in captions] == ["only", "two"]


@pytest.mark.slow
@pytest.mark.skipif(SAMPLE_VOICE is None, reason="no sample voice audio in assets/voice/")
def test_generate_aligns_real_script_to_real_audio():
    source = HybridSubtitleSource()
    script_text = "this is a placeholder script matching the sample voice clip"

    captions = source.generate(script_text=script_text, voice_audio=str(SAMPLE_VOICE))

    assert captions
    assert " ".join(c.text for c in captions) == script_text
    assert all(a.start <= b.start for a, b in zip(captions, captions[1:]))
