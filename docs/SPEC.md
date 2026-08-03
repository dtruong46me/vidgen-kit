# Technical spec — vidgen

This document describes the **detailed API of each class/method** within the
layers introduced in [ARCHITECTURE.md](ARCHITECTURE.md). Read
ARCHITECTURE.md first to get the overall picture (the 5-layer Dependency
Inversion stack), then come back here for field/method details while
implementing. Sections below are grouped and labeled by layer. For every
field's exact type/default, every invariant, and every algorithm
step-by-step, see [DESIGN.md](DESIGN.md) — this document is the API shape,
DESIGN.md is the implementation-ready reference.

## 1. Timeline — domain data (Layer 0)

`Timeline` is plain data: a resolution, an fps, and a set of named tracks.
It has no `add_*` methods — those live on `TimelineBuilder` (§2). Advanced
code (tests, alternate builders) may still construct/mutate a `Timeline`
directly, since it's just a dataclass with light integrity checks:

```python
@dataclass
class Timeline:
    resolution: tuple[int, int]
    fps: int = 30
    tracks: dict[str, Track] = field(default_factory=dict)

    def get_track(self, name: str) -> Track | None: ...
    def _validate(self) -> None: ...   # checks time overlap, empty tracks, etc.
```

## 2. TimelineBuilder — fluent construction API (Layer 1)

`TimelineBuilder` is the official, day-to-day entry point. Every method
**returns the builder itself** so calls chain; the only way to get a
`Timeline` out is `.build()`. Internally it delegates to `Track`/`Clip`/
`Overlay` (Layer 0) — a regular user doesn't need to know `Track` exists to
use it:

```python
class TimelineBuilder:
    def __init__(self, resolution: tuple[int, int], fps: int = 30):
        self._timeline = Timeline(resolution=resolution, fps=fps)

    # --- track management (when fine-grained control is needed) ---
    def track(self, name: str, track_cls: type[Track] = VideoTrack) -> "TimelineBuilder": ...

    # --- fluent, chainable editing API ---
    def clip(self, path, start, end=None, *, track="main",
             transition_in: Transition | None = None) -> "TimelineBuilder": ...
    def clips(self, specs: list[dict], *, track="main") -> "TimelineBuilder": ...
    def text(self, text, start, end, *, position=Position.preset(Alignment.CENTER),
             style: TextStyle | None = None, animation: Animation | None = None,
             track="overlay") -> "TimelineBuilder": ...
    def image(self, path, start, end=None, *, position, animation=None,
              track="overlay") -> "TimelineBuilder": ...
    def audio(self, path, *, start=0, volume=1.0, fade_in=0, fade_out=0,
              track="audio") -> "TimelineBuilder": ...
    def captions(self, source: "SubtitleSource", *, script_text: str, voice_audio: str,
                 style: TextStyle | None = None, track="captions") -> "TimelineBuilder": ...

    def build(self) -> Timeline: ...   # runs Timeline._validate(), returns the domain object

    # --- private ---
    def _get_or_create_track(self, name: str, track_cls: type[Track]) -> Track: ...
```

Key points:

- **`.clip(path, ...)` does not touch the filesystem.** It stores
  `Asset(path=path)` with `duration`/`resolution`/`fps` left `None` —
  resolving that metadata is `AssetLoader`'s job, called by `RenderStrategy`
  at render time (§8). This is what keeps `TimelineBuilder` free of any
  ffprobe/MoviePy dependency (Layer 1 → Layer 0 only).
