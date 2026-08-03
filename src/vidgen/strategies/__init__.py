"""Layer 2 — Render Strategy & provider strategies.

The only layer allowed to import heavy third-party libraries (MoviePy,
Pillow, ``srt``, ``faster-whisper``). Depends on ``vidgen.domain``
(Layer 0) and ``vidgen.builder`` (Layer 1) only. See
docs/ARCHITECTURE.md and docs/DESIGN.md for the full design.
"""
