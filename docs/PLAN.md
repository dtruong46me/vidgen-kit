# Plan — vidgen

Roadmap, finalized design decisions, and the v1 implementation checklist.
See [PRD.md](PRD.md) for product goals, [ARCHITECTURE.md](ARCHITECTURE.md)
for the layered architecture, and [SPEC.md](SPEC.md) for the detailed API.

## 1. Roadmap

- **v1 (current)**: full 5-layer Dependency Inversion stack — Domain Model
  (pure dataclasses/ABCs incl. the `SubtitleSource` port), `TimelineBuilder`
  fluent API, `RenderStrategy`/`MoviePyRenderStrategy` + `AssetLoader` +
  subtitle strategies, `Script` + `Template`, `BatchProducer`. Feature
  depth: cut/join + basic transitions, text/image overlay + basic
  animation, custom fonts, alignment presets + free coordinates, audio
  mixing, captions (file/auto/hybrid), reusable Templates. Also includes an
  optional HTTP API (`api/`, §3.7) — a FastAPI wrapper one layer above
  Automation, for consumers that want vidgen as a service instead of a
  library import.
- **v2 (later)**: `Agent` (Layer 4 — natural-language intent →
  `Script`/`Template` selection and parametrization), an alternate
  `RenderStrategy` for performance at scale (e.g. `FFmpegRenderStrategy`),
  TTS voice generation, thumbnail generator, exporting multiple aspect
  ratios at once (9:16/16:9), a richer keyframe/property animation system
  if the fixed-preset one proves limiting.

## 2. Finalized design decisions

1. **Naming**: `Project` → **`Timeline`** (matches its actual nature as a
   timeline of tracks).
