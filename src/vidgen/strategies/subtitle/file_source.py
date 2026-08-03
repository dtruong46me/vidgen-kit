"""FileSubtitleSource — reads captions from an existing .srt/.vtt file
(Layer 2)."""

import srt

from vidgen.domain.caption import Caption
from vidgen.domain.ports import SubtitleSource
from vidgen.strategies.errors import SubtitleGenerationError


class FileSubtitleSource(SubtitleSource):
    """Parses an existing subtitle file instead of generating captions.

    Attributes:
        path: Path to the ``.srt`` file to parse.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def generate(self, *, script_text: str | None, voice_audio: str) -> list[Caption]:
        """Parse ``self.path`` into ``Caption``s.

        ``script_text``/``voice_audio`` are ignored — the file already
        has both text and timing.
        """
        try:
            with open(self.path, encoding="utf-8") as handle:
                subtitles = srt.parse(handle.read())
                return [
                    Caption(
                        text=sub.content,
                        start=sub.start.total_seconds(),
                        end=sub.end.total_seconds(),
                    )
                    for sub in subtitles
                ]
        except (OSError, srt.SRTParseError) as exc:
            raise SubtitleGenerationError(
                f"could not parse subtitle file at {self.path!r}: {exc}"
            ) from exc
