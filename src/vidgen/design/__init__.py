"""Layer 3 — Design: Script & Template.

``Script`` (declarative JSON/YAML) and ``Template`` (parametrized Python
recipe) are the two ways to describe a design above the raw
``TimelineBuilder`` calls (Layer 1). This layer is allowed to import
Layer 0, 1, and 2 — in particular, ``Script.parse()`` and
``FacelessQuoteTemplate.apply()`` construct concrete ``SubtitleSource``
implementations from ``vidgen.strategies.subtitle`` (Layer 2).
"""

from vidgen.design.script import Script
from vidgen.design.template import FacelessQuoteTemplate, Template

__all__ = ["Script", "Template", "FacelessQuoteTemplate"]
