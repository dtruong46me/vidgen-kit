"""Registry of ``Template``\\ s exposed over the API.

Adding a new ``Template`` to the API only requires registering its class
here — the ``GET /templates`` listing and its parameter description are
derived by introspecting ``apply()``'s signature, not hand-maintained.
"""

from __future__ import annotations

import inspect
from typing import Any

from vidgen.design.template import FacelessQuoteTemplate, Template

TEMPLATES: dict[str, type[Template]] = {
    "faceless_quote": FacelessQuoteTemplate,
}


def get_template(name: str) -> type[Template] | None:
    return TEMPLATES.get(name)


def describe_template(name: str, template_cls: type[Template]) -> dict[str, Any]:
    """Build a ``GET /templates`` entry from ``template_cls.apply()``'s signature."""
    signature = inspect.signature(template_cls.apply)
    params = []
    for param_name, param in signature.parameters.items():
        if param_name in ("self", "builder"):
            continue
        params.append(
            {
                "name": param_name,
                "required": param.default is inspect.Parameter.empty,
                "type": _annotation_to_str(param.annotation),
            }
        )
    return {
        "name": name,
        "description": (template_cls.__doc__ or "").strip().splitlines()[0] if template_cls.__doc__ else "",
        "params": params,
    }


def _annotation_to_str(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "any"
    return getattr(annotation, "__name__", str(annotation))


def list_templates() -> list[dict[str, Any]]:
    return [describe_template(name, cls) for name, cls in sorted(TEMPLATES.items())]
