from pathlib import Path

from fastapi.testclient import TestClient

from vidgen.api import create_app
from vidgen.domain.timeline import Timeline
from vidgen.strategies.render.base import RenderStrategy


class RecordingStubRenderStrategy(RenderStrategy):
    """Writes an empty file and records the Timeline it was given, so tests
    can assert on the built Timeline's shape without a real render."""

    def __init__(self) -> None:
        self.rendered: list[Timeline] = []

    def render(self, timeline: Timeline, output_path: str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-video-bytes")
        self.rendered.append(timeline)
        return path


def _make_client(tmp_path, strategy: RecordingStubRenderStrategy) -> TestClient:
    app = create_app(output_dir=str(tmp_path / "output"), render_strategy=strategy)
    return TestClient(app)


def _wait_for_job(client: TestClient, job_id: str, timeout: float = 5.0) -> dict:
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get(f"/jobs/{job_id}").json()
        if body["status"] in ("succeeded", "failed"):
            return body
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not finish within {timeout}s")


def test_concat_joins_clips_sequentially_with_only_last_open_ended(tmp_path):
    strategy = RecordingStubRenderStrategy()
    client = _make_client(tmp_path, strategy)

    response = client.post(
        "/edit/concat",
        json={
            "resolution": [320, 240],
            "fps": 24,
            "filename": "merged",
            "clips": [
                {"path": "assets/clips/a.mp4"},
                {"path": "assets/clips/b.mp4", "trim_start": 1.0},
            ],
        },
    )
    assert response.status_code == 202
    finished = _wait_for_job(client, response.json()["id"])
    assert finished["status"] == "succeeded"
    assert (tmp_path / "output" / "merged.mp4").exists()

    timeline = strategy.rendered[0]
    clips = sorted(timeline.tracks["main"].items(), key=lambda c: c.start)
    assert [c.asset.path for c in clips] == ["assets/clips/a.mp4", "assets/clips/b.mp4"]
    assert clips[0].end is not None
    assert clips[1].end is None
    assert clips[1].trim_in == 1.0


def test_concat_requires_at_least_one_clip(tmp_path):
    strategy = RecordingStubRenderStrategy()
    client = _make_client(tmp_path, strategy)

    response = client.post("/edit/concat", json={"clips": []})
    assert response.status_code == 422


def test_trim_extracts_a_segment(tmp_path):
    strategy = RecordingStubRenderStrategy()
    client = _make_client(tmp_path, strategy)

    response = client.post(
        "/edit/trim",
        json={"path": "assets/clips/a.mp4", "trim_start": 2.0, "trim_end": 5.0, "filename": "clip"},
    )
    assert response.status_code == 202
    finished = _wait_for_job(client, response.json()["id"])
    assert finished["status"] == "succeeded"

    timeline = strategy.rendered[0]
    (clip,) = timeline.tracks["main"].items()
    assert clip.trim_in == 2.0
    assert clip.trim_out == 5.0


def test_add_audio_mixes_music_into_video(tmp_path):
    strategy = RecordingStubRenderStrategy()
    client = _make_client(tmp_path, strategy)

    response = client.post(
        "/edit/add-audio",
        json={
            "video_path": "assets/clips/a.mp4",
            "audio_path": "assets/music/bg.mp3",
            "volume": 0.3,
            "filename": "with_music",
        },
    )
    assert response.status_code == 202
    finished = _wait_for_job(client, response.json()["id"])
    assert finished["status"] == "succeeded"

    timeline = strategy.rendered[0]
    (audio_layer,) = timeline.tracks["audio"].items()
    assert audio_layer.asset.path == "assets/music/bg.mp3"
    assert audio_layer.volume == 0.3


def test_overlay_text_burns_text_onto_video(tmp_path):
    strategy = RecordingStubRenderStrategy()
    client = _make_client(tmp_path, strategy)

    response = client.post(
        "/edit/overlay-text",
        json={
            "video_path": "assets/clips/a.mp4",
            "text": "Hello!",
            "start": 0,
            "end": 3,
            "position": {"preset": "center"},
        },
    )
    assert response.status_code == 202
    finished = _wait_for_job(client, response.json()["id"])
    assert finished["status"] == "succeeded"

    timeline = strategy.rendered[0]
    (overlay,) = timeline.tracks["overlay"].items()
    assert overlay.text == "Hello!"


def test_overlay_image_burns_watermark_onto_video(tmp_path):
    strategy = RecordingStubRenderStrategy()
    client = _make_client(tmp_path, strategy)

    response = client.post(
        "/edit/overlay-image",
        json={
            "video_path": "assets/clips/a.mp4",
            "image_path": "assets/logo.png",
            "start": 0,
            "end": 5,
            "position": {"preset": "top-right"},
        },
    )
    assert response.status_code == 202
    finished = _wait_for_job(client, response.json()["id"])
    assert finished["status"] == "succeeded"

    timeline = strategy.rendered[0]
    (overlay,) = timeline.tracks["overlay"].items()
    assert overlay.asset.path == "assets/logo.png"


def test_overlay_image_missing_position_returns_422(tmp_path):
    strategy = RecordingStubRenderStrategy()
    client = _make_client(tmp_path, strategy)

    response = client.post(
        "/edit/overlay-image",
        json={"video_path": "assets/clips/a.mp4", "image_path": "assets/logo.png"},
    )
    assert response.status_code == 422


def test_captions_with_file_source_burns_captions_onto_video(tmp_path):
    srt_path = tmp_path / "captions.srt"
    srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello!\n",
        encoding="utf-8",
    )
    strategy = RecordingStubRenderStrategy()
    client = _make_client(tmp_path, strategy)

    response = client.post(
        "/edit/captions",
        json={
            "video_path": "assets/clips/a.mp4",
            "captions": {"source": "file", "voice_audio": "assets/voice/x.mp3", "path": str(srt_path)},
        },
    )
    assert response.status_code == 202
    finished = _wait_for_job(client, response.json()["id"])
    assert finished["status"] == "succeeded"

    timeline = strategy.rendered[0]
    (caption,) = timeline.tracks["captions"].items()
    assert caption.text == "Hello!"
