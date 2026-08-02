# Technical spec — vidgen

This document describes the **detailed API of each class/method** within the
layers introduced in [ARCHITECTURE.md](ARCHITECTURE.md). Read
ARCHITECTURE.md first to get the overall picture (layers, class diagram),
then come back here for field/method details while implementing.

## 1. Timeline — public API (Orchestration-layer facade)

`Timeline` is the main entry point, exposing convenient **public** methods
that internally delegate to `Track`/`Clip`/`Overlay` (private helpers) — a
regular user doesn't need to know about `Track` to use it:

```python
class Timeline:
    def __init__(self, resolution: tuple[int, int], fps: int = 30):
        self.resolution = resolution
        self.fps = fps
        self._tracks: dict[str, Track] = {}          # private state, not accessed directly

    # --- track management (when fine-grained control is needed) ---
    def add_track(self, track: Track) -> Track: ...
    def get_track(self, name: str) -> Track | None: ...

    # --- convenience API, implicitly creates a track if it doesn't exist ---
    def add_clip(self, path, start, end=None, *, track="main",
                 transition_in: Transition | None = None) -> VideoClip: ...
    def add_clips(self, specs: list[dict], *, track="main") -> list[VideoClip]: ...
    def add_text(self, text, start, end, *, position=Position.preset(Alignment.CENTER),
                 style: TextStyle | None = None, animation: Animation | None = None,
                 track="overlay") -> TextOverlay: ...
    def add_image(self, path, start, end=None, *, position, animation=None,
                  track="overlay") -> ImageOverlay: ...
    def add_audio(self, path, *, start=0, volume=1.0, fade_in=0, fade_out=0,
                  track="audio") -> AudioLayer: ...
    def add_captions_from_script(self, script_text, voice_audio, *, mode="hybrid",
                                  style: TextStyle | None = None) -> CaptionTrack: ...

    def render(self, output_path, backend: "RenderBackend | None" = None) -> Path: ...

    # --- private ---
    def _get_or_create_track(self, name: str, track_cls: type[Track]) -> Track: ...
    def _validate(self) -> None: ...     # checks time overlap, empty tracks, etc.
```

`add_clips([...])`, like every `add_many` at the `Track` level, is just a
loop calling the single-item version — no special logic, keeping the "one
job, one place" principle.

## 2. Track/Clip/Overlay — Domain layer details

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
until render time.

`Clip`/`Overlay` are ABCs holding common fields (`start`, `end`,
`animation`), specialized by `VideoClip`/`ImageClip` (adding `asset`,
`trim_in`, `trim_out`, `transition_in`) and `TextOverlay`/`ImageOverlay`
(adding `position`, and for `TextOverlay`, `text`/`style`).

## 3. Position & Alignment — presets and free coordinates

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

`RenderBackend` is the only place that "resolves" a `Position` into final
pixel coordinates (preset → lookup table based on `resolution`;
`unit="ratio"` → multiplied by `resolution`; `unit="pixel"` → used as-is).

## 4. TextStyle — fully customizable, custom fonts

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

## 5. Animation & Transition — basic presets

```python
class Animation(ABC):
    duration: float
    @abstractmethod
    def _apply(self, clip, backend_ctx) -> Any: ...   # called only by RenderBackend

class FadeAnimation(Animation):
    direction: Literal["in", "out"]

class SlideAnimation(Animation):
    direction: Literal["left", "right", "top", "bottom"]

class ZoomAnimation(Animation):
    direction: Literal["in", "out"]
```

- Attached to `Overlay`/`Clip` via the `animation` field (simple
  entrance/exit, one animation at a time — no chaining or complex
  keyframing).
- `Transition` works similarly but attaches between **two consecutive
  clips** on a `VideoTrack` (the `transition_in` field of the following
  `VideoClip`): `CutTransition` (default — straight cut, no effect),
  `FadeTransition` (fade through black), `DissolveTransition` (crossfade
  between the 2 clips).
- `_apply()` is **protected/internal**, called only by `RenderBackend` at
  render time — users never call it directly; they just attach an
  animation/transition to an object and let the backend handle it (keeping
  the domain layer ignorant of "how to execute", only aware of "declared
  intent").

## 6. Caption — 3 modes

`SubtitleSource` (ABC, Caption layer) with the abstract method
`generate(...) -> list[Caption]`:

- **`FileSubtitleSource`**: parses existing `.srt`/`.vtt` files (via the
  `srt` lib).
- **`WhisperSubtitleSource`**: ASR via `faster-whisper` — used when there's
  no original script.
- **`HybridSubtitleSource`** (recommended default for batch production):
  script text already known to be correct → uses Whisper/a forced-aligner
  only to align timestamps, never taking recognized text from ASR →
  eliminates Whisper's text-recognition errors. Fallback: generate via
  Whisper → export `.srt` for manual correction → reload via
  `FileSubtitleSource`.

## 7. RenderBackend

```python
class RenderBackend(ABC):
    @abstractmethod
    def render(self, timeline: "Timeline", output_path: str) -> Path: ...
```

`MoviePyBackend` is the sole v1 implementation: it walks each `Track` of the
`Timeline`, and for each `Clip`/`Overlay` resolves `Position`/`TextStyle`/
`Animation`/`Transition` into the corresponding MoviePy calls (`fadein`,
`crossfadein`, `set_position`, time-varying `resize` for zoom, etc.), then
composites and calls `write_videofile`. Because the Domain layer has no
MoviePy dependency, adding an `FFmpegBackend` later only requires
re-implementing `render()`, with no change to the `Timeline` API.

## 8. BatchPipeline & Config (JSON as a thin wrapper)

- **The Python API (`Timeline.add_*`) is the official, complete
  interface.**
- `config/spec.py` reads a JSON/YAML file and maps each field 1-to-1 to the
  corresponding `Timeline.add_*` call — no logic of its own beyond mapping
  + validation.
- `BatchPipeline(spec_dir=...)`: for each spec file in the directory →
  parse into a `Timeline` → `render()` → save to `output/`. An error in one
  spec does not stop the whole batch (logs the error, continues to the next
  file).
- Adding a new field to the `Timeline` API requires syncing a mapping
  addition in `spec.py` — an accepted maintenance cost in exchange for
  supporting both usage styles in parallel.

---
See also: [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [PLAN.md](PLAN.md)
