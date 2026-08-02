# Architecture — vidgen

This document describes **how the system is organized** (layers, class
diagram, package layout). See [PRD.md](PRD.md) for goals/features at the
product level, and [SPEC.md](SPEC.md) for the detailed API of each class.

## 1. Most important design principle

`vidgen` does not handle video/audio at a low level itself — it defines an
**OOP data model** (`Timeline`/`Track`/`Clip`/`Overlay`/`Animation`/
`Transition`) and **orchestrates** existing libraries (MoviePy, Whisper,
Pillow...) to do the work. Swapping the render backend later (MoviePy →
ffmpeg-python) does not affect the public API.

## 2. Layered architecture

Each layer depends only on the layer below it, never upward:

```
┌─────────────────────────────────────────────────────────┐
│ 5. Orchestration   Timeline (facade) · BatchPipeline     │  depends on every layer below
├─────────────────────────────────────────────────────────┤
│ 4. Config           config/spec.py (JSON/YAML -> Timeline)│
├─────────────────────────────────────────────────────────┤
│ 3. Render           RenderBackend (ABC) · MoviePyBackend │  the ONLY layer that imports moviepy
├─────────────────────────────────────────────────────────┤
│ 2. Caption          SubtitleSource (ABC) · File/Whisper/Hybrid │
├─────────────────────────────────────────────────────────┤
│ 2. Asset            Asset · AssetLoader                   │
├─────────────────────────────────────────────────────────┤
│ 1. Domain (core)    Timeline internals · Track · Clip ·   │  does NOT import
│                     Overlay · Animation · Transition ·    │  any render/ASR
│                     Position · TextStyle · Caption        │  library
└─────────────────────────────────────────────────────────┘
```

- **Layer 1 (Domain)**: pure Python dataclasses + abstract base classes,
  no moviepy/whisper imports. Testable without ffmpeg installed.
- **Layer 2 (Asset/Caption)**: builds domain data from external input (media
  files, ASR). Caption depends on an ASR library; Asset depends on
  ffprobe/moviepy only to read metadata.
- **Layer 3 (Render)**: the only place that "understands" MoviePy. Takes a
  pure domain object (`Timeline`) and produces a video file.
- **Layer 4 (Config)**: parses a JSON/YAML spec into calls to the domain API
  — no business logic of its own, just mapping.
- **Layer 5 (Orchestration)**: `Timeline` is the facade users interact with
  day to day; `BatchPipeline` iterates over multiple specs to render in
  bulk.

## 3. OOP class diagram (Domain layer)

```
Track (ABC, generic over item type)
 ├─ VideoTrack     — holds Clip (VideoClip, ImageClip)
 ├─ OverlayTrack   — holds Overlay (TextOverlay, ImageOverlay)
 ├─ AudioTrack     — holds AudioLayer
 └─ CaptionTrack   — holds Caption

Clip (ABC)                          Overlay (ABC)
 ├─ VideoClip                        ├─ TextOverlay  (+ TextStyle, Position, Animation)
 └─ ImageClip                        └─ ImageOverlay (+ Position, Animation)

Animation (ABC)                     Transition (ABC)        — attached between 2 consecutive Clips
 ├─ FadeAnimation                     ├─ CutTransition (default, no effect)
 ├─ SlideAnimation                    ├─ FadeTransition
 └─ ZoomAnimation                     └─ DissolveTransition

Position                            TextStyle
 - Position.preset(Alignment.X)       - font, font_size, color
 - Position.custom(x, y, unit=...)    - outline_color, outline_width
                                      - bg_color, align, max_width

SubtitleSource (ABC)                 RenderBackend (ABC)
 ├─ FileSubtitleSource                 └─ MoviePyBackend
 ├─ WhisperSubtitleSource
 └─ HybridSubtitleSource
```

Every ABC defines abstract methods that subclasses must implement (e.g.
`Track._validate_item()`, `RenderBackend.render()`,
`SubtitleSource.generate()`), keeping roles clear: the base class defines
the "contract", subclasses define the "concrete behavior". See
[SPEC.md](SPEC.md) for field/method details of each class.

## 4. Package structure

```
src/vidgen/
  core/                         # Layer 1 — Domain, no external library dependencies
    timeline.py                  # Timeline: facade + aggregate root
    track.py                      # Track (ABC), VideoTrack, OverlayTrack, AudioTrack, CaptionTrack
    clip.py                        # Clip (ABC), VideoClip, ImageClip
    overlay.py                      # Overlay (ABC), TextOverlay, ImageOverlay
    audio.py                         # AudioLayer
    caption.py                        # Caption
    position.py                        # Position, Alignment (enum)
    style.py                            # TextStyle
    animation.py                         # Animation (ABC), FadeAnimation, SlideAnimation, ZoomAnimation
    transition.py                         # Transition (ABC), CutTransition, FadeTransition, DissolveTransition
  assets/                       # Layer 2
    asset.py                     # Asset (dataclass: path, type, duration, resolution, fps)
    loader.py                     # AssetLoader
  captions/                     # Layer 2
    base.py                       # SubtitleSource (ABC)
    file_source.py
    whisper_source.py
    hybrid_source.py
  render/                       # Layer 3 — the only layer that imports moviepy
    backend.py                    # RenderBackend (ABC)
    moviepy_backend.py
  config/                       # Layer 4
    spec.py                       # parses JSON/YAML -> calls the Timeline API
  pipeline/                     # Layer 5
    batch.py                      # BatchPipeline
  __init__.py                  # exports Timeline, BatchPipeline
tests/
docs/
  PRD.md
  ARCHITECTURE.md
  SPEC.md
  PLAN.md
input/specs/                   # JSON/YAML specs for batch runs
assets/                         # clips/ music/ images/ voice/
output/
```

## 5. Underlying libraries

| Task | Library |
|---|---|
| Video compositing/rendering, basic animation/transitions | `moviepy` (wraps `ffmpeg`) |
| ASR for captions | `faster-whisper` |
| Parsing/writing subtitle files | `srt` |
| Image processing (overlay, resize) | `Pillow` |
| Data model validation / spec JSON parsing | `pydantic` |

---
See also: [PRD.md](PRD.md) · [SPEC.md](SPEC.md) · [PLAN.md](PLAN.md)
