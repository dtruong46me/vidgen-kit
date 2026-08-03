"""Layer 4 — Automation: Batch Producer.

``BatchProducer`` is the top of the layer stack: it drives ``Script``
(Layer 3) and a ``RenderStrategy`` (Layer 2) to turn a directory of spec
files into rendered videos. ``Agent`` (natural-language-driven generation)
is a documented v2 extension point only — see PLAN.md's roadmap — and has
no class here in v1.
"""

from vidgen.automation.batch_producer import BatchProducer, BatchResult

__all__ = ["BatchProducer", "BatchResult"]
