"""Layer 5 — HTTP API.

A thin FastAPI wrapper around ``design`` (Script/Template) and
``strategies.render`` (Layer 2), exposing render jobs over HTTP behind
an in-memory async job queue (``jobs.py``). This is one more consumer
built *on top* of the engine — same relationship ``automation/`` has to
the rest of the stack — not a replacement for using vidgen as a library.
"""

from vidgen.api.app import create_app

__all__ = ["create_app"]
