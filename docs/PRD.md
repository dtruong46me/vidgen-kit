# PRD — vidgen

This document answers **what vidgen is, who it's for, and what it does and
doesn't do** — at the product level, not the technical level. See
[ARCHITECTURE.md](ARCHITECTURE.md) for how the system is organized, and
[SPEC.md](SPEC.md) for the detailed API.

## 1. Goals & non-goals

**Goal**: a high-level, programmable (OOP) Python library for batch video
production: cutting/joining clips, adding text/image overlays with basic
animation, simple transitions between clips, mixing background music/audio,
attaching captions, and rendering to a file. Architectural clarity (clear
layers, clear abstract classes) is prioritized over feature richness.

**Non-goals**: not competing with CapCut/Premiere on complex keyframe/easing
effects, color grading, freely nested multi-track editing, or large-scale
render performance. Animation/transitions here are a **set of built-in
presets** (fade, slide, zoom, dissolve...), not a general-purpose animation
engine.

## 2. Audience & use case

Developers who want to automate **batch video production** — e.g.
"faceless" videos made from a script + existing images/clips + background
music + voiceover + captions — instead of repeating manual work in
CapCut/Premiere for every video. Used as a Python library embedded in a
custom pipeline, or run as a batch job from a list of JSON/YAML configs.

## 3. Features (v1 scope)

- Cut/join clips on a timeline (trim, concat, basic transitions between
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
  - **hybrid**: use a script text already known to be correct + ASR only to
    align timestamps to the audio — avoids Whisper's text-recognition errors
- Render to a complete video file (via MoviePy, backend swappable later)
- Batch pipeline: run in bulk from a list of configs (each item = 1 video)

## 4. Out of scope for v1

Possible later, the architecture leaves room for it (see
[PLAN.md](PLAN.md) v2 section):

- TTS voice generation
- Automatic thumbnail generation
- `FFmpegBackend` for performance at scale (replacing/alongside
  `MoviePyBackend`)
- Exporting multiple aspect ratios at once (9:16/16:9)
- More advanced animation/transitions (free keyframing) — only if truly
  needed, without contradicting the "simpler than CapCut/Premiere" spirit
  from section 1.

## 5. Example usage (illustrative, planned API — not yet implemented)

```python
from vidgen import Timeline
from vidgen.core import Alignment, Position, TextStyle, FadeAnimation, DissolveTransition

timeline = Timeline(resolution=(1080, 1920), fps=30)

timeline.add_clips([
    {"path": "assets/clips/intro.mp4", "start": 0},
    {"path": "assets/clips/main.mp4", "start": 5,
     "transition_in": DissolveTransition(duration=0.5)},
])

timeline.add_text(
    "Hello!", start=0, end=3,
    position=Position.preset(Alignment.CENTER),
    style=TextStyle(font="Roboto-Bold.ttf", font_size=64,
                     color="white", outline_color="black", outline_width=2),
    animation=FadeAnimation(direction="in", duration=0.4),
)

timeline.add_audio("assets/music/bg.mp3", volume=0.3, fade_out=2)

timeline.add_captions_from_script(
    script_text=open("script.txt").read(),
    voice_audio="assets/voice/segment_0.mp3",
    mode="hybrid",
)

timeline.render("output/video_001.mp4")
```

Batch multiple videos:

```python
from vidgen.pipeline import BatchPipeline

pipeline = BatchPipeline(spec_dir="input/specs/")
pipeline.run(output_dir="output/")
```

> The Python API (`Timeline.add_*`) is the official, complete interface.
> JSON/YAML in `input/specs/` is just a declarative way to write batch
> configs — see
> [SPEC.md §8](SPEC.md#8-batchpipeline--config-json-as-a-thin-wrapper).

## 6. Project status

Currently in the architecture design stage, no implementation code yet. See
[PLAN.md](PLAN.md) for the roadmap and implementation checklist.

---
See also: [ARCHITECTURE.md](ARCHITECTURE.md) · [SPEC.md](SPEC.md) · [PLAN.md](PLAN.md)
