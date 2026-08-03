# Architecture — vidgen

This document describes **how the system is organized** (layers, class
diagram, package layout). See [PRD.md](PRD.md) for goals/features at the
product level, and [SPEC.md](SPEC.md) for the detailed API of each class.

## 1. Most important design principle: Dependency Inversion

vidgen is a programmable **video editing engine** — a code-first library in
the spirit of what powers CapCut/Premiere, not a batch script. Its
architecture follows strict **Dependency Inversion**: dependencies only
point downward. A higher layer may depend on any layer(s) below it; a lower
layer must never import from a layer above it.

```
Layer 4  Automation / Agent / Batch Producer
              ↓ depends on
Layer 3  Design / Template / Script
              ↓ depends on
Layer 2  Render Strategy    (implementation, replaceable)
              ↓ depends on
Layer 1  Builder API        (fluent interface)
              ↓ depends on
Layer 0  Domain Model       (pure data, no moviepy/ffmpeg import)
```

**Layer 0 has zero third-party imports.** This is the precondition for
swapping the renderer later (MoviePy → ffmpeg-python, or adding a second
backend) without touching 90% of the codebase — every other layer is built
so it can change independently as long as it still honors Layer 0's data
model.

## 2. The five layers

```
┌─────────────────────────────────────────────────────────────────┐
│ 4. Automation/Agent/Batch Producer   BatchProducer               │  depends on every layer below
├─────────────────────────────────────────────────────────────────┤
│ 3. Design/Template/Script            Script · Template            │
├─────────────────────────────────────────────────────────────────┤
│ 2. Render Strategy   RenderStrategy(ABC) · MoviePyRenderStrategy  │  the ONLY layer that imports
│                       AssetLoader · SubtitleSource implementations │  moviepy / ffprobe / whisper
├─────────────────────────────────────────────────────────────────┤
│ 1. Builder API        TimelineBuilder (fluent, chainable)         │
├─────────────────────────────────────────────────────────────────┤
│ 0. Domain Model        Timeline · Track · Clip · Overlay ·        │  does NOT import
│                        Animation · Transition · Position ·        │  any external library
│                        TextStyle · Caption · Asset ·               │  at all
│                        SubtitleSource (abstract port)              │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Contains | May depend on | Responsibility |
|---|---|---|---|
| **0. Domain Model** | `Timeline`, `Track`+subclasses, `Clip`/`Overlay`+subclasses, `Animation`/`Transition`+subclasses, `Position`, `TextStyle`, `Caption`, `Asset`, `SubtitleSource` (ABC only) | nothing | Pure data + integrity rules (e.g. "a `VideoTrack` only accepts `Clip`s"). Testable with plain `pytest`, no ffmpeg/whisper installed. |
| **1. Builder API** | `TimelineBuilder` | Layer 0 | The fluent, chainable, official way to construct a `Timeline`. Every method returns the builder itself; `.build()` is the only way out to a `Timeline`. |
| **2. Render Strategy** | `RenderStrategy` (ABC) + `MoviePyRenderStrategy`; sibling provider strategies `AssetLoader`, `FileSubtitleSource`/`WhisperSubtitleSource`/`HybridSubtitleSource` | Layer 0, Layer 1 | Turns a `Timeline` into an actual video file, and resolves real-world data (media metadata, ASR captions) — the only place heavy third-party libraries are imported. Swappable: a new `RenderStrategy` implementation doesn't change `Timeline` or `TimelineBuilder`. |
| **3. Design/Template/Script** | `Script` (declarative JSON/YAML), `Template` (reusable parametrized code recipe) | Layers 0–2 | Two ways to express *what to build* above raw `TimelineBuilder` calls: data-driven (`Script`) or code-driven-and-reusable (`Template`). |
| **4. Automation/Agent/Batch Producer** | `BatchProducer` | all layers below | Drives many `Script`/`Template` instances through the stack to produce many videos. `Agent` (natural-language-driven generation) is a documented extension point here for v2 — see [PLAN.md](PLAN.md) — not designed yet. |

### Three design resolutions that keep the rule honest

- **Rendering is not a `TimelineBuilder` method.** `TimelineBuilder.build()`
  returns a plain `Timeline` (Layer 0). Rendering is a separate call —
  `SomeRenderStrategy().render(timeline, "out.mp4")` — made by whatever sits
  above the stack (Layer 3/4, or application code). This keeps Layer 1 free
  of any Layer 2 import.
- **Asset metadata resolution happens at render time, not build time.**
  `TimelineBuilder.clip(path, ...)` just stores `Asset(path=path)` — no
  `ffprobe` call. `RenderStrategy` resolves duration/resolution/fps via
  `AssetLoader` only when it actually renders. Layer 1 never needs
  `ffprobe`/MoviePy.
- **Captions are injected, not constructed internally.** `SubtitleSource` is
  declared as an abstract *port* in Layer 0 (zero third-party imports); its
  concrete implementations (`FileSubtitleSource`, `WhisperSubtitleSource`,
  `HybridSubtitleSource`) live in Layer 2. The caller passes a concrete
  instance into `TimelineBuilder.captions(source, ...)` — `TimelineBuilder`
  itself only ever references the Layer-0 abstraction.

## 3. OOP class diagram

```
Track (ABC, generic over item type)                — Layer 0
 ├─ VideoTrack     — holds Clip (VideoClip, ImageClip)
 ├─ OverlayTrack   — holds Overlay (TextOverlay, ImageOverlay)
 ├─ AudioTrack     — holds AudioLayer
 └─ CaptionTrack   — holds Caption

