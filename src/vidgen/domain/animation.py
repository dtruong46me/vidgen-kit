"""Animation presets attached to overlays/clips (Layer 0).

Only *what* animation is attached and its parameters are declared here.
*How* an animation is actually rendered is implemented by a
``RenderStrategy`` in Layer 2 (e.g. via MoviePy calls) — Layer 0 must
stay ignorant of that, so ``_apply`` is intentionally left unimplemented
in this module.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class Animation(ABC):
    """Base class for entrance/exit animation presets.

    Attributes:
        duration: Length of the animation in seconds.
    """

    duration: float

    def __post_init__(self) -> None:
        if self.duration < 0:
            raise ValueError(f"duration must be >= 0, got {self.duration!r}")

    @abstractmethod
    def _apply(self, clip: Any, backend_ctx: Any) -> Any:
        """Apply this animation to a render-backend clip object.

        Called only by a ``RenderStrategy`` at render time — never by
        domain/builder code. Implemented in Layer 2 once
        ``MoviePyRenderStrategy`` exists (see docs/DESIGN.md, Layer 2);
        left unimplemented here on purpose.
        """
        raise NotImplementedError


@dataclass
class FadeAnimation(Animation):
    """Fade opacity in or out over ``duration``.

    Attributes:
        direction: Whether the overlay/clip fades ``"in"`` or ``"out"``.
    """

    direction: Literal["in", "out"]

    def _apply(self, clip: Any, backend_ctx: Any) -> Any:
        # Implemented in Layer 2 (RenderStrategy) — see docs/DESIGN.md.
        raise NotImplementedError


@dataclass
class SlideAnimation(Animation):
    """Slide in/out from a screen edge over ``duration``.

    Attributes:
        direction: The screen edge the slide moves from/to.
    """

    direction: Literal["left", "right", "top", "bottom"]

    def _apply(self, clip: Any, backend_ctx: Any) -> Any:
        # Implemented in Layer 2 (RenderStrategy) — see docs/DESIGN.md.
        raise NotImplementedError


@dataclass
class ZoomAnimation(Animation):
    """Scale in/out over ``duration``.

    Attributes:
        direction: Whether the overlay/clip zooms ``"in"`` or ``"out"``.
    """

    direction: Literal["in", "out"]

    def _apply(self, clip: Any, backend_ctx: Any) -> Any:
        # Implemented in Layer 2 (RenderStrategy) — see docs/DESIGN.md.
        raise NotImplementedError
