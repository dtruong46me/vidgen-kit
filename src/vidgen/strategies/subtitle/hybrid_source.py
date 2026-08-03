"""HybridSubtitleSource — known-correct script text, Whisper only for
timing alignment (Layer 2).

Recommended default for batch production: the caller already knows the
exact narration text, so Whisper's own (error-prone) speech recognition
is used only to find *when* each chunk of that text is spoken, never to
supply the caption text itself. This eliminates ASR text-recognition
errors while still getting per-caption timestamps automatically.
"""

from faster_whisper import WhisperModel

from vidgen.domain.caption import Caption
from vidgen.domain.ports import SubtitleSource
from vidgen.strategies.errors import SubtitleGenerationError


class HybridSubtitleSource(SubtitleSource):
    """Aligns known ``script_text`` to ``voice_audio`` via Whisper timing.

    Attributes:
        model_size: Whisper model size/name (e.g. ``"base"``, ``"small"``).
        device: Inference device, e.g. ``"cpu"`` or ``"cuda"``.
    """

    def __init__(self, model_size: str = "base", device: str = "cpu") -> None:
        self.model_size = model_size
        self.device = device

    def generate(self, *, script_text: str | None, voice_audio: str) -> list[Caption]:
        """Align ``script_text`` to ``voice_audio``'s timing.

        Raises:
            ValueError: ``script_text`` is ``None`` or empty.
            SubtitleGenerationError: the underlying transcription failed.
        """
        if not script_text:
            raise ValueError("HybridSubtitleSource requires script_text")

        try:
            model = WhisperModel(self.model_size, device=self.device)
            segments, _info = model.transcribe(voice_audio)
            return self._align(script_text, segments)
        except ValueError:
            raise
        except Exception as exc:  # noqa: BLE001 - wrap any faster-whisper/model failure
            raise SubtitleGenerationError(
                f"could not align script to voice audio at {voice_audio!r}: {exc}"
            ) from exc

    @staticmethod
    def _align(script_text: str, segments) -> list[Caption]:
        """Distribute ``script_text`` words across ASR segment timestamps.

        Each Whisper segment contributes only its ``[start, end)`` timing
        — never its recognized text. The same number of words Whisper
        recognized in that segment is instead pulled, in order, from the
        real script, so the returned captions' text always matches the
        script verbatim.
        """
        words = script_text.split()
        word_index = 0
        captions: list[Caption] = []

        for segment in segments:
            if word_index >= len(words):
                break
            segment_word_count = max(len(segment.text.strip().split()), 1)
            chunk = words[word_index : word_index + segment_word_count]
            word_index += segment_word_count
            captions.append(
                Caption(text=" ".join(chunk), start=segment.start, end=segment.end)
            )

        if word_index < len(words) and captions:
            leftover = words[word_index:]
            last = captions[-1]
            captions[-1] = Caption(
                text=f"{last.text} {' '.join(leftover)}", start=last.start, end=last.end
            )

        return captions
