"""Shared exception hierarchy for Layer 2 (strategies).

Failures from the underlying third-party libraries (MoviePy/ffmpeg,
``srt``, ``faster-whisper``) are wrapped in one of these instead of
propagating the raw library exception, so callers can catch
strategy-level failures precisely and still get the offending
path/context in the message.
"""


class AssetResolutionError(RuntimeError):
    """``AssetLoader.resolve()`` could not read an asset's metadata."""


class RenderError(RuntimeError):
    """A ``RenderStrategy`` failed to render a ``Timeline``."""


class SubtitleGenerationError(RuntimeError):
    """A ``SubtitleSource`` failed to generate captions."""
