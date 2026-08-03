"""Transition presets between two consecutive clips on a VideoTrack
(Layer 0).

Like ``animation.py``, this module only declares *what* transition is
attached; the actual compositing logic is implemented by a
``RenderStrategy`` in Layer 2, so ``_apply`` is intentionally left
unimplemented here.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Transition(ABC):
    """Base class for a transition between two consecutive ``VideoClip``s.

    Attributes:
        duration: Length of the transition in seconds.
    """

    duration: float = 0

    @abstractmethod
    def _apply(
        self, outgoing_clip: Any, incoming_clip: Any, backend_ctx: Any
    ) -> Any:
        """Composite the outgoing/incoming clips across this transition.

        Called only by a ``RenderStrategy`` at render time. Implemented
        in Layer 2 once ``MoviePyRenderStrategy`` exists (see
        docs/DESIGN.md, Layer 2); left unimplemented here on purpose.
        """
        raise NotImplementedError


@dataclass
class CutTransition(Transition):
    """Default transition: a straight cut, no visual effect.

    ``duration`` is always forced to ``0`` regardless of what is passed
    in — a cut is instantaneous by definition.
    """

    def __post_init__(self) -> None:
        self.duration = 0

    def _apply(
        self, outgoing_clip: Any, incoming_clip: Any, backend_ctx: Any
    ) -> Any:
        # Implemented in Layer 2 (RenderStrategy) — see docs/DESIGN.md.
        raise NotImplementedError


@dataclass
class FadeTransition(Transition):
    """Outgoing clip fades to black, incoming clip fades in, over
    ``duration``."""

    def _apply(
        self, outgoing_clip: Any, incoming_clip: Any, backend_ctx: Any
    ) -> Any:
        # Implemented in Layer 2 (RenderStrategy) — see docs/DESIGN.md.
        raise NotImplementedError


@dataclass
class DissolveTransition(Transition):
    """Crossfade between the outgoing and incoming clip over
    ``duration``."""

    def _apply(
        self, outgoing_clip: Any, incoming_clip: Any, backend_ctx: Any
    ) -> Any:
        # Implemented in Layer 2 (RenderStrategy) — see docs/DESIGN.md.
        raise NotImplementedError