- **`.captions(source, ...)` takes a `SubtitleSource` instance from the
  caller** (e.g. `builder.captions(HybridSubtitleSource(), script_text=...,
  voice_audio=...)`). `TimelineBuilder`'s own module only imports the
  `SubtitleSource` ABC from `domain/ports.py` (Layer 0) — never a concrete
  implementation. This is dependency injection in service of the Layer
  1 → Layer 2 rule from [ARCHITECTURE.md §2](ARCHITECTURE.md#2-the-five-layers).
- `.clips([...])`, like every batch-style call, is just a loop calling the
  single-item version — no special logic, keeping the "one job, one place"
  principle.

## 3. Track/Clip/Overlay — Domain layer details (Layer 0)

```python
class Track(ABC, Generic[T]):
    def __init__(self, name: str):
        self.name = name
        self._items: list[T] = []                # private

    def add(self, item: T) -> T:                  # public
        self._validate_item(item)                  # calls the subclass's private hook
        self._items.append(item)
        return item

    def add_many(self, items: Iterable[T]) -> list[T]:  # public, batch
        return [self.add(i) for i in items]

    def items(self) -> tuple[T, ...]:              # public, read-only view
        return tuple(self._items)

    @abstractmethod
    def _validate_item(self, item: T) -> None: ...  # subclasses must implement
```

`VideoTrack._validate_item` only accepts `Clip`; `OverlayTrack` only accepts
`Overlay`; etc. — a wrong item type is rejected right at `add()`, not left
until render time. `TimelineBuilder` calls `Track.add`/`add_many` internally
— users of the fluent API never call `Track` directly unless they want
fine-grained control (see [ARCHITECTURE.md §2](ARCHITECTURE.md#2-the-five-layers)).

`Clip`/`Overlay` are ABCs holding common fields (`start`, `end`,
`animation`), specialized by `VideoClip`/`ImageClip` (adding `asset`,
`trim_in`, `trim_out`, `transition_in`) and `TextOverlay`/`ImageOverlay`
(adding `position`, and for `TextOverlay`, `text`/`style`).

## 4. Position & Alignment — presets and free coordinates (Layer 0)

```python
class Alignment(Enum):
    CENTER = "center"
    TOP_LEFT = "top-left"; TOP_CENTER = "top-center"; TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"; BOTTOM_CENTER = "bottom-center"; BOTTOM_RIGHT = "bottom-right"
    LEFT = "left"; RIGHT = "right"

class Position:
    @classmethod
    def preset(cls, alignment: Alignment) -> "Position": ...
    @classmethod
    def custom(cls, x: float, y: float, unit: Literal["ratio", "pixel"] = "ratio") -> "Position": ...
```

`RenderStrategy` (§8) is the only place that "resolves" a `Position` into
final pixel coordinates (preset → lookup table based on `resolution`;
`unit="ratio"` → multiplied by `resolution`; `unit="pixel"` → used as-is).

## 5. TextStyle — fully customizable, custom fonts (Layer 0)

```python
@dataclass
class TextStyle:
    font: str = "Arial"              # system font name or a path to a custom .ttf
    font_size: int = 48
    color: str = "white"
    outline_color: str | None = "black"
    outline_width: int = 0
    bg_color: str | None = None       # background behind the text, optional
    align: Literal["left", "center", "right"] = "center"
    max_width: int | None = None       # auto line-wrap by pixel width
```

Every field has a sensible default — simple usage only needs `text` +
`start`/`end`; customizing font/color/outline is optional. Applies to both
`TextOverlay` and `Caption`.

## 6. Animation & Transition — basic presets (Layer 0)

```python
class Animation(ABC):
    duration: float
    @abstractmethod
    def _apply(self, clip, backend_ctx) -> Any: ...   # called only by RenderStrategy

class FadeAnimation(Animation):
    direction: Literal["in", "out"]

class SlideAnimation(Animation):
    direction: Literal["left", "right", "top", "bottom"]

class ZoomAnimation(Animation):
    direction: Literal["in", "out"]
```

- Attached to `Overlay`/`Clip` via the `animation` field (simple
  entrance/exit, one animation at a time — no chaining or free
  keyframing; see [PRD.md §1](PRD.md#1-goals--non-goals) for why this stays
  a fixed preset set in v1).
- `Transition` works similarly but attaches between **two consecutive
  clips** on a `VideoTrack` (the `transition_in` field of the following
  `VideoClip`): `CutTransition` (default — straight cut, no effect),
  `FadeTransition` (fade through black), `DissolveTransition` (crossfade
  between the 2 clips).
- `_apply()` is **protected/internal**, called only by `RenderStrategy` at
  render time — users never call it directly; they just attach an
  animation/transition to an object via `TimelineBuilder` and let the
  strategy handle it (keeping Layer 0 ignorant of "how to execute", only
  aware of "declared intent" — Dependency Inversion in miniature).

## 7. Caption & SubtitleSource — port (Layer 0) + strategies (Layer 2)

`Caption` (Layer 0, plain dataclass: `text`, start/end timestamps).

`SubtitleSource` is an **abstract port**, declared in `domain/ports.py`
(Layer 0 — zero third-party imports, just an `ABC`):

```python
class SubtitleSource(ABC):
    @abstractmethod
    def generate(self, *, script_text: str | None, voice_audio: str) -> list["Caption"]: ...
```

Its concrete implementations live in Layer 2
(`strategies/subtitle/`), each importing whatever library it needs, and are
injected into `TimelineBuilder.captions(source, ...)` (§2) by the caller:

- **`FileSubtitleSource`**: parses existing `.srt`/`.vtt` files (imports
  `srt`).
- **`WhisperSubtitleSource`**: ASR via `faster-whisper` — used when there's
  no original script.
- **`HybridSubtitleSource`** (recommended default for batch production):
  script text already known to be correct → uses Whisper/a forced-aligner
  only to align timestamps, never taking recognized text from ASR →
  eliminates Whisper's text-recognition errors. Fallback: generate via
  `WhisperSubtitleSource` → export `.srt` for manual correction → reload via
  `FileSubtitleSource`.

## 8. RenderStrategy & provider strategies (Layer 2)

```python
class RenderStrategy(ABC):
    @abstractmethod
    def render(self, timeline: "Timeline", output_path: str) -> Path: ...
```

`MoviePyRenderStrategy` is the sole v1 implementation: it walks each `Track`
of the `Timeline`; for each `VideoClip`/`ImageClip` it first resolves the
referenced `Asset`'s real metadata via `AssetLoader` (the first and only
point the file is actually inspected), then resolves `Position`/`TextStyle`/
`Animation`/`Transition` into the corresponding MoviePy calls (`fadein`,
`crossfadein`, `set_position`, time-varying `resize` for zoom, etc.), then
composites and calls `write_videofile`. Because Layer 0/1 have no MoviePy
dependency, adding e.g. an `FFmpegRenderStrategy` later only requires a new
class implementing `render()`, with no change to `TimelineBuilder` or
`Timeline`.

```python
class AssetLoader:
    def resolve(self, asset: "Asset") -> "Asset": ...  # returns a new Asset with duration/resolution/fps filled in
```

`AssetLoader` reads real file metadata (via `ffprobe`/MoviePy) for an
`Asset` that a `TimelineBuilder` created with only a `path`. It's a sibling
strategy to `RenderStrategy` — same layer, same "the only place that talks
to the outside world for this concern" role.

## 9. Template — reusable parametrized edit recipes (Layer 3)

```python
class Template(ABC):
    @abstractmethod
    def apply(self, builder: "TimelineBuilder", **params) -> "TimelineBuilder": ...
```

A `Template` encapsulates a repeatable visual structure once (e.g. "quote
video: background clip + centered text + background music + optional
voice/captions") and applies it to a `TimelineBuilder` for arbitrary input
parameters — the code-first equivalent of a CapCut/Premiere template:

```python
class FacelessQuoteTemplate(Template):
    def apply(self, builder, *, background_clip, quote_text, music,
              voice_audio=None, style=None):
        builder.clip(background_clip, start=0)
        builder.text(quote_text, start=0, end=None,
                     position=Position.preset(Alignment.CENTER),
                     style=style or TextStyle())
        builder.audio(music, volume=0.3)
        if voice_audio:
            builder.captions(HybridSubtitleSource(), script_text=quote_text,
                              voice_audio=voice_audio)
        return builder
```

`Template.apply()` returns the same `TimelineBuilder` it was given (still
chainable), so a template can be combined with extra manual `.text()`/
`.image()` calls before `.build()`.

## 10. Script — declarative spec (Layer 3)

- **The fluent `TimelineBuilder` API is the official, complete
  interface.**
- `design/script.py` reads a JSON/YAML file and maps each field 1-to-1 to
  the corresponding `TimelineBuilder` method call — no logic of its own
  beyond mapping + validation (via `pydantic`).
- A `Script` is one way (alongside `Template`, §9) to describe a design
  above the raw `TimelineBuilder` calls — useful for cases where the design
  is generated or edited outside of Python (a UI, a config file).
- Adding a new field to `TimelineBuilder` requires syncing a mapping
  addition in `Script` — an accepted maintenance cost in exchange for
  supporting both usage styles in parallel.

## 11. BatchProducer (Layer 4)

```python
@dataclass
class BatchResult:
    succeeded: list[Path]
    failed: list[tuple[Path, Exception]]

class BatchProducer:
    def __init__(self, spec_dir: str, render_strategy: "RenderStrategy | None" = None): ...
    def run(self, output_dir: str) -> BatchResult: ...
```

For each `Script` file in `spec_dir`: parse it into a `Timeline` (via
`TimelineBuilder`), render it with the given (or default) `RenderStrategy`,
and save to `output_dir`. An error in one spec does not stop the whole
batch (logs the error, continues to the next file); `run()` returns a
`BatchResult` summarizing which specs succeeded and which failed (and why)
— see [DESIGN.md](DESIGN.md#layer-4--automation-batch-producer-automationbatch_producerpy)
for the full algorithm. This is the top of the stack — the only layer
allowed to import from every layer below it. `Agent`
(natural-language-driven generation, choosing/parametrizing a `Template` or
writing a `Script` from an intent string) is a documented extension point
here for v2 — see [PLAN.md](PLAN.md) — not designed in v1.

---
See also: [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [DESIGN.md](DESIGN.md) · [PLAN.md](PLAN.md)
