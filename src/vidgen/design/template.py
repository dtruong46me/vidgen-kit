"""Template — reusable parametrized edit recipes (Layer 3).

A ``Template`` encapsulates a repeatable visual structure once (e.g.
"quote video: background clip + centered text + background music +
optional voice/captions") and applies it to a ``TimelineBuilder`` for
arbitrary input parameters — the code-first equivalent of a CapCut/
Premiere template. It is the other of the two ways (alongside ``Script``,
``script.py``) to describe a design above the raw ``TimelineBuilder``
calls.

A concrete ``Template`` declares its actual required parameters as named
keyword arguments in its own ``apply()`` override (not a loose
``**params`` dict) so missing/invalid parameters fail immediately and
legibly with a plain ``TypeError`` from Python — the base class's
``**params`` only exists because different templates need different
parameters and there's no shared signature to enforce.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from vidgen.builder import TimelineBuilder
from vidgen.domain.ports import SubtitleSource
from vidgen.domain.position import Alignment, Position
from vidgen.domain.style import TextStyle
from vidgen.strategies.subtitle import HybridSubtitleSource


class Template(ABC):
    """Base class for a reusable, parametrized ``TimelineBuilder`` recipe."""

    @abstractmethod
    def apply(self, builder: TimelineBuilder, **params: Any) -> TimelineBuilder:
        """Apply this template's recipe to ``builder`` and return it.

        Returns the same ``TimelineBuilder`` it was given (still
        chainable), so a template can be combined with extra manual
        ``.text()``/``.image()`` calls before ``.build()``.
        """
        raise NotImplementedError


class FacelessQuoteTemplate(Template):
    """Background clip + centered quote text + background music, with
    optional voice narration/captions."""

    def apply(
        self,
        builder: TimelineBuilder,
        *,
        background_clip: str,
        quote_text: str,
        music: str,
        voice_audio: str | None = None,
        style: TextStyle | None = None,
        subtitle_source: SubtitleSource | None = None,
    ) -> TimelineBuilder:
        builder.clip(background_clip, start=0)
        builder.text(
            quote_text,
            start=0,
            end=None,
            position=Position.preset(Alignment.CENTER),
            style=style or TextStyle(),
        )
        builder.audio(music, volume=0.3)
        if voice_audio:
            builder.captions(
                subtitle_source or HybridSubtitleSource(),
                script_text=quote_text,
                voice_audio=voice_audio,
            )
        return builder