Clip (ABC)                          Overlay (ABC)                  — Layer 0
 ├─ VideoClip                        ├─ TextOverlay  (+ TextStyle, Position, Animation)
 └─ ImageClip                        └─ ImageOverlay (+ Position, Animation)

Animation (ABC)                     Transition (ABC)                — Layer 0
 ├─ FadeAnimation                     ├─ CutTransition (default, no effect)
 ├─ SlideAnimation                    ├─ FadeTransition
 └─ ZoomAnimation                     └─ DissolveTransition

Position                            TextStyle                       — Layer 0
 - Position.preset(Alignment.X)       - font, font_size, color
 - Position.custom(x, y, unit=...)    - outline_color, outline_width
                                      - bg_color, align, max_width

SubtitleSource (ABC, port)          Asset (dataclass)                — Layer 0
                                       - path, type, duration=None,
                                         resolution=None, fps=None

TimelineBuilder                                                       — Layer 1
 - .track() .clip() .clips() .text() .image() .audio() .captions() .build()

RenderStrategy (ABC)                Provider strategies               — Layer 2
 └─ MoviePyRenderStrategy            ├─ AssetLoader
                                      ├─ FileSubtitleSource
                                      ├─ WhisperSubtitleSource
                                      └─ HybridSubtitleSource

Script                              Template (ABC)                    — Layer 3
                                      └─ e.g. FacelessQuoteTemplate

BatchProducer                                                          — Layer 4
```

Every ABC defines abstract methods that subclasses must implement (e.g.
`Track._validate_item()`, `RenderStrategy.render()`,
`SubtitleSource.generate()`, `Template.apply()`), keeping roles clear: the
base class defines the "contract", subclasses define the "concrete
behavior". See [SPEC.md](SPEC.md) for field/method details of each class.

## 4. Package structure

```
src/vidgen/
  domain/                        # Layer 0 — pure data, zero third-party imports
    timeline.py                   # Timeline (resolution, fps, tracks)
    track.py                       # Track (ABC), VideoTrack, OverlayTrack, AudioTrack, CaptionTrack
    clip.py                         # Clip (ABC), VideoClip, ImageClip
    overlay.py                       # Overlay (ABC), TextOverlay, ImageOverlay
    audio.py                          # AudioLayer
    caption.py                         # Caption
    asset.py                            # Asset (dataclass: path, type, duration/resolution/fps optional)
    position.py                          # Position, Alignment (enum)
    style.py                              # TextStyle
    animation.py                           # Animation (ABC), FadeAnimation, SlideAnimation, ZoomAnimation
    transition.py                           # Transition (ABC), CutTransition, FadeTransition, DissolveTransition
    ports.py                                 # SubtitleSource (ABC) — abstract port, no srt/whisper import
  builder/                       # Layer 1 — fluent construction API
    timeline_builder.py            # TimelineBuilder
  strategies/                    # Layer 2 — swappable implementations, only place importing heavy libs
    render/
      base.py                      # RenderStrategy (ABC)
      moviepy_strategy.py           # MoviePyRenderStrategy
    asset/
      loader.py                     # AssetLoader
    subtitle/
      file_source.py                # FileSubtitleSource
      whisper_source.py              # WhisperSubtitleSource
      hybrid_source.py                # HybridSubtitleSource
  design/                        # Layer 3 — Script + Template
    script.py                      # Script: parses JSON/YAML -> TimelineBuilder calls
    template.py                     # Template (ABC): apply(builder, **params) -> TimelineBuilder
  automation/                    # Layer 4 — Automation / Agent / Batch Producer
    batch_producer.py              # BatchProducer
  __init__.py                  # exports TimelineBuilder, BatchProducer
tests/
docs/
  PRD.md
  ARCHITECTURE.md
  SPEC.md
  DESIGN.md
  PLAN.md
input/specs/                   # Script (JSON/YAML) files for batch runs
assets/                         # clips/ music/ images/ voice/
output/
```

## 5. Underlying libraries

All third-party imports live in Layer 2 — grouped here by which strategy
uses which library:

| Layer 2 strategy | Library | Purpose |
|---|---|---|
| `MoviePyRenderStrategy` | `moviepy` (wraps `ffmpeg`) | Compositing/rendering video, basic animation/transitions |
| `AssetLoader` | `moviepy` / `ffprobe` | Reading media metadata (duration, resolution, fps) |
| `WhisperSubtitleSource`, `HybridSubtitleSource` | `faster-whisper` | ASR / timestamp alignment for captions |
| `FileSubtitleSource` | `srt` | Parsing/writing subtitle files |
| `MoviePyRenderStrategy` (image overlays) | `Pillow` | Image processing (overlay, resize) |
| `Script` | `pydantic` | Validating/parsing spec JSON |

---
See also: [PRD.md](PRD.md) · [SPEC.md](SPEC.md) · [DESIGN.md](DESIGN.md) · [PLAN.md](PLAN.md)