2. **Architecture rebuilt around Dependency Inversion**: the 5-layer stack
   Domain Model → Builder API → Render Strategy → Design (Script/Template)
   → Automation ([ARCHITECTURE.md §1–2](ARCHITECTURE.md#1-most-important-design-principle-dependency-inversion))
   replaces the earlier Domain → Asset/Caption → Render → Config →
   Orchestration framing. Rationale: vidgen is a real, extensible editing
   engine, not just a batch script — this stack makes every implementation
   detail (renderer, ASR, animation depth) swappable without touching the
   domain model ([PRD.md §1](PRD.md#1-goals--non-goals)).
3. **`Timeline` (data) vs `TimelineBuilder` (fluent construction) split
   apart** — previously conflated in one `Timeline` facade with `add_*`
   methods. Now `Timeline` is inert data (Layer 0) and `TimelineBuilder` is
   the chainable API that produces it (Layer 1)
   ([SPEC.md §1–2](SPEC.md#1-timeline--domain-data-layer-0)).
4. **`RenderStrategy`** (renamed from the earlier `RenderBackend`) — same
   contract, Strategy-pattern vocabulary to match the reference
   architecture ([SPEC.md §8](SPEC.md#8-renderstrategy--provider-strategies-layer-2)).
5. **Asset metadata resolution deferred to render time** — `AssetLoader` is
   called by `RenderStrategy`, not by `TimelineBuilder`. Keeps the Builder
   free of any `ffprobe`/MoviePy dependency
   ([SPEC.md §2](SPEC.md#2-timelinebuilder--fluent-construction-api-layer-1),
   [§8](SPEC.md#8-renderstrategy--provider-strategies-layer-2)).
6. **`SubtitleSource` is an abstract port defined in Domain (Layer 0)**,
   zero third-party imports; concrete sources (`File`/`Whisper`/`Hybrid`)
   live in Layer 2 and are injected into `TimelineBuilder.captions()` by
   the caller — dependency injection in service of the one-way-dependency
   rule ([SPEC.md §7](SPEC.md#7-caption--subtitlesource--port-layer-0--strategies-layer-2)).
7. **`Template` introduced** (Layer 3) — reusable parametrized edit
   recipes, alongside `Script` (declarative JSON/YAML), as the two ways to
   express a "design" above the raw Builder API
   ([SPEC.md §9–10](SPEC.md#9-template--reusable-parametrized-edit-recipes-layer-3)).
8. **`BatchPipeline` renamed `BatchProducer`** (Layer 4). `Agent`
   (AI-driven generation) is a documented v2 extension point only — no
   interface designed in v1, to avoid speculative design before there's a
   concrete use case
   ([SPEC.md §11](SPEC.md#11-batchproducer-layer-4)).
9. **Batch config**: `Script` (JSON/YAML) is a thin, validated mapping onto
   `TimelineBuilder` calls — the fluent Builder API remains the official,
   complete interface ([SPEC.md §10](SPEC.md#10-script--declarative-spec-layer-3)).
10. **Overlay positioning**: both presets (`Alignment`) and free
    coordinates (`Position.custom`)
    ([SPEC.md §4](SPEC.md#4-position--alignment--presets-and-free-coordinates-layer-0)).
11. **Text style**: fully customizable from v1, optional fields with
    sensible defaults
    ([SPEC.md §5](SPEC.md#5-textstyle--fully-customizable-custom-fonts-layer-0)).
12. **Animation/Transition stay simple presets in v1** (fade/slide/zoom for
    overlays; cut/fade/dissolve for transitions) — reconsidered and
    reconfirmed this round rather than generalizing to a keyframe engine,
    to keep v1 scope shippable while the DIP layering already leaves room
    to grow this later
    ([PRD.md §1](PRD.md#1-goals--non-goals),
    [SPEC.md §6](SPEC.md#6-animation--transition--basic-presets-layer-0)).

## 3. v1 implementation checklist

No code exists in `src/` yet. Build in the exact layer order from
[ARCHITECTURE.md §2](ARCHITECTURE.md#2-the-five-layers) — each module gets
its own unit test written right after it, and a layer isn't "done" until
its own layer-level test passes. Don't start a layer before the one below
it is done. Field/method details for every class are in [SPEC.md](SPEC.md).

### 3.1 Domain Model (`domain/`) — pure Python, zero third-party imports

- [x] `position.py` — `Alignment` enum, `Position.preset()` /
      `Position.custom()`
  - [x] Test: `preset()` stores the given `Alignment`; `custom()` stores
        `x`/`y`/`unit` correctly for both `unit="ratio"` and `unit="pixel"`
- [x] `style.py` — `TextStyle` dataclass
  - [ ] Test: default values match [SPEC.md §5](SPEC.md#5-textstyle--fully-customizable-custom-fonts-layer-0);
        overriding individual fields leaves the rest at their defaults
- [x] `animation.py` — `Animation` ABC, `FadeAnimation`, `SlideAnimation`,
      `ZoomAnimation`
  - [ ] Test: `Animation` cannot be instantiated directly (abstract);
        each subclass stores `duration` + its own `direction`
- [x] `transition.py` — `Transition` ABC, `CutTransition`,
      `FadeTransition`, `DissolveTransition`
  - [ ] Test: same shape as the `animation.py` test above, applied to
        `Transition` and its subclasses
- [x] `asset.py` — `Asset` dataclass (`path`, `type`, `duration=None`,
      `resolution=None`, `fps=None`)
  - [ ] Test: constructing with only `path` leaves metadata fields `None`
        (no I/O performed)
- [x] `clip.py` — `Clip` ABC, `VideoClip`, `ImageClip`
  - [ ] Test: `VideoClip`/`ImageClip` hold `asset`, `start`, `end`,
        `trim_in`/`trim_out`, `transition_in`; invalid `end < start` is
        rejected
- [x] `overlay.py` — `Overlay` ABC, `TextOverlay`, `ImageOverlay`
  - [ ] Test: `TextOverlay` requires `text`/`style`; `ImageOverlay`
        requires `position`; both accept an optional `animation`
- [x] `audio.py` — `AudioLayer`
  - [ ] Test: `volume`/`fade_in`/`fade_out` defaults and overrides
- [x] `caption.py` — `Caption` dataclass
  - [ ] Test: holds `text` + start/end timestamps
- [x] `ports.py` — `SubtitleSource` ABC (abstract `generate(...)`)
  - [ ] Test: cannot be instantiated directly; a minimal subclass
        implementing `generate()` can be
- [x] `track.py` — `Track` ABC, `VideoTrack`, `OverlayTrack`,
      `AudioTrack`, `CaptionTrack`
  - [ ] Test: `add()` calls `_validate_item()` and rejects the wrong item
        type per subclass (e.g. `VideoTrack.add(TextOverlay(...))` raises);
        `add_many()` returns all added items in order; `items()` returns a
        read-only view
- [x] `timeline.py` — `Timeline` (resolution, fps, tracks)
  - [ ] Test: `get_track()` returns `None` for a missing name;
        `_validate()` catches overlapping items on the same track
- [ ] **Layer test**: the whole `domain/` package imports and its full
      `pytest` suite passes in an environment with `moviepy`/
      `faster-whisper`/`srt` **not installed** — proof of Layer 0 purity

### 3.2 Builder API (`builder/`)

- [x] `timeline_builder.py` — `TimelineBuilder`
  - [x] Test: `.track()`/`.clip()`/`.text()`/`.image()`/`.audio()` each
        return the same `TimelineBuilder` instance (chaining)
  - [x] Test: `.clip(path, ...)` stores `Asset(path=path)` without
        touching the filesystem (no `ffprobe`/MoviePy call)
  - [x] Test: `.captions(source, ...)` calls the given `SubtitleSource`'s
        `generate()` and attaches the resulting `Caption`s to a
        `CaptionTrack`, using a fake in-test `SubtitleSource` subclass —
        no concrete subtitle library involved
  - [x] Test: `.build()` calls `Timeline._validate()` and returns a
        `Timeline` matching everything chained before it
- [x] **Layer test**: the `builder/` package imports successfully with
      `moviepy`/`faster-whisper`/`srt` **not installed** — proof that
      Layer 1 only depends on Layer 0

### 3.3 Render Strategy (`strategies/`) — the only layer importing heavy libs

- [x] `render/base.py` — `RenderStrategy` ABC
- [x] `asset/loader.py` — `AssetLoader`
  - [x] Test: `resolve()` on a real sample file in `assets/clips/` and
        `assets/music/` → returned `Asset.duration`/`resolution`/`fps`
        are real, sane values (no standalone `ffprobe` binary in this
        environment, so compared against MoviePy's/Pillow's own reading
        rather than a separate `ffprobe` invocation); also covers
        idempotency, no-mutation, and a missing-file `AssetResolutionError`
- [x] `render/moviepy_strategy.py` — `MoviePyRenderStrategy`
  - [x] Test: render a minimal `Timeline` (1 short `VideoClip` + 1
        `TextOverlay`) to a temp file → output file exists, re-opens with
        MoviePy, and has the expected duration/resolution
  - [x] Test: confirms `AssetLoader.resolve()` is called during `render()`,
        not before (metadata resolution happens at render time, per
        [ARCHITECTURE.md §2](ARCHITECTURE.md#three-design-resolutions-that-keep-the-rule-honest))
  - [x] Test: render a `Timeline` with a `FadeAnimation` overlay and a
        `DissolveTransition` between 2 clips → render completes without
        error (visual correctness checked manually, not asserted)
- [x] `subtitle/file_source.py` — `FileSubtitleSource`
  - [x] Test: parse a sample `.srt` fixture → returned `Caption` list has
        the exact text/timestamps from the file
- [x] `subtitle/whisper_source.py` — `WhisperSubtitleSource`
  - [x] Test (slow, opt-in, `@pytest.mark.slow`): skips automatically
        until a real sample voice clip exists in `assets/voice/` (not
        yet added to the repo) — once present, runs a real transcription
        and asserts a non-empty `Caption` list with increasing timestamps
- [x] `subtitle/hybrid_source.py` — `HybridSubtitleSource`
  - [x] Test: the word-distribution alignment algorithm is unit-tested
        directly against fake Whisper-segment stubs (no model/network
        needed) — returned captions' **text** comes from the script, not
        the (fake) ASR output, only timestamps come from the segments;
        plus a `@pytest.mark.slow` opt-in test against a real sample in
        `assets/voice/`, same skip condition as above
- [x] **Layer test**: a stub `RenderStrategy` swapped in for
      `MoviePyRenderStrategy` in a test requires no change to `builder/`
      or `domain/` code — proof of renderer swappability

### 3.4 Design (`design/`)

- [x] `script.py` — `Script` (JSON/YAML, `pydantic`-validated; `extra="forbid"`
      at every level so unknown fields are rejected, not ignored)
  - [x] Test: a sample spec file → drives `TimelineBuilder` → the
        resulting `Timeline`'s tracks/items match a `Timeline` built by
        calling the equivalent `TimelineBuilder` methods directly (both a
        JSON and a YAML variant of the same spec are covered)
  - [x] Test: an invalid spec (unknown field, missing required field) is
        rejected with a clear validation error, not a silent partial
        `Timeline` (`ScriptValidationError` wrapping `pydantic.ValidationError`)
- [x] `template.py` — `Template` ABC + one concrete example
      (`FacelessQuoteTemplate`)
  - [x] Test: applying the example `Template` with sample params produces
        a `Timeline` with the expected tracks/items
  - [x] Test: applying it twice with different params produces different
        but structurally-equivalent timelines (same tracks, different
        content)

### 3.5 Automation (`automation/`)

- [x] `batch_producer.py` — `BatchProducer` (`BatchResult` dataclass with
      `succeeded`/`failed`; non-recursive `*.json`/`*.yaml`/`*.yml` glob of
      `spec_dir`, processed in filename order; `render_strategy` defaults to
      `MoviePyRenderStrategy()`)
  - [x] Test: `spec_dir` with 2 valid sample specs → `run()` produces 2
        output files in `output_dir`
  - [x] Test: `spec_dir` with 1 valid + 1 intentionally broken spec →
        `run()` still produces the output for the valid spec, logs the
        broken one's error via `logging.getLogger("vidgen.automation")`,
        and does not raise

### 3.6 End-to-end

- [x] Integration test: 1 real sample `Script` (clip + text + audio +
      hybrid captions) → `BatchProducer.run()` → resulting file plays
      correctly and matches the spec's declared duration/resolution
      (`tests/e2e/test_end_to_end.py`; marked `@pytest.mark.slow` and
      skipped until a real sample clip exists under `assets/voice/`, same
      opt-in convention as the §3.3 Whisper tests)
- [x] Integration test: 1 real `Template` applied with real assets from
      `assets/` → `TimelineBuilder` → `MoviePyRenderStrategy` → renders
      successfully

### 3.7 HTTP API (`api/`) — thin FastAPI wrapper, sits above Automation

Not part of the original 5-layer stack in [ARCHITECTURE.md](ARCHITECTURE.md)
— an added consumer alongside `automation/`, for driving vidgen as an HTTP
service instead of a library import. Rendering is slow, so every render is
an async job: the endpoint returns a `job_id` immediately and the caller
polls for completion rather than blocking the request. Full usage guide:
[API.md](API.md).

- [x] `jobs.py`: `JobStore`/`Job`/`JobStatus` — in-memory job bookkeeping,
      each job's render running on a background thread pool
      (`tests/api/test_api.py`)
- [x] `templates_registry.py`: registry of `Template`s exposed over the
      API, with `GET /templates` parameters derived by introspecting each
      template's `apply()` signature rather than hand-maintained
- [x] `POST /renders`: a `Script`-shaped JSON body → background render →
      `job_id` (reuses `design.script.build_timeline_from_spec`, extracted
      from `Script.parse()` so the API can validate/build a spec already in
      memory without writing a temp file)
- [x] `GET /templates`, `POST /templates/{name}/render`: list registered
      `Template`s and their params; apply one with parameters → background
      render → `job_id`
- [x] `POST /edit/concat`, `/edit/trim`, `/edit/add-audio`,
      `/edit/overlay-text`, `/edit/overlay-image`, `/edit/captions`:
      single-purpose editing operations (join clips, extract a segment, mix
      in background music, burn in text/image/captions) that don't require
      assembling a `Script`/`Template` — each builds a small `Timeline`
      directly (bypassing `TimelineBuilder` only for `concat`/`trim`, which
      need per-clip `trim_in`/`trim_out` that `TimelineBuilder.clip()`
      doesn't expose) and submits it through the same job queue
      (`tests/api/test_edits.py`)
- [x] `GET /jobs/{id}`, `GET /jobs/{id}/file`: poll job status; download the
      finished file (404 unknown job, 409 if not yet finished)
- [x] Integration test: full request/response cycle against a real
      `TestClient` + stub `RenderStrategy` for every endpoint, including a
      blocking-strategy test proving `GET /jobs/{id}/file` 409s while a job
      is still running (`tests/api/test_api.py`, `tests/api/test_edits.py`)
- [x] Bug fix found via `/edit/concat`: `VideoTrack._validate_item`
      (`domain/track.py`) rejected any open-ended (`end=None`) clip added
      after an earlier one, even in the ordinary case of several closed
      clips followed by one open-ended clip added last — the dedicated
      check was redundant with (and stricter than) the existing overlap
      check, which already fully enforces "at most one open-ended clip,
      and nothing else may overlap it" regardless of insertion order.
      Removed the redundant check; regression tests in
      `tests/domain/test_track.py`.

---
See also: [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [SPEC.md](SPEC.md) · [DESIGN.md](DESIGN.md) · [API.md](API.md)
