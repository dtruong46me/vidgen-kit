"""RenderStrategy — abstract contract for turning a Timeline into a
rendered video file (Layer 2).

Kept in its own module, separate from any concrete implementation, so a
new renderer (e.g. a future ``FFmpegRenderStrategy``) can be added
without importing MoviePy at all — only ``moviepy_strategy.py`` does
that.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from vidgen.domain.timeline import Timeline


class RenderStrategy(ABC):
    """A pluggable strategy for rendering a ``Timeline`` to a file.

    Swapping the concrete ``RenderStrategy`` (e.g. MoviePy vs. a future
    FFmpeg-based one) requires no change to ``Timeline``,
    ``TimelineBuilder``, or any other caller — that's the whole point of
    this being a Strategy-pattern seam at Layer 2.
    """

    @abstractmethod
    def render(self, timeline: Timeline, output_path: str) -> Path:
        """Render ``timeline`` and write the result to ``output_path``.

        Returns:
            The path the output file was written to.
        """
        raise NotImplementedError
