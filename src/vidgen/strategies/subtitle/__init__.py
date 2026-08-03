"""Concrete SubtitleSource implementations (Layer 2).

Each of these imports whatever library it needs (``srt``,
``faster-whisper``) and is injected into ``TimelineBuilder.captions()``
by the caller — ``vidgen.builder`` itself never imports this package.
"""

from vidgen.strategies.subtitle.file_source import FileSubtitleSource
from vidgen.strategies.subtitle.hybrid_source import HybridSubtitleSource
from vidgen.strategies.subtitle.whisper_source import WhisperSubtitleSource

__all__ = ["FileSubtitleSource", "WhisperSubtitleSource", "HybridSubtitleSource"]
