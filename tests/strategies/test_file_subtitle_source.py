from pathlib import Path

import pytest

from vidgen.strategies.errors import SubtitleGenerationError
from vidgen.strategies.subtitle.file_source import FileSubtitleSource

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
SAMPLE_SRT = FIXTURE_DIR / "sample.srt"


def test_generate_returns_captions_matching_the_srt_file():
    source = FileSubtitleSource(str(SAMPLE_SRT))

    captions = source.generate(script_text=None, voice_audio="unused.mp3")

    assert [(c.text, c.start, c.end) for c in captions] == [
        ("Hello there", 0.0, 2.0),
        ("General Kenobi", 2.0, 4.5),
    ]


def test_generate_ignores_script_text_and_voice_audio():
    source = FileSubtitleSource(str(SAMPLE_SRT))

    captions = source.generate(script_text="something else entirely", voice_audio="unused.mp3")

    assert captions[0].text == "Hello there"


def test_generate_missing_file_raises_subtitle_generation_error():
    source = FileSubtitleSource(str(FIXTURE_DIR / "does-not-exist.srt"))

    with pytest.raises(SubtitleGenerationError):
        source.generate(script_text=None, voice_audio="unused.mp3")
