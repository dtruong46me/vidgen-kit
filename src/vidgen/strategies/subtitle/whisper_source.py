"""WhisperSubtitleSource — ASR-based caption generation via
faster-whisper (Layer 2).

Used when there is no known-correct script text to align against; see
``hybrid_source.py`` for the script-aware alternative that avoids
Whisper's text-recognition errors.
"""

from faster_whisper import WhisperModel

from vidgen.domain.caption import Caption
from vidgen.domain.ports import SubtitleSource
from vidgen.strategies.errors import SubtitleGenerationError


class WhisperSubtitleSource(SubtitleSource):
    """Transcribes ``voice_audio`` with ``faster-whisper``.

    Attributes:
        model_size: Whisper model size/name (e.g. ``"base"``, ``"small"``).
        device: Inference device, e.g. ``"cpu"`` or ``"cuda"``.
    """

    def __init__(self, model_size: str = "base", device: str = "cpu") -> None:
        self.model_size = model_size
        self.device = device

    def generate(self, *, script_text: str | None, voice_audio: str) -> list[Caption]:
        """Transcribe ``voice_audio`` into timed ``Caption``s.

        ``script_text`` is ignored — this source relies entirely on
        Whisper's own recognized text.
        """
        try:
            model = WhisperModel(self.model_size, device=self.device)
            segments, _info = model.transcribe(voice_audio)
            return [
                Caption(text=segment.text.strip(), start=segment.start, end=segment.end)
                for segment in segments
            ]
        except Exception as exc:  # noqa: BLE001 - wrap any faster-whisper/model failure
            raise SubtitleGenerationError(
                f"could not transcribe voice audio at {voice_audio!r}: {exc}"
            ) from exc
