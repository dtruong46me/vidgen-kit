"""Render strategies — turn a ``Timeline`` into a rendered video file."""

from vidgen.strategies.render.base import RenderStrategy
from vidgen.strategies.render.moviepy_strategy import MoviePyRenderStrategy

__all__ = ["RenderStrategy", "MoviePyRenderStrategy"]
