# Detailed design — vidgen

[SPEC.md](SPEC.md) shows the *shape* of the public API (method signatures,
illustrative sketches with `...` bodies). This document is the full,
implementation-ready reference: every field (type, default, constraint),
every method (parameters, return type, behavior, errors raised), and every
invariant, for every class — organized by the same 5 layers as
[ARCHITECTURE.md](ARCHITECTURE.md). Where a decision here refines a
signature shown in SPEC.md, SPEC.md has been updated to match (e.g.
`BatchProducer.run()` §11.2 below).

Conventions used throughout: dataclasses are plain (`@dataclass`, not
frozen) unless noted; validation happens in `__post_init__` and raises the
error type named for it; all module paths are relative to `src/vidgen/`.

## Layer 0 — Domain Model (`domain/`)

Shared error module `domain/errors.py`:

| Exception | Base | Raised when |
|---|---|---|
| `TimeRangeError` | `ValueError` | `end <= start`, or a non-last `VideoClip` on a `VideoTrack` has `end=None` |
| `TrackItemTypeError` | `TypeError` | `Track.add()` called with an item of the wrong type for that track |
| `ClipOverlapError` | `TimeRangeError` | Two `VideoClip`s on the same `VideoTrack` overlap in time |
| `TrackTypeConflictError` | `TypeError` | Requesting an existing track name with a different `Track` subclass |
| `TimelineValidationError` | `ValueError` | `Timeline._validate()` fails for a reason not covered above (e.g. no tracks at all) |

### `position.py`

**`Alignment(Enum)`** — `CENTER="center"`, `TOP_LEFT="top-left"`,
`TOP_CENTER="top-center"`, `TOP_RIGHT="top-right"`, `BOTTOM_LEFT="bottom-left"`,
`BOTTOM_CENTER="bottom-center"`, `BOTTOM_RIGHT="bottom-right"`,
`LEFT="left"`, `RIGHT="right"`.

**`Position`** — `@dataclass(frozen=True)`. Internally tagged so exactly one
of "preset" or "custom" is active; direct construction is discouraged in
favor of the two classmethods.

| Field | Type | Default | Notes |
|---|---|---|---|
| `kind` | `Literal["preset", "custom"]` | required | set by the classmethod used |
| `alignment` | `Alignment \| None` | `None` | set only when `kind="preset"` |
| `x`, `y` | `float \| None` | `None` | set only when `kind="custom"` |
| `unit` | `Literal["ratio", "pixel"]` | `"ratio"` | only meaningful when `kind="custom"` |

- `Position.preset(alignment: Alignment) -> Position` — returns
  `Position(kind="preset", alignment=alignment)`.
- `Position.custom(x, y, unit="ratio") -> Position` — if `unit="ratio"`,
  raises `ValueError` unless `0 <= x <= 1` and `0 <= y <= 1`. `unit="pixel"`
  accepts any non-negative `x`/`y`.

### `style.py`

