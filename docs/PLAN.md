# Plan — vidgen

Roadmap, finalized design decisions, and the v1 implementation checklist.
See [PRD.md](PRD.md) for product goals, [ARCHITECTURE.md](ARCHITECTURE.md)
for the layered architecture, and [SPEC.md](SPEC.md) for the detailed API.

## 1. Roadmap

- **v1 (current)**: full OOP domain layer (Track/Clip/Overlay ABCs),
  basic cut/join + transitions, text/image overlay + basic animation,
  custom fonts, alignment presets + free coordinates, audio mixing,
  captions (file/auto/hybrid), MoviePyBackend, BatchPipeline + JSON spec
  wrapper.
- **v2 (later)**: TTS voice generation, thumbnail generator,
  `FFmpegBackend` for performance at scale, exporting multiple aspect
  ratios at once (9:16/16:9), more advanced animation/transitions
  (free keyframing) if actually needed.

## 2. Finalized design decisions

1. **Naming**: `Project` → renamed to **`Timeline`** (more standard,
   matches its actual nature as a timeline of tracks).
2. **Batch config**: the Python API is the core; JSON/YAML is a thin
   mapping ([SPEC.md §8](SPEC.md#8-batchpipeline--config-json-as-a-thin-wrapper)).
3. **Overlay positioning**: both presets (`Alignment`) and free coordinates
   (`Position.custom`) ([SPEC.md §3](SPEC.md#3-position--alignment--presets-and-free-coordinates)).
4. **Text style**: fully customizable from v1, optional fields with
   sensible defaults ([SPEC.md §4](SPEC.md#4-textstyle--fully-customizable-custom-fonts)).
5. **Animation/Transition**: included in v1 scope but limited to
   **simple presets** (fade/slide/zoom for overlays; cut/fade/dissolve for
   transitions between clips) — not a general-purpose animation engine,
   staying true to the "simpler than CapCut/Premiere" spirit
   ([PRD.md §1](PRD.md#1-goals--non-goals)).
6. **Layering + OOP**: architecture split into 5 clear layers (Domain →
   Asset/Caption → Render → Config → Orchestration), using ABCs for every
   "family" of classes with multiple variants (`Track`, `Clip`, `Overlay`,
   `Animation`, `Transition`, `SubtitleSource`, `RenderBackend`), with a
   clear distinction between public API (`add_*`, `render`, `items()`) and
   private/protected helpers (`_validate_item`, `_get_or_create_track`,
   `_apply`).

## 3. v1 implementation checklist

No code exists in `src/` yet — start in the exact layer order from
[ARCHITECTURE.md §2](ARCHITECTURE.md#2-layered-architecture), finishing each
lower layer, with tests, before building the layer above it:

- [ ] **Domain (`core/`)**: `Position`/`Alignment`, `TextStyle`,
      `Animation` + subclasses, `Transition` + subclasses, `Clip`/`Overlay`
      + subclasses, `Track` + subclasses, `Timeline` (facade). Pure Python
      unit tests, no ffmpeg required.
- [ ] **Asset (`assets/`)**: `Asset`, `AssetLoader` (reads metadata via
      ffprobe/moviepy).
- [ ] **Caption (`captions/`)**: `SubtitleSource` ABC,
      `FileSubtitleSource`, `WhisperSubtitleSource`,
      `HybridSubtitleSource`.
- [ ] **Render (`render/`)**: `RenderBackend` ABC, `MoviePyBackend`.
- [ ] **Config (`config/`)**: `spec.py` mapping JSON/YAML → `Timeline` API.
- [ ] **Orchestration (`pipeline/`)**: `BatchPipeline`.
- [ ] Integration test: 1 sample JSON spec in `input/specs/` → renders to
      `output/` successfully end-to-end.

---
See also: [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [SPEC.md](SPEC.md)
