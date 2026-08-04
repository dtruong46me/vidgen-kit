import threading
import time
from pathlib import Path

from fastapi.testclient import TestClient

from vidgen.api import create_app
from vidgen.domain.timeline import Timeline
from vidgen.strategies.render.base import RenderStrategy


class StubRenderStrategy(RenderStrategy):
    """Writes an empty file instead of really rendering, so these tests
    don't need real video assets, ffmpeg, or to wait on a real render."""

    def render(self, timeline: Timeline, output_path: str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-video-bytes")
        return path


class BlockingStubRenderStrategy(RenderStrategy):
    """Like StubRenderStrategy, but blocks until ``release`` is set — lets
    a test observe a job in the 'running' state before it finishes."""

    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()

    def render(self, timeline: Timeline, output_path: str) -> Path:
        self.started.set()
        self.release.wait(timeout=5)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-video-bytes")
        return path


def _make_client(tmp_path, render_strategy=None) -> TestClient:
    app = create_app(
        output_dir=str(tmp_path / "output"),
        render_strategy=render_strategy or StubRenderStrategy(),
    )
    return TestClient(app)


def _wait_for_job(client: TestClient, job_id: str, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get(f"/jobs/{job_id}").json()
        if body["status"] in ("succeeded", "failed"):
            return body
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not finish within {timeout}s")


def _valid_script_body() -> dict:
    return {
        "resolution": [320, 240],
        "fps": 24,
        "clips": [{"path": "assets/clips/a.mp4", "start": 0, "end": 5}],
    }


def test_health(tmp_path):
    client = _make_client(tmp_path)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_templates_includes_faceless_quote(tmp_path):
    client = _make_client(tmp_path)
    response = client.get("/templates")
    assert response.status_code == 200
    templates = {t["name"]: t for t in response.json()}
    assert "faceless_quote" in templates
    param_names = {p["name"] for p in templates["faceless_quote"]["params"]}
    assert {"background_clip", "quote_text", "music", "voice_audio", "style"} <= param_names
    required = {p["name"] for p in templates["faceless_quote"]["params"] if p["required"]}
    assert required == {"background_clip", "quote_text", "music"}


def test_render_template_runs_job_to_completion_and_downloads(tmp_path):
    client = _make_client(tmp_path)
    response = client.post(
        "/templates/faceless_quote/render",
        json={
            "resolution": [320, 240],
            "fps": 24,
            "filename": "quote",
            "params": {
                "background_clip": "assets/clips/a.mp4",
                "quote_text": "Be water, my friend.",
                "music": "assets/music/bg.mp3",
            },
        },
    )
    assert response.status_code == 202
    job_id = response.json()["id"]

    finished = _wait_for_job(client, job_id)
    assert finished["status"] == "succeeded"
    assert finished["download_url"] == f"/jobs/{job_id}/file"

    downloaded = client.get(finished["download_url"])
    assert downloaded.status_code == 200
    assert downloaded.content == b"fake-video-bytes"
    assert (tmp_path / "output" / "quote.mp4").exists()


def test_render_template_unknown_name_returns_404(tmp_path):
    client = _make_client(tmp_path)
    response = client.post(
        "/templates/does_not_exist/render",
        json={"params": {}},
    )
    assert response.status_code == 404


def test_render_template_missing_required_param_returns_422(tmp_path):
    client = _make_client(tmp_path)
    response = client.post(
        "/templates/faceless_quote/render",
        json={"params": {"quote_text": "missing the rest"}},
    )
    assert response.status_code == 422


def test_create_render_runs_job_to_completion_and_downloads(tmp_path):
    client = _make_client(tmp_path)
    response = client.post("/renders", json={**_valid_script_body(), "filename": "clip"})
    assert response.status_code == 202
    job_id = response.json()["id"]

    finished = _wait_for_job(client, job_id)
    assert finished["status"] == "succeeded"

    downloaded = client.get(finished["download_url"])
    assert downloaded.status_code == 200
    assert (tmp_path / "output" / "clip.mp4").exists()


def test_create_render_invalid_body_returns_422(tmp_path):
    client = _make_client(tmp_path)
    response = client.post("/renders", json={"resolution": [320, 240], "bogus_field": 1})
    assert response.status_code == 422


def test_get_unknown_job_returns_404(tmp_path):
    client = _make_client(tmp_path)
    response = client.get("/jobs/does-not-exist")
    assert response.status_code == 404


def test_download_before_job_finishes_returns_409(tmp_path):
    strategy = BlockingStubRenderStrategy()
    client = _make_client(tmp_path, render_strategy=strategy)

    response = client.post("/renders", json=_valid_script_body())
    job_id = response.json()["id"]

    assert strategy.started.wait(timeout=5)
    download_response = client.get(f"/jobs/{job_id}/file")
    assert download_response.status_code == 409

    strategy.release.set()
    finished = _wait_for_job(client, job_id)
    assert finished["status"] == "succeeded"
