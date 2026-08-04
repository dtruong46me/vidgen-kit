# API.md — vidgen HTTP API

A thin [FastAPI](https://fastapi.tiangolo.com/) wrapper around the vidgen
engine (`design.Script`/`design.Template` → `TimelineBuilder` →
`RenderStrategy`), for consumers that want vidgen as an HTTP service instead
of a Python library import. See [PLAN.md §3.7](PLAN.md#37-http-api-api--thin-fastapi-wrapper-sits-above-automation)
for where this sits in the architecture.

Rendering a video takes seconds to minutes, so **every render is
asynchronous**: the endpoint that starts a render returns a `job_id`
immediately (HTTP 202), and the caller polls `GET /jobs/{job_id}` until the
job finishes, then downloads the result.

## 1. Install & run

```bash
pip install -e ".[api]"
uvicorn vidgen.api:create_app --factory --reload
```

This starts the server at `http://127.0.0.1:8000`. Interactive docs
(Swagger UI, generated automatically by FastAPI) are at
`http://127.0.0.1:8000/docs`; the raw OpenAPI schema is at `/openapi.json`.

`create_app()` accepts optional keyword arguments if you need to customize
where output files are written or which `RenderStrategy` runs jobs:

```python
from vidgen.api import create_app
from vidgen.strategies.render.moviepy_strategy import MoviePyRenderStrategy

app = create_app(
    output_dir="output",              # where rendered .mp4 files are written
    render_strategy=MoviePyRenderStrategy(),  # default; swap for a custom RenderStrategy
    max_workers=2,                    # size of the background render thread pool
)
```

## 2. Authentication

None in v1 — the API has no auth layer. Put it behind a reverse proxy /
gateway if you need to expose it beyond a trusted network.

## 3. Endpoints

| Method | Path                          | Purpose                                         |
| ------ | ----------------------------- | ------------------------------------------------ |
| GET    | `/health`                     | Liveness check                                   |
| GET    | `/templates`                  | List registered `Template`s and their params     |
| POST   | `/templates/{name}/render`    | Apply a `Template` → background render → job     |
| POST   | `/edit/concat`                | Join clips end to end                            |
| POST   | `/edit/trim`                  | Extract a time segment from one video            |
| POST   | `/edit/add-audio`             | Mix background music/audio into a video          |
| POST   | `/edit/overlay-text`          | Burn a text overlay onto a video                 |
| POST   | `/edit/overlay-image`         | Burn an image/watermark onto a video             |
| POST   | `/edit/captions`               | Burn captions onto a video                       |
| POST   | `/renders`                    | Submit a `Script`-shaped spec → background render → job |
| GET    | `/jobs/{job_id}`               | Poll a job's status                              |
| GET    | `/jobs/{job_id}/file`          | Download the finished file                       |

Every `POST` above returns the same `202 Accepted` job shape and is
polled/downloaded the same way (§3.6/§3.7) — `/edit/*` and `/templates/*`
just differ in what they let you describe with a single flat request body,
without assembling a full `Script`.

### 3.1 `GET /health`

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status": "ok"}
```

### 3.2 `GET /templates`

Lists every `Template` registered in `vidgen.api.templates_registry.TEMPLATES`,
with each parameter of its `apply()` method (name, whether it's required,
and its type) so a client can discover what a template needs without
reading Python source.

```bash
curl http://127.0.0.1:8000/templates
```

```json
[
  {
    "name": "faceless_quote",
    "description": "Background clip + centered quote text + background music, with",
    "params": [
      {"name": "background_clip", "required": true, "type": "str"},
      {"name": "quote_text", "required": true, "type": "str"},
      {"name": "music", "required": true, "type": "str"},
      {"name": "voice_audio", "required": false, "type": "str | None"},
      {"name": "style", "required": false, "type": "TextStyle | None"},
      {"name": "subtitle_source", "required": false, "type": "SubtitleSource | None"}
    ]
  }
]
```

To add a new template to this list, register its class in
`vidgen.api.templates_registry.TEMPLATES` — the listing and its param
description update automatically.

### 3.3 `POST /templates/{name}/render`

Applies template `name` with `params` (forwarded as keyword arguments to
the template's `apply()`), builds the timeline, and submits it for
background rendering.

Request body:

```json
{
  "resolution": [1080, 1920],
  "fps": 30,
  "filename": "quote_001",
  "params": {
    "background_clip": "assets/clips/a.mp4",
    "quote_text": "Be water, my friend.",
    "music": "assets/music/bg.mp3"
  }
}
```

- `resolution`, `fps` — default to `[1080, 1920]` and `30` if omitted.
- `filename` — base name (no extension) for the output `.mp4`. Defaults to
  the job id if omitted.
- `params.style`, if present, is a `TextStyle`-shaped object (same shape
  used in a `Script` spec's `texts[].style` — see §3.4) and is converted to
  a domain `TextStyle` before being passed to the template.
- `params.subtitle_source` is **not** supported over HTTP (it's a Python
  object, not JSON-representable) — templates that accept it fall back to
  their own default (`HybridSubtitleSource`) when `voice_audio` is given.

```bash
curl -X POST http://127.0.0.1:8000/templates/faceless_quote/render \
  -H "Content-Type: application/json" \
  -d '{
        "resolution": [1080, 1920],
        "fps": 30,
        "filename": "quote_001",
        "params": {
          "background_clip": "assets/clips/a.mp4",
          "quote_text": "Be water, my friend.",
          "music": "assets/music/bg.mp3"
        }
      }'
```

Response — `202 Accepted`:

```json
{"id": "3f8e...", "status": "pending", "error": null, "download_url": "/jobs/3f8e.../file"}
```

Errors: `404` if `name` isn't a registered template; `422` if `params` is
missing a required parameter or the template raises during `apply()`.

### 3.4 `/edit/*` — single-purpose editing operations

For the common case of "just do one thing to one video" — no need to
assemble a `Script`/`Template`. Each of these still renders in the
background the same as every other endpoint (see the note at the top of
this document); the difference is only in how much you have to describe
up front.

#### `POST /edit/concat` — join clips end to end

```bash
curl -X POST http://127.0.0.1:8000/edit/concat \
  -H "Content-Type: application/json" \
  -d '{
        "resolution": [1080, 1920], "fps": 30, "filename": "merged",
        "clips": [
          {"path": "assets/clips/a.mp4"},
          {"path": "assets/clips/b.mp4", "transition_in": {"type": "dissolve", "duration": 0.5}}
        ]
      }'
```

`clips` is a list of `{path, trim_start=0, trim_end=null, transition_in=null}`,
joined in the order given. `trim_start`/`trim_end` cut each source clip
before it's joined (see `/edit/trim` below for the same fields alone).
`transition_in` (`{"type": "cut" | "fade" | "dissolve", "duration": ...}`)
applies between this clip and the previous one; ignored on the first clip.

#### `POST /edit/trim` — extract a segment from one video

```bash
curl -X POST http://127.0.0.1:8000/edit/trim \
  -H "Content-Type: application/json" \
  -d '{"path": "assets/clips/a.mp4", "trim_start": 2.0, "trim_end": 8.0, "filename": "clip_2_to_8"}'
```

Extracts `[trim_start, trim_end)` seconds from `path` as a standalone
video. Omit `trim_end` to cut from `trim_start` to the source's natural
end.

#### `POST /edit/add-audio` — background music/audio

```bash
curl -X POST http://127.0.0.1:8000/edit/add-audio \
  -H "Content-Type: application/json" \
  -d '{
        "video_path": "assets/clips/a.mp4", "audio_path": "assets/music/bg.mp3",
        "volume": 0.3, "fade_in": 0, "fade_out": 2, "filename": "with_music"
      }'
```

Mixes `audio_path` into `video_path` at `volume`. The video's own
original audio, if it has any, is kept and mixed together with it — not
replaced.

#### `POST /edit/overlay-text` — burn in a text overlay

```bash
curl -X POST http://127.0.0.1:8000/edit/overlay-text \
  -H "Content-Type: application/json" \
  -d '{
        "video_path": "assets/clips/a.mp4", "text": "Hello!",
        "start": 0, "end": 3, "position": {"preset": "center"},
        "style": {"font_size": 64, "color": "white"}
      }'
```

`position`/`style`/`animation` use the same shapes as a `Script` spec's
`texts[]` entry (see [SPEC.md §10](SPEC.md#10-script--declarative-spec-layer-3)).
Omit `end` to show the text until the video ends.

#### `POST /edit/overlay-image` — burn in an image/watermark

```bash
curl -X POST http://127.0.0.1:8000/edit/overlay-image \
  -H "Content-Type: application/json" \
  -d '{
        "video_path": "assets/clips/a.mp4", "image_path": "assets/logo.png",
        "start": 0, "end": null, "position": {"preset": "top-right"}
      }'
```

`position` is required (no default) — same `PositionSpec` shape as above.
Omit `end` (or pass `null`) for a watermark shown for the whole video.

#### `POST /edit/captions` — burn in captions

```bash
curl -X POST http://127.0.0.1:8000/edit/captions \
  -H "Content-Type: application/json" \
  -d '{
        "video_path": "assets/clips/a.mp4",
        "captions": {"source": "file", "path": "captions.srt", "voice_audio": "unused-for-file-source.mp3"}
      }'
```

`captions` uses the same `source: "file" | "whisper" | "hybrid"` shape as
a `Script` spec's `captions` field — see
[SPEC.md §10](SPEC.md#10-script--declarative-spec-layer-3) for the full
field reference per source.

All six endpoints share `resolution` (default `[1080, 1920]`), `fps`
(default `30`), and `filename` fields, and return the same `202` job
response as §3.3. Errors: `422` for a missing/invalid field, or a
domain-level rejection (e.g. `/edit/concat` needs at least one clip).

### 3.5 `POST /renders`

Submits a `Script`-shaped JSON body (identical shape to a spec file under
`input/specs/`, plus an optional `filename`) for background rendering.
See [SPEC.md §10](SPEC.md#10-script--declarative-spec-layer-3) for the full
spec field reference (clips/texts/images/audio/captions).

```bash
curl -X POST http://127.0.0.1:8000/renders \
  -H "Content-Type: application/json" \
  -d '{
        "resolution": [1080, 1920],
        "fps": 30,
        "filename": "video_001",
        "clips": [{"path": "assets/clips/a.mp4", "start": 0}],
        "texts": [{"text": "Hello!", "start": 0, "end": 3,
                    "position": {"preset": "center"}}],
        "audio": [{"path": "assets/music/bg.mp3", "volume": 0.3}]
      }'
```

Response — `202 Accepted`, same shape as §3.3.

Errors: `422` if the body fails spec validation (unknown field, missing
required field, wrong type — same rules `Script.parse()` applies to a spec
file) or fails a domain-level rule (e.g. two tracks with conflicting
types).

### 3.6 `GET /jobs/{job_id}`

```bash
curl http://127.0.0.1:8000/jobs/3f8e...
```

```json
{"id": "3f8e...", "status": "running", "error": null, "download_url": null}
```

`status` is one of `pending` / `running` / `succeeded` / `failed`.
`download_url` is only populated once `status` is `succeeded`. If a job
failed, `error` holds the exception message.

Errors: `404` if `job_id` is unknown.

### 3.7 `GET /jobs/{job_id}/file`

Downloads the rendered `.mp4` once the job has succeeded.

```bash
curl -OJ http://127.0.0.1:8000/jobs/3f8e.../file
```

Errors: `404` if `job_id` is unknown; `409` if the job hasn't finished yet
(still `pending`/`running`) or failed.

## 4. Typical client flow

```python
import time
import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000")

# Same flow for every job-returning endpoint — swap the URL/body for
# /edit/concat, /edit/add-audio, /templates/{name}/render, etc.
response = client.post("/renders", json={
    "resolution": [1080, 1920],
    "fps": 30,
    "clips": [{"path": "assets/clips/a.mp4", "start": 0}],
})
job_id = response.json()["id"]

while True:
    job = client.get(f"/jobs/{job_id}").json()
    if job["status"] in ("succeeded", "failed"):
        break
    time.sleep(1)

if job["status"] == "succeeded":
    video_bytes = client.get(job["download_url"]).content
else:
    raise RuntimeError(job["error"])
```

## 5. Notes & limitations (v1)

- Jobs are kept **in memory** — they don't survive a server restart, and
  don't scale past a single process. There's no persistence layer or
  external queue (Redis/Celery/etc.) in v1.
- No authentication, rate limiting, or multi-tenant isolation.
- Templates are the only Layer-3 construct exposed with structured
  discovery (`GET /templates`); a `Script` body is validated the same way
  a spec file is, but there's no `GET /renders` listing endpoint — track
  a render by the `job_id` returned from `POST /renders`.
