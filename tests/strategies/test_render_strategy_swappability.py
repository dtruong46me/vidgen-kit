from pathlib import Path

from vidgen.builder import TimelineBuilder
from vidgen.domain import Alignment, Position
from vidgen.domain.timeline import Timeline
from vidgen.strategies.render.base import RenderStrategy


class StubRenderStrategy(RenderStrategy):
    """A fake RenderStrategy standing in for MoviePyRenderStrategy.

    Records the Timeline it was asked to render instead of touching
    MoviePy/ffmpeg at all — proves a renderer can be swapped in without
    any change to builder/ or domain/ code.
    """

    def __init__(self):
        self.rendered: list[tuple[Timeline, str]] = []

    def render(self, timeline: Timeline, output_path: str) -> Path:
        self.rendered.append((timeline, output_path))
        return Path(output_path)


def test_stub_render_strategy_swaps_in_for_moviepy_without_touching_builder_or_domain():
    timeline = (
        TimelineBuilder(resolution=(1080, 1920), fps=30)
        .clip("assets/clips/a.mp4", start=0, end=5)
        .text("hi", 0, 1, position=Position.preset(Alignment.CENTER))
        .build()
    )
    strategy = StubRenderStrategy()

    result = strategy.render(timeline, "output/fake.mp4")

    assert result == Path("output/fake.mp4")
    assert strategy.rendered == [(timeline, "output/fake.mp4")]
