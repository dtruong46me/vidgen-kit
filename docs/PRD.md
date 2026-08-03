# PRD — vidgen

This document answers **what vidgen is, who it's for, and what it does and
doesn't do** — at the product level, not the technical level. See
[ARCHITECTURE.md](ARCHITECTURE.md) for how the system is organized, and
[SPEC.md](SPEC.md) for the detailed API.

## 1. Goals & non-goals

**Goal**: vidgen is a programmable, code-first **video editing engine** —
the kind of model that could power a tool like CapCut/Premiere/Adobe, but
consumed as a Python library/SDK rather than a GUI app. Every editing
operation (cut/join clips, text/image overlays with animation, transitions,
audio mixing, captions, rendering) is expressed through a fluent Builder API
sitting on top of a pure domain model that has no idea *how* rendering
actually happens (Dependency Inversion — see
[ARCHITECTURE.md §1](ARCHITECTURE.md#1-most-important-design-principle-dependency-inversion)).
Automated batch production is one thing you can build *on top* of this
engine (its topmost layer) — it is not what the engine fundamentally is.

**Non-goals (v1 scope, not architectural ceiling)**: v1 does not attempt
full professional-editor feature *depth* — no color grading, no freely
nested multi-track compositing, no arbitrary keyframe/easing animation.
Animation/transitions are still a **fixed preset set** (fade, slide, zoom,
dissolve...), not a general animation engine (see
[SPEC.md §6](SPEC.md#6-animation--transition--basic-presets-layer-0)). This
is a deliberate scope choice for v1, not a limit baked into the
architecture: the layering (Builder API separated from Render Strategy
separated from Domain Model, see ARCHITECTURE.md) exists specifically so
richer animation, alternate render backends, or new automation modes (an AI
Agent) can be added later without breaking existing code.

## 2. Audience & use case

Developers building on top of a programmable video editing engine —
whether that means scripted one-off edits, reusable **Templates** (a
repeatable visual structure reapplied to new inputs, e.g. "quote video:
background clip + centered text + music"), or fully automated batch
pipelines (e.g. "faceless" videos from a script + assets + voiceover +
captions, run over hundreds of inputs). vidgen is the engine; *how* you
drive it — by hand in a script, via a declarative `Script` (JSON/YAML), via
a `Template`, or eventually via an AI `Agent` — is a choice at the top of
the layer stack, not something baked into the core.

## 3. Features (v1 scope)

- **Fluent Builder API** (`TimelineBuilder`): chainable method calls to
  assemble an edit in code — see
  [SPEC.md §2](SPEC.md#2-timelinebuilder--fluent-construction-api-layer-1)
- Cut/join clips on a timeline (trim, concat, basic transitions between
  clips: cut/fade/dissolve)
- Text overlay: fully customizable font/size/color/outline, positioned via
  alignment presets (center, left, right, 4 corners...) or free coordinates
- Image overlay/watermark, using the same positioning mechanism as above
- Basic entrance/exit animation for overlays: fade in/out, slide, zoom
- Audio: mix background music + existing voiceover audio (volume, fade
  in/out)
- Captions/subtitles, supporting 3 interchangeable sources injected into the
  builder:
  - **file**: load existing subtitles (.srt/.vtt)
  - **auto**: auto-generate via ASR (faster-whisper)
  - **hybrid**: use a script text already known to be correct + ASR only to
    align timestamps to the audio — avoids Whisper's text-recognition
    errors
- **Templates**: reusable, parametrized edit recipes — encapsulate a
  repeatable visual structure once, reapply it to many different inputs
  without rewriting the underlying `TimelineBuilder` calls
- Render to a complete video file via a pluggable `RenderStrategy` (v1
  ships `MoviePyRenderStrategy`; swappable later without touching the
  domain model or builder)
- Batch production: run in bulk from a directory of `Script` files (each
  one = 1 video)

## 4. Out of scope for v1

Possible later, the architecture leaves room for it (see
[PLAN.md](PLAN.md) v2 section):

- `Agent`: AI, natural-language-driven video generation (choosing/
  parametrizing a `Template` or writing a `Script` from an intent string)
- TTS voice generation
- Automatic thumbnail generation
- An alternate `RenderStrategy` for performance at scale (e.g. an
  `FFmpegRenderStrategy` using raw filter-graphs)
- Exporting multiple aspect ratios at once (9:16/16:9)
- A general keyframe/property animation engine — only if truly needed,
  once the fixed-preset system in v1 proves limiting

## 5. Example usage (illustrative, planned API — not yet implemented)

```python
from vidgen.builder import TimelineBuilder
from vidgen.strategies.render import MoviePyRenderStrategy
from vidgen.strategies.subtitle import HybridSubtitleSource
from vidgen.domain import Alignment, Position, TextStyle, FadeAnimation, DissolveTransition

timeline = (
    TimelineBuilder(resolution=(1080, 1920), fps=30)
    .clip("assets/clips/intro.mp4", start=0)
    .clip("assets/clips/main.mp4", start=5,
          transition_in=DissolveTransition(duration=0.5))
    .text("Hello!", start=0, end=3,
          position=Position.preset(Alignment.CENTER),
          style=TextStyle(font="Roboto-Bold.ttf", font_size=64,
                           color="white", outline_color="black", outline_width=2),
          animation=FadeAnimation(direction="in", duration=0.4))
    .audio("assets/music/bg.mp3", volume=0.3, fade_out=2)
    .captions(HybridSubtitleSource(),
              script_text=open("script.txt").read(),
              voice_audio="assets/voice/segment_0.mp3")
    .build()
)

MoviePyRenderStrategy().render(timeline, "output/video_001.mp4")
```

Batch multiple videos (Layer 4, driven by `Script` files):

```python
from vidgen.automation import BatchProducer

producer = BatchProducer(spec_dir="input/specs/")
producer.run(output_dir="output/")
```

> The fluent `TimelineBuilder` API is the official, complete interface.
> JSON/YAML in `input/specs/` (parsed by `Script`) is just a declarative way
> to write the same builder calls — see
> [SPEC.md §10](SPEC.md#10-script--declarative-spec-layer-3).

## 6. Project status

Currently in the architecture design stage, no implementation code yet. See
[PLAN.md](PLAN.md) for the roadmap and implementation checklist.

---
See also: [ARCHITECTURE.md](ARCHITECTURE.md) · [SPEC.md](SPEC.md) · [DESIGN.md](DESIGN.md) · [PLAN.md](PLAN.md)
