# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

**This repository is currently documentation-only.** `src/` and `tests/` exist but are empty — there is no implementation code, no `pyproject.toml`/`setup.py`, and no build/lint/test tooling configured yet. Do not assume any of that exists; check before referencing commands. When implementation begins, this file should be updated with the actual commands (install, test, lint) once they're defined.

## What vidgen is

A programmable, code-first **video editing engine** for Python — the kind of model that could power a tool like CapCut/Premiere/Adobe, consumed as a library/SDK rather than a GUI app. Every editing operation (cut/join clips, text/image overlays with animation, transitions, audio mixing, captions, rendering) is expressed through a fluent Builder API. Automated batch production is one consumer built *on top* of the engine, not what the engine fundamentally is — don't reintroduce "it's a batch pipeline" framing into docs or code.

## Documentation map

The full design lives in `docs/`, in increasing order of detail:

- [docs/PRD.md](docs/PRD.md) — goals, non-goals, audience, v1 feature scope (product level)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — the layer stack, OOP class diagram, package layout
- [docs/SPEC.md](docs/SPEC.md) — API shape (classes/methods) per layer
- [docs/DESIGN.md](docs/DESIGN.md) — implementation-ready reference: every field's type/default, every invariant, every algorithm step-by-step
- [docs/PLAN.md](docs/PLAN.md) — roadmap, finalized design decisions, and the v1 build-order checklist (module-by-module, each with its own test)

Before writing any code under `src/vidgen/`, read DESIGN.md for the module being implemented — it is the authoritative source for field names, defaults, and validation rules, not SPEC.md (which only shows the shape) and not this file.

## Core architectural rule: Dependency Inversion

The entire design is organized as 5 strictly one-directional layers. **A lower layer must never import from a higher layer.** Layer 0 has zero third-party imports — this is the load-bearing constraint that keeps the renderer/ASR backend swappable.

```
Layer 4  Automation / Agent / Batch Producer   (automation/)   — depends on everything below
Layer 3  Design / Template / Script            (design/)
Layer 2  Render Strategy                       (strategies/)   — the ONLY layer importing moviepy/ffprobe/faster-whisper/srt/Pillow
Layer 1  Builder API                           (builder/)      — TimelineBuilder (fluent, chainable)
Layer 0  Domain Model                          (domain/)       — pure dataclasses/ABCs, NO third-party imports at all
```

Planned package layout (`src/vidgen/`, not yet created):

```
domain/       timeline.py, track.py, clip.py, overlay.py, audio.py, caption.py,
              asset.py, position.py, style.py, animation.py, transition.py, ports.py
builder/      timeline_builder.py
strategies/   render/base.py, render/moviepy_strategy.py, asset/loader.py,
              subtitle/file_source.py, subtitle/whisper_source.py, subtitle/hybrid_source.py
design/       script.py, template.py
automation/   batch_producer.py
```

Three resolutions worth internalizing before touching this design (details in [ARCHITECTURE.md §2](docs/ARCHITECTURE.md#2-the-five-layers)):

- **Rendering is not a `TimelineBuilder` method.** `.build()` returns a plain `Timeline` (Layer 0); rendering is a separate call, `SomeRenderStrategy().render(timeline, "out.mp4")`, made by whatever sits above the stack. This keeps Layer 1 free of any Layer 2 import.
- **Asset metadata (duration/resolution/fps) is resolved at render time, not build time.** `TimelineBuilder.clip(path, ...)` only stores `Asset(path=path)` — no `ffprobe` call. `RenderStrategy` calls `AssetLoader` when it actually renders.
- **Captions are injected, not constructed internally.** `SubtitleSource` is an abstract port declared in `domain/ports.py` (Layer 0, zero third-party imports); concrete implementations (`FileSubtitleSource`, `WhisperSubtitleSource`, `HybridSubtitleSource`) live in Layer 2 and are passed into `TimelineBuilder.captions(source, ...)` by the caller.

When implementing or reviewing code in this repo, verifying the DIP rule means checking imports, not just behavior: a `grep` for third-party imports in `domain/` or `builder/` should always come back empty.

## Key naming/design decisions already finalized (see [PLAN.md §2](docs/PLAN.md#2-finalized-design-decisions) for full rationale)

- `Timeline` (Layer 0, inert data) is split apart from `TimelineBuilder` (Layer 1, chainable construction) — they were previously conflated into one facade; don't re-merge them.
- `RenderStrategy` (not `RenderBackend`), `BatchProducer` (not `BatchPipeline`) — these renames already happened at the design level.
- `Template` (Layer 3, ABC with `apply(builder, **params) -> TimelineBuilder`) is a distinct concept from `Script` (Layer 3, declarative JSON/YAML parsed via `pydantic`) — both exist in v1, they are not alternatives to choose between.
- `Agent` (natural-language-driven generation) is a **documented v2 extension point only** — do not design or stub an `Agent` class as part of v1 work unless explicitly asked.
- Animation/Transition stay a fixed preset set in v1 (fade/slide/zoom; cut/fade/dissolve) — this was deliberately reconsidered and reconfirmed, not an oversight. Don't generalize to a keyframe engine without being asked.

## Build order

[PLAN.md §3](docs/PLAN.md#3-v1-implementation-checklist) specifies an exact build order — don't start a layer before the one below it is complete and its layer-level purity test passes: Domain (`domain/`) → Builder (`builder/`) → Render Strategy (`strategies/`) → Design (`design/`) → Automation (`automation/`) → end-to-end integration. Each module gets its own unit test immediately after it, per the checklist in that section. Two layer-level tests recur throughout: confirm `domain/` and `builder/` import successfully with `moviepy`/`faster-whisper`/`srt` **not installed**, as proof of Layer 0/1 purity.