**`TextStyle`** — `@dataclass`, all fields optional with defaults per
[SPEC.md §5](SPEC.md#5-textstyle--fully-customizable-custom-fonts-layer-0):
`font="Arial"`, `font_size=48`, `color="white"`, `outline_color="black"`,
`outline_width=0`, `bg_color=None`, `align="center"`, `max_width=None`. No
validation beyond type — an invalid `font` path is only discovered by
`RenderStrategy` at render time (Layer 0 has no filesystem access).

### `animation.py`

**`Animation(ABC)`** — `duration: float` (required in every subclass;
`ValueError` if `< 0`). Abstract `_apply(self, clip, backend_ctx) -> Any`,
called only by a `RenderStrategy`.

| Class | Extra field | Values |
|---|---|---|
| `FadeAnimation` | `direction: Literal["in", "out"]` | fade opacity over `duration` |
| `SlideAnimation` | `direction: Literal["left","right","top","bottom"]` | slide in/out from that edge over `duration` |
| `ZoomAnimation` | `direction: Literal["in", "out"]` | scale over `duration` |

### `transition.py`

**`Transition(ABC)`** — `duration: float = 0`. Abstract
`_apply(self, outgoing_clip, incoming_clip, backend_ctx) -> Any`, called
only by a `RenderStrategy`, given the two `VideoClip`s it sits between.

| Class | Behavior |
|---|---|
| `CutTransition` | default; `duration` forced to `0`; no visual effect |
| `FadeTransition` | outgoing clip fades to black, incoming fades in, over `duration` |
| `DissolveTransition` | crossfade between outgoing and incoming over `duration` |

### `asset.py`

**`Asset`** — `@dataclass`. `path: str`, `type: Literal["video","image","audio"]`,
`duration: float | None = None`, `resolution: tuple[int,int] | None = None`,
`fps: float | None = None`. Constructed with only `path`/`type` by
`TimelineBuilder` — the metadata fields stay `None` until `AssetLoader`
(§2.2) resolves them at render time. No I/O in this class.

### `clip.py`

**`Clip(ABC)`** — `start: float`, `end: float | None`,
`animation: Animation | None = None`. `__post_init__` raises
`TimeRangeError` if `end is not None and end <= start`.

- **`VideoClip(Clip)`** — adds `asset: Asset` (must have
  `asset.type == "video"`), `trim_in: float = 0`, `trim_out: float | None = None`,
  `transition_in: Transition | None = None`. `transition_in` only exists on
  `VideoClip` — transitions are specifically clip-to-clip on a `VideoTrack`.
- **`ImageClip(Clip)`** — adds `asset: Asset` (`asset.type == "image"`). No
  `transition_in` field (images don't participate in clip-to-clip video
  transitions).

### `overlay.py`

**`Overlay(ABC)`** — `start: float`, `end: float | None`,
`position: Position`, `animation: Animation | None = None`. Same
`TimeRangeError` check as `Clip`.

- **`TextOverlay(Overlay)`** — adds `text: str`,
  `style: TextStyle = field(default_factory=TextStyle)`.
- **`ImageOverlay(Overlay)`** — adds `asset: Asset` (`asset.type == "image"`).

### `audio.py`

**`AudioLayer`** — `@dataclass`. `asset: Asset` (`asset.type == "audio"`),
`start: float = 0`, `volume: float = 1.0`, `fade_in: float = 0`,
`fade_out: float = 0`. No explicit `end` — duration comes from the
resolved `Asset` at render time (an `AudioLayer` always plays its asset in
full from `start`, minus any future trim support).

### `caption.py`

**`Caption`** — `@dataclass`. `text: str`, `start: float`, `end: float`.
Deliberately has no `style` field — a `CaptionTrack` (below) carries one
shared `TextStyle` for all its captions, since a track's captions are
rendered with one consistent look.

### `ports.py`

**`SubtitleSource(ABC)`** — zero third-party imports (the abstract port).
Abstract `generate(self, *, script_text: str | None, voice_audio: str) -> list[Caption]`.
Concrete implementations (Layer 2, §2.3) may ignore `script_text` (pure
ASR) or require it (hybrid) — the *signature* stays uniform across every
`SubtitleSource` so `TimelineBuilder.captions()` can call any of them the
same way; anything source-specific (e.g. a `.srt` file path, a Whisper
model size) is a **constructor** argument on the concrete class, not part
of this method.

### `track.py`

**`Track(ABC, Generic[T])`** — `name: str`, private `_items: list[T] = []`.

- `add(item: T) -> T` — calls `self._validate_item(item)` then appends.
- `add_many(items: Iterable[T]) -> list[T]` — `[self.add(i) for i in items]`.
- `items() -> tuple[T, ...]` — read-only view (`tuple(self._items)`).
- `_validate_item(item: T) -> None` (abstract) — subclass hook.

| Subclass | `T` | `_validate_item` rule |
|---|---|---|
| `VideoTrack` | `Clip` | rejects non-`Clip` with `TrackItemTypeError`; additionally rejects a new `VideoClip` whose `[start, end)` overlaps any existing clip's range with `ClipOverlapError`; rejects a non-last clip with `end=None` (`TimeRangeError`) |
| `OverlayTrack` | `Overlay` | rejects non-`Overlay` with `TrackItemTypeError`; **no** overlap check — multiple overlays may legitimately be on screen at once |
| `AudioTrack` | `AudioLayer` | rejects non-`AudioLayer`; no overlap check — layered audio is normal |
| `CaptionTrack` | `Caption` | rejects non-`Caption`; no overlap check; **extra field** `style: TextStyle = field(default_factory=TextStyle)`, applied to every `Caption` on this track when rendering |

### `timeline.py`

**`Timeline`** — `@dataclass`. `resolution: tuple[int,int]`, `fps: int = 30`,
`tracks: dict[str, Track] = field(default_factory=dict)`.

- `get_track(name: str) -> Track | None`.
- `_validate() -> None` — raises `TimelineValidationError` if `tracks` is
  empty. Per-track invariants (overlap, item type) are already enforced at
  `add()` time by each `Track` subclass, so `_validate()` only checks
  cross-cutting/whole-timeline conditions (currently just non-emptiness;
  future checks — e.g. "at least one `VideoTrack`" — extend this method
  without changing `Track`).

## Layer 1 — Builder API (`builder/timeline_builder.py`)

**`TimelineBuilder`** — wraps one `Timeline` instance being assembled.
`__init__(self, resolution: tuple[int,int], fps: int = 30)` creates
`self._timeline = Timeline(resolution=resolution, fps=fps)`. Every method
below returns `self` (the builder) unless noted, so calls chain; calling
`.build()` more than once is allowed and always re-validates/returns the
same underlying `Timeline` reflecting whatever has been chained so far.

- **`track(name, track_cls=VideoTrack) -> TimelineBuilder`** — calls
  `self._get_or_create_track(name, track_cls)` and discards the result
  (kept for the return-self chaining contract). Use when you want a track
  to exist before referencing it by name elsewhere, or to pre-create a
  `CaptionTrack` with a custom `style`.
- **`clip(path, start, end=None, *, track="main", transition_in=None) -> TimelineBuilder`**
  — wraps `Asset(path=path, type="video")`, builds a `VideoClip`, adds it
  to `self._get_or_create_track(track, VideoTrack)`.
- **`clips(specs: list[dict], *, track="main") -> TimelineBuilder`** — for
  each `spec` dict, calls `self.clip(track=track, **spec)`; no logic beyond
  the loop.
- **`text(text, start, end, *, position=Position.preset(Alignment.CENTER), style=None, animation=None, track="overlay") -> TimelineBuilder`**
  — `style` defaults to `TextStyle()` if `None`; builds a `TextOverlay`,
  adds it to `self._get_or_create_track(track, OverlayTrack)`.
- **`image(path, start, end=None, *, position, animation=None, track="overlay") -> TimelineBuilder`**
  — `position` is required (no default; Python raises `TypeError` if
  omitted, same as any required keyword-only arg); wraps
  `Asset(path=path, type="image")`, builds an `ImageOverlay`.
- **`audio(path, *, start=0, volume=1.0, fade_in=0, fade_out=0, track="audio") -> TimelineBuilder`**
  — wraps `Asset(path=path, type="audio")`, builds an `AudioLayer`, adds it
  to `self._get_or_create_track(track, AudioTrack)`.
- **`captions(source: SubtitleSource, *, script_text, voice_audio, style=None, track="captions") -> TimelineBuilder`**
  — calls `source.generate(script_text=script_text, voice_audio=voice_audio)`,
  gets back `list[Caption]`, adds them via `add_many()` to
  `self._get_or_create_track(track, CaptionTrack)`; if `style` is given and
  the track was just created, sets `CaptionTrack.style = style`. Raises
  whatever `source.generate()` raises (e.g. `ValueError` from
  `HybridSubtitleSource` if `script_text` is falsy) — the builder does not
  wrap or suppress it.
- **`build() -> Timeline`** — calls `self._timeline._validate()`, returns
  `self._timeline`.
- **`_get_or_create_track(name, track_cls) -> Track`** (private) — if
  `name` not in `self._timeline.tracks`, creates `track_cls(name=name)` and
  stores it; if it exists but `type(existing) is not track_cls`, raises
  `TrackTypeConflictError`; otherwise returns the existing track.

Note what's *not* here: no `.render()`, no `AssetLoader`, no concrete
`SubtitleSource` import anywhere in this module — see
[ARCHITECTURE.md's three design resolutions](ARCHITECTURE.md#three-design-resolutions-that-keep-the-rule-honest)
for why.

## Layer 2 — Render Strategy & provider strategies (`strategies/`)

Shared error module `strategies/errors.py`: `AssetResolutionError(RuntimeError)`,
`RenderError(RuntimeError)`, `SubtitleGenerationError(RuntimeError)`.

### 2.1 `render/base.py` — `RenderStrategy(ABC)`

`render(self, timeline: Timeline, output_path: str) -> Path` (abstract).

### 2.2 `strategies/asset/loader.py` — `AssetLoader`

`resolve(self, asset: Asset) -> Asset` — if `asset.duration is not None`
(already resolved), returns `asset` unchanged (idempotent). Otherwise
returns a **new** `Asset` with metadata filled in (never mutates the input
in place, so a `Timeline`'s original `Asset` objects stay exactly what the
builder created):

| `asset.type` | How metadata is read |
|---|---|
| `"video"` | `moviepy.VideoFileClip(asset.path)` → `.duration`, `.size` (resolution), `.fps` |
| `"image"` | `PIL.Image.open(asset.path)` → `.size` (resolution); `duration=None`, `fps=None` |
| `"audio"` | `moviepy.AudioFileClip(asset.path)` → `.duration`; `resolution=None`, `fps=None` |

Wraps any `FileNotFoundError`/`OSError` from the underlying library into
`AssetResolutionError` with the offending path in the message.

### 2.3 `strategies/subtitle/` — `SubtitleSource` implementations

- **`FileSubtitleSource(SubtitleSource)`** — `__init__(self, path: str)`.
  `generate()` ignores `script_text`/`voice_audio`, parses `self.path` with
  the `srt` library, returns one `Caption` per subtitle entry.
- **`WhisperSubtitleSource(SubtitleSource)`** — `__init__(self,
  model_size: str = "base", device: str = "cpu")`. `generate()` ignores
  `script_text`, runs `faster-whisper` transcription on `voice_audio`, maps
  each recognized segment to `Caption(text=segment.text, start=segment.start,
  end=segment.end)`.
- **`HybridSubtitleSource(SubtitleSource)`** — same constructor as
  `WhisperSubtitleSource`. `generate()` raises `ValueError` if
  `script_text` is `None`/empty ("HybridSubtitleSource requires
  script_text"); otherwise runs forced alignment between `script_text` and
  `voice_audio` (via `faster-whisper`, discarding its recognized text) and
  returns `Caption`s whose `text` is taken verbatim from `script_text`
  segments, with `start`/`end` from the alignment.

All three wrap unexpected library failures in `SubtitleGenerationError`.

### 2.4 `render/moviepy_strategy.py` — `MoviePyRenderStrategy(RenderStrategy)`

`__init__(self, asset_loader: AssetLoader = field(default_factory=AssetLoader))`
— this is the only place `AssetLoader` gets wired in by default, so
`TimelineBuilder` never has to know it exists.

`render(timeline, output_path)` algorithm:

1. For each `VideoTrack`, in item order: resolve each `VideoClip.asset` via
   `self.asset_loader.resolve(asset)`; build a MoviePy `VideoFileClip`
   trimmed to `[trim_in, trim_out]`; apply `animation._apply()` if set;
   apply `transition_in._apply()` between this clip and the previous one
   (straight concat for `CutTransition`, crossfade compositing for
   `FadeTransition`/`DissolveTransition`).
2. Concatenate the track's clips into one base video clip.
3. For each `OverlayTrack` item: resolve `Position` into pixel coordinates
   using `timeline.resolution` (preset → lookup table; `unit="ratio"` →
   multiply by resolution; `unit="pixel"` → used as-is); build a MoviePy
   `TextClip`/`ImageClip` positioned and timed accordingly; apply
   `animation._apply()` if set.
4. For each `AudioTrack` item: resolve the asset, build an
   `AudioFileClip`, apply `volume`/`fade_in`/`fade_out`, offset by `start`.
5. For each `CaptionTrack`: build one `TextClip` per `Caption`, styled with
   the track's shared `style`, timed at `caption.start`/`caption.end`.
6. Composite video layers with `CompositeVideoClip`, audio layers with
   `CompositeAudioClip`, at `timeline.fps`/`timeline.resolution`.
7. `write_videofile(output_path, fps=timeline.fps)`; return `Path(output_path)`.

Any MoviePy/ffmpeg failure at any step is wrapped in `RenderError` with
enough context (track name, item index) to locate the failing element.

## Layer 3 — Design: Script & Template (`design/`)

### 3.1 `script.py` — `Script`

`__init__(self, path: str)`. `parse(self) -> TimelineBuilder` — reads the
JSON/YAML file at `path`, validates it against a `pydantic` model
(`resolution`, `fps`, `clips: list[ClipSpec]`, `texts: list[TextSpec]`,
`images: list[ImageSpec]`, `audio: list[AudioSpec]`,
`captions: CaptionSpec | None`), then calls the matching `TimelineBuilder`
method once per entry (`.clip(**clip_spec)`, `.text(**text_spec)`, etc.) in
the order: clips, texts, images, audio, captions. Returns the
**not-yet-built** `TimelineBuilder` so callers may chain further manual
calls before `.build()`. Raises `ScriptValidationError(ValueError)`
wrapping the underlying `pydantic.ValidationError`, with the failing
field path in the message.

### 3.2 `template.py` — `Template(ABC)`

`apply(self, builder: TimelineBuilder, **params) -> TimelineBuilder`
(abstract). A concrete `Template` is expected to declare its actual
required parameters as named keyword arguments in its own `apply()`
override (not a loose `**params` dict) so missing/invalid parameters fail
immediately and legibly — the base class's `**params` only exists because
different templates need different parameters and there's no shared
signature to enforce.

Example: **`FacelessQuoteTemplate(Template)`**

```
apply(self, builder, *, background_clip: str, quote_text: str, music: str,
      voice_audio: str | None = None, style: TextStyle | None = None,
      subtitle_source: SubtitleSource | None = None) -> TimelineBuilder
```

Algorithm: `builder.clip(background_clip, start=0)` →
`builder.text(quote_text, start=0, end=None, position=Position.preset(Alignment.CENTER), style=style or TextStyle())`
→ `builder.audio(music, volume=0.3)` → if `voice_audio` is given,
`builder.captions(subtitle_source or HybridSubtitleSource(), script_text=quote_text, voice_audio=voice_audio)`
→ return `builder`. `background_clip`/`quote_text`/`music` are required
(plain `TypeError` from Python if omitted, since they're named parameters,
not defaulted).

## Layer 4 — Automation: Batch Producer (`automation/batch_producer.py`)

**`BatchResult`** — `@dataclass`. `succeeded: list[Path]`,
`failed: list[tuple[Path, Exception]]`. *(This refines
[SPEC.md §11](SPEC.md#11-batchproducer-layer-4)'s illustrative
`run() -> None` to a real return value — SPEC.md has been updated to
match.)*

**`BatchProducer`** — `__init__(self, spec_dir: str, render_strategy: RenderStrategy | None = None)`
— `render_strategy` defaults to `MoviePyRenderStrategy()` if not given.

`run(self, output_dir: str) -> BatchResult`:

1. List every spec file in `spec_dir` (non-recursive, `*.json`/`*.yaml`/`*.yml`).
2. For each spec file, in filename order: `Script(path).parse().build()` →
   `self.render_strategy.render(timeline, output_dir / f"{spec.stem}.mp4")`.
3. On success, append the output path to `BatchResult.succeeded`. On any
   exception (`ScriptValidationError`, `RenderError`, or anything else),
   log it via `logging.getLogger("vidgen.automation")` at `ERROR` level
   with the spec filename, append `(spec_path, exception)` to
   `BatchResult.failed`, and continue to the next file — one bad spec never
   stops the batch.
4. Return the accumulated `BatchResult` after processing every spec file.

`Agent` — not designed in v1; see [PLAN.md](PLAN.md) roadmap for the v2
extension point this layer leaves open.

---
See also: [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [SPEC.md](SPEC.md) · [PLAN.md](PLAN.md)
