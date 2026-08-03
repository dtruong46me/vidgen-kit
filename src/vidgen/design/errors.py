"""Shared exceptions for the design layer (Layer 3)."""


class ScriptValidationError(ValueError):
    """``Script.parse()`` could not validate the spec file's contents.

    Wraps the underlying ``pydantic.ValidationError``; the message
    includes the failing field path(s).
    """
