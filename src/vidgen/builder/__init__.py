"""Layer 1 — Builder API.

Fluent, chainable construction of a ``Timeline``. Depends only on
``vidgen.domain`` (Layer 0). See docs/ARCHITECTURE.md and docs/DESIGN.md
for the full design.
"""

from vidgen.builder.timeline_builder import TimelineBuilder

__all__ = ["TimelineBuilder"]
