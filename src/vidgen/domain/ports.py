"""SubtitleSource — abstract port for caption generation (Layer 0).

This is the one place Layer 0 declares a contract that Layer 2
implements: the ABC itself has zero third-party imports, while its
concrete implementations (Whisper/srt-backed) live entirely in Layer 2
and get injected into ``TimelineBuilder.captions()`` by the caller. This
is dependency injection in service of the one-way Dependency Inversion
rule (see docs/ARCHITECTURE.md).
"""

from abc import ABC, abstractmethod

from vidgen.domain.caption import Caption


class SubtitleSource(ABC):
    """A pluggable strategy for producing ``Caption``s.

    Concrete implementations may ignore ``script_text`` (pure ASR) or
    require it (hybrid alignment) — the signature stays uniform across
    every ``SubtitleSource`` so ``TimelineBuilder.captions()`` can call
    any of them the same way. Anything source-specific (e.g. a ``.srt``
    file path, a Whisper model size) belongs on the concrete class's
    constructor, not in this method signature.
    """

    @abstractmethod
    def generate(
        self, *, script_text: str | None, voice_audio: str
    ) -> list[Caption]:
        """Produce the list of captions for a piece of voice audio.

        Args:
            script_text: The known-correct script text, if available.
                Required by hybrid sources, ignored by pure-ASR sources.
            voice_audio: Path to the voice/narration audio file to
                transcribe and/or align captions against.

        Returns:
            Captions in chronological order.
        """
        raise NotImplementedError
