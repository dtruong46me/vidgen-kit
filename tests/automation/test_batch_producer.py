import json
import logging
from pathlib import Path

from vidgen.automation.batch_producer import BatchProducer, BatchResult
from vidgen.domain.timeline import Timeline
from vidgen.strategies.render.base import RenderStrategy


class StubRenderStrategy(RenderStrategy):
    """A fake RenderStrategy that just touches the output file.

    Stands in for MoviePyRenderStrategy so these tests don't need real
    video assets or ffmpeg — only that BatchProducer wires Script ->
    RenderStrategy correctly.
    """

    def __init__(self):
        self.rendered: list[tuple[Timeline, str]] = []

    def render(self, timeline: Timeline, output_path: str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
        self.rendered.append((timeline, output_path))
        return path


def _valid_spec_dict() -> dict:
    return {
        "resolution": [320, 240],
        "fps": 24,
        "clips": [{"path": "assets/clips/a.mp4", "start": 0, "end": 5}],
    }


def _write_json_spec(directory: Path, name: str, data: dict) -> Path:
    path = directory / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_run_produces_output_file_per_valid_spec(tmp_path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    _write_json_spec(spec_dir, "one.json", _valid_spec_dict())
    _write_json_spec(spec_dir, "two.json", _valid_spec_dict())
    output_dir = tmp_path / "output"
    strategy = StubRenderStrategy()

    result = BatchProducer(str(spec_dir), render_strategy=strategy).run(str(output_dir))

    assert isinstance(result, BatchResult)
    assert result.failed == []
    assert sorted(p.name for p in result.succeeded) == ["one.mp4", "two.mp4"]
    assert (output_dir / "one.mp4").exists()
    assert (output_dir / "two.mp4").exists()
    assert len(strategy.rendered) == 2


def test_run_continues_past_a_broken_spec_and_logs_it(tmp_path, caplog):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    _write_json_spec(spec_dir, "good.json", _valid_spec_dict())
    _write_json_spec(spec_dir, "broken.json", {"resolution": [320, 240], "bogus_field": 1})
    output_dir = tmp_path / "output"
    strategy = StubRenderStrategy()

    with caplog.at_level(logging.ERROR, logger="vidgen.automation"):
        result = BatchProducer(str(spec_dir), render_strategy=strategy).run(str(output_dir))

    assert [p.name for p in result.succeeded] == ["good.mp4"]
    assert (output_dir / "good.mp4").exists()
    assert not (output_dir / "broken.mp4").exists()

    assert len(result.failed) == 1
    failed_path, failed_exc = result.failed[0]
    assert failed_path.name == "broken.json"
    assert isinstance(failed_exc, Exception)
    assert "broken.json" in caplog.text
