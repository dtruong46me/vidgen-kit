"""BatchProducer — turns a directory of Script specs into rendered videos
(Layer 4).

This is one consumer built *on top* of the engine (Script → TimelineBuilder
→ RenderStrategy), not what the engine fundamentally is. It is allowed to
import every layer below it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from vidgen.design.script import Script
from vidgen.strategies.render import MoviePyRenderStrategy, RenderStrategy

logger = logging.getLogger("vidgen.automation")

_SPEC_GLOBS = ("*.json", "*.yaml", "*.yml")


@dataclass
class BatchResult:
    """The outcome of one ``BatchProducer.run()`` call."""

    succeeded: list[Path] = field(default_factory=list)
    failed: list[tuple[Path, Exception]] = field(default_factory=list)


class BatchProducer:
    """Renders every spec file in ``spec_dir`` to ``output_dir``.

    Attributes:
        spec_dir: Directory containing ``.json``/``.yaml``/``.yml`` spec files.
        render_strategy: The ``RenderStrategy`` used to render each parsed
            ``Timeline``. Defaults to ``MoviePyRenderStrategy()``.
    """

    def __init__(self, spec_dir: str, render_strategy: RenderStrategy | None = None) -> None:
        self.spec_dir = spec_dir
        self.render_strategy = render_strategy if render_strategy is not None else MoviePyRenderStrategy()

    def run(self, output_dir: str) -> BatchResult:
        """Parse and render every spec file in ``spec_dir``, in filename order.

        One spec failing to parse or render (``ScriptValidationError``,
        ``RenderError``, or anything else) is logged and recorded in the
        returned ``BatchResult.failed`` — it never stops the batch.
        """
        output_dir_path = Path(output_dir)
        result = BatchResult()

        for spec_path in self._list_spec_files():
            try:
                timeline = Script(str(spec_path)).parse().build()
                output_path = self.render_strategy.render(
                    timeline, str(output_dir_path / f"{spec_path.stem}.mp4")
                )
                result.succeeded.append(Path(output_path))
            except Exception as exc:  # noqa: BLE001 - one bad spec must never stop the batch
                logger.error("failed to produce %s: %s", spec_path.name, exc)
                result.failed.append((spec_path, exc))

        return result

    def _list_spec_files(self) -> list[Path]:
        spec_dir_path = Path(self.spec_dir)
        paths = {p for pattern in _SPEC_GLOBS for p in spec_dir_path.glob(pattern)}
        return sorted(paths, key=lambda p: p.name)
