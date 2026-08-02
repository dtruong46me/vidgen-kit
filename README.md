# Video Generator Kit (vidgen)

A **high-level, OOP-oriented** Python library for automated batch video
production — similar to what you'd do by hand in CapCut/Premiere, but every
operation is callable from code, so you can automate a video production
pipeline.

This is **not** a full-featured video editor. Animation/transitions are
just a **set of built-in, simple presets** (fade, slide, zoom,
dissolve...), not a free keyframe/easing engine; no color grading, no
complex nested multi-track editing. Only the core operations needed for
batch video production (e.g. "faceless" videos from a script + images/clips
+ background music + voiceover + captions).

`vidgen` doesn't implement video processing itself — it's a thin API layer
that **orchestrates** existing libraries (MoviePy/FFmpeg, Whisper, Pillow,
...), organized into 5 clear layers (Domain → Asset/Caption → Render →
Config → Orchestration). See [docs/PRD.md](docs/PRD.md) for detailed
goals/features, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the
architecture & OOP class diagram, [docs/SPEC.md](docs/SPEC.md) for the
detailed API of each class, and [docs/PLAN.md](docs/PLAN.md) for the
roadmap & implementation checklist.

## Features (v1 scope)

- Cut/join clips on the `Timeline` (trim, concat, basic transitions between
  clips: cut/fade/dissolve)
- Text overlay: fully customizable font/size/color/outline, positioned via
  alignment presets (center, left, right, 4 corners...) or free coordinates
- Image overlay/watermark, using the same positioning mechanism as above
- Basic entrance/exit animation for overlays: fade in/out, slide, zoom
- Audio: mix background music + existing voiceover audio (volume, fade
  in/out)
- Captions/subtitles, supporting 3 modes:
  - **file**: load existing subtitles (.srt/.vtt)
  - **auto**: auto-generate via ASR (faster-whisper)
  - **hybrid**: use a script text already known to be correct (100%
    accurate) + ASR only to align timestamps to the audio — avoids
    Whisper's text-recognition errors
- Render to a complete video file (via MoviePy, backend swappable later)
- Batch pipeline: run in bulk from a list of configs (each item = 1 video)

Not in v1 (possible later, architecture leaves room for it): TTS voice
generation, thumbnail generation, more advanced animation/transitions
(free keyframing), performance optimization via raw ffmpeg filter-graphs.

## Example usage (planned API — not yet implemented)

```python
from vidgen import Timeline
from vidgen.core import Alignment, Position, TextStyle, FadeAnimation, DissolveTransition

timeline = Timeline(resolution=(1080, 1920), fps=30)

# add multiple clips at once, with a transition between them
timeline.add_clips([
    {"path": "assets/clips/intro.mp4", "start": 0},
    {"path": "assets/clips/main.mp4", "start": 5,
     "transition_in": DissolveTransition(duration=0.5)},
])

timeline.add_text(
    "Hello!", start=0, end=3,
    position=Position.preset(Alignment.CENTER),   # or Position.custom(0.5, 0.1)
    style=TextStyle(font="Roboto-Bold.ttf", font_size=64,
                     color="white", outline_color="black", outline_width=2),
    animation=FadeAnimation(direction="in", duration=0.4),
)

timeline.add_image(
    "assets/logo.png", start=0, end=None,
    position=Position.preset(Alignment.TOP_RIGHT),
)

timeline.add_audio("assets/music/bg.mp3", volume=0.3, fade_out=2)

timeline.add_captions_from_script(
    script_text=open("script.txt").read(),
    voice_audio="assets/voice/segment_0.mp3",
    mode="hybrid",  # "file" | "auto" | "hybrid"
)

timeline.render("output/video_001.mp4")
```

For finer-grained control (working directly with tracks), you can still do
so, since `add_clip`/`add_text`/... are just convenience wrappers around
`Track`/`Clip`/`Overlay`:

```python
from vidgen.core import VideoTrack, VideoClip

track = timeline.add_track(VideoTrack(name="b-roll"))
track.add_many([
    VideoClip(asset=asset_a, start=0, end=4),
    VideoClip(asset=asset_b, start=4, end=9),
])
```

Batch multiple videos:

```python
from vidgen.pipeline import BatchPipeline

pipeline = BatchPipeline(spec_dir="input/specs/")
pipeline.run(output_dir="output/")
```

> The Python API (`Timeline.add_*`, `Track.add`/`add_many`) is the
> official, complete interface. Each JSON/YAML file in `input/specs/` is
> just a declarative way to write the same calls (1-to-1 mapping) — used
> when you want to generate bulk configs without writing Python. See
> [docs/SPEC.md §8](docs/SPEC.md#8-batchpipeline--config-json-as-a-thin-wrapper).

## Installation (planned)

```bash
pip install moviepy faster-whisper pillow pydantic srt
```

## Project status

Currently in the architecture design stage, no implementation code yet.
