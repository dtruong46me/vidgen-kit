from pathlib import Path

import pytest

from vidgen.strategies.subtitle.whisper_source import WhisperSubtitleSource

REPO_ROOT = Path(__file__).resolve().parents[2]
VOICE_DIR = REPO_ROOT / "assets" / "voice"
SAMPLE_VOICE = next(VOICE_DIR.glob("*"), None) if VOICE_DIR.is_dir() else None


@pytest.mark.slow
@pytest.mark.skipif(SAMPLE_VOICE is None, reason="no sample voice audio in assets/voice/")
def test_generate_returns_non_empty_captions_with_increasing_timestamps():
    source = WhisperSubtitleSource(model_size="base", device="cpu")

    captions = source.generate(script_text=None, voice_audio=str(SAMPLE_VOICE))

    assert captions
    assert all(c.start < c.end for c in captions)
    assert all(a.start <= b.start for a, b in zip(captions, captions[1:]))
