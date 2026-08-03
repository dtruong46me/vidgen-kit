# Video Generator Kit (vidgen)

A programmable, code-first **video editing engine** for Python — the kind
of model that could power a tool like CapCut/Premiere/Adobe, but consumed
as a library/SDK rather than a GUI app. Every editing operation (cutting/
joining clips, text/image overlays with animation, transitions, audio
mixing, captions, rendering) is expressed through a fluent Builder API.
Automated batch production is one thing you can build *on top* of this
engine — it isn't what the engine fundamentally is.

vidgen's architecture follows strict **Dependency Inversion**: a pure
Domain Model (zero third-party imports) sits at the bottom; a fluent
`TimelineBuilder` sits above it; a swappable `RenderStrategy` (MoviePy today,
replaceable later) sits above that; `Script`/`Template` and `BatchProducer`
sit on top for declarative and automated use. See
[docs/PRD.md](docs/PRD.md) for detailed goals/features,
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full layer stack &
OOP class diagram, [docs/SPEC.md](docs/SPEC.md) for the API shape of each
class, [docs/DESIGN.md](docs/DESIGN.md) for the full implementation-ready
design (fields, invariants, algorithms), and [docs/PLAN.md](docs/PLAN.md)
for the roadmap & implementation checklist.

v1 focuses on a deliberately limited feature *depth* — no color grading, no
freely nested multi-track compositing, animation/transitions are still a
fixed preset set rather than a general keyframe engine — but that's a v1
scope choice, not an architectural ceiling: the layering exists precisely
so richer capability can be added later without breaking existing code.

## Features (v1 scope)

- **Fluent Builder API** (`TimelineBuilder`): chainable method calls to
  assemble an edit in code
- Cut/join clips on a timeline (trim, concat, basic transitions between
  clips: cut/fade/dissolve)
- Text overlay: fully customizable font/size/color/outline, positioned via
  alignment presets (center, left, right, 4 corners...) or free coordinates
- Image overlay/watermark, using the same positioning mechanism as above
- Basic entrance/exit animation for overlays: fade in/out, slide, zoom
- Audio: mix background music + existing voiceover audio (volume, fade
  in/out)
- Captions/subtitles, supporting 3 interchangeable sources injected into
  the builder:
  - **file**: load existing subtitles (.srt/.vtt)
  - **auto**: auto-generate via ASR (faster-whisper)
  - **hybrid**: use a script text already known to be correct (100%
    accurate) + ASR only to align timestamps to the audio — avoids
    Whisper's text-recognition errors
- **Templates**: reusable, parametrized edit recipes — encapsulate a
  repeatable visual structure once, reapply it to many different inputs
- Render to a complete video file via a pluggable `RenderStrategy` (v1
  ships `MoviePyRenderStrategy`, swappable later)
- Batch production: run in bulk from a directory of `Script` files (each
  one = 1 video)

Not in v1 (possible later, architecture leaves room for it): an `Agent`
that generates videos from natural language, TTS voice generation,
thumbnail generation, an alternate `RenderStrategy` for performance at
scale, exporting multiple aspect ratios at once, a general keyframe/
property animation engine.

## Example usage (planned API — not yet implemented)

```python
from vidgen.builder import TimelineBuilder
from vidgen.strategies.render import MoviePyRenderStrategy
from vidgen.strategies.subtitle import HybridSubtitleSource
from vidgen.domain import Alignment, Position, TextStyle, FadeAnimation, DissolveTransition

timeline = (
    TimelineBuilder(resolution=(1080, 1920), fps=30)
    # add multiple clips, with a transition between them
    .clip("assets/clips/intro.mp4", start=0)
    .clip("assets/clips/main.mp4", start=5,
          transition_in=DissolveTransition(duration=0.5))
    .text("Hello!", start=0, end=3,
          position=Position.preset(Alignment.CENTER),   # or Position.custom(0.5, 0.1)
          style=TextStyle(font="Roboto-Bold.ttf", font_size=64,
                           color="white", outline_color="black", outline_width=2),
          animation=FadeAnimation(direction="in", duration=0.4))
    .image("assets/logo.png", start=0, end=None,
           position=Position.preset(Alignment.TOP_RIGHT))
    .audio("assets/music/bg.mp3", volume=0.3, fade_out=2)
    .captions(HybridSubtitleSource(),
              script_text=open("script.txt").read(),
              voice_audio="assets/voice/segment_0.mp3")
    .build()
)

MoviePyRenderStrategy().render(timeline, "output/video_001.mp4")
```

Rendering is a separate call from building — `TimelineBuilder` only ever
produces a plain `Timeline`; you pick a `RenderStrategy` to turn it into a
file. This keeps the builder swappable-renderer-agnostic (see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for why).

For finer-grained control (working directly with tracks), you can still do
so, since the fluent methods are just convenience wrappers around
`Track`/`Clip`/`Overlay`:

```python
from vidgen.domain import VideoTrack, VideoClip

builder.track("b-roll", VideoTrack)
builder._get_or_create_track("b-roll", VideoTrack).add_many([
    VideoClip(asset=asset_a, start=0, end=4),
    VideoClip(asset=asset_b, start=4, end=9),
])
```

Batch multiple videos:

```python
from vidgen.automation import BatchProducer

producer = BatchProducer(spec_dir="input/specs/")
producer.run(output_dir="output/")
```

> The fluent `TimelineBuilder` API is the official, complete interface.
> Each JSON/YAML file in `input/specs/` (parsed by `Script`) is just a
> declarative way to write the same builder calls — used when you want to
> generate bulk configs without writing Python. See
> [docs/SPEC.md §10](docs/SPEC.md#10-script--declarative-spec-layer-3).

## Installation (planned)

```bash
pip install moviepy faster-whisper pillow pydantic srt
```

## Project status

Currently in the architecture design stage, no implementation code yet.
