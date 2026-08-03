import json
from pathlib import Path

import pytest
import yaml

from vidgen.builder import TimelineBuilder
from vidgen.design.errors import ScriptValidationError
from vidgen.design.script import Script
from vidgen.domain.animation import FadeAnimation
from vidgen.domain.position import Alignment, Position
from vidgen.domain.style import TextStyle
from vidgen.domain.timeline import Timeline
from vidgen.domain.track import CaptionTrack
from vidgen.domain.transition import DissolveTransition
from vidgen.strategies.subtitle import FileSubtitleSource

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "strategies" / "fixtures"
SAMPLE_SRT = FIXTURE_DIR / "sample.srt"


def _assert_timelines_equivalent(a: Timeline, b: Timeline) -> None:
    assert a.resolution == b.resolution
    assert a.fps == b.fps
    assert set(a.tracks) == set(b.tracks)
    for name in a.tracks:
        track_a, track_b = a.tracks[name], b.tracks[name]
        assert type(track_a) is type(track_b)
        assert track_a.items() == track_b.items()
        if isinstance(track_a, CaptionTrack):
            assert track_a.style == track_b.style


def _write_json_spec(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _sample_spec_dict() -> dict:
    return {
        "resolution": [320, 240],
        "fps": 24,
        "clips": [
            {
                "path": "assets/clips/a.mp4",
                "start": 0,
                "end": 5,
                "transition_in": {"type": "dissolve", "duration": 0.5},
            }
        ],
        "texts": [
            {
                "text": "Hello!",
                "start": 0,
                "end": 3,
                "position": {"preset": "center"},
                "style": {"font_size": 64, "color": "white"},
                "animation": {"type": "fade", "duration": 0.4, "direction": "in"},
            }
        ],
        "images": [
            {
                "path": "logo.png",
                "start": 0,
                "end": 5,
                "position": {"x": 0.05, "y": 0.05, "unit": "ratio"},
            }
        ],
        "audio": [{"path": "bg.mp3", "volume": 0.3, "fade_out": 2}],
        "captions": {
            "source": "file",
            "path": str(SAMPLE_SRT),
            "voice_audio": "unused.mp3",
        },
    }


def _expected_timeline() -> Timeline:
    return (
        TimelineBuilder(resolution=(320, 240), fps=24)
        .clip("assets/clips/a.mp4", 0, 5, transition_in=DissolveTransition(duration=0.5))
        .text(
            "Hello!",
            0,
            3,
            position=Position.preset(Alignment.CENTER),
            style=TextStyle(font_size=64, color="white"),
            animation=FadeAnimation(duration=0.4, direction="in"),
        )
        .image("logo.png", 0, 5, position=Position.custom(0.05, 0.05, unit="ratio"))
        .audio("bg.mp3", volume=0.3, fade_out=2)
        .captions(FileSubtitleSource(str(SAMPLE_SRT)), voice_audio="unused.mp3")
        .build()
    )


def test_parse_json_spec_matches_equivalent_builder_calls(tmp_path):
    spec_path = _write_json_spec(tmp_path, _sample_spec_dict())

    parsed = Script(str(spec_path)).parse().build()

    _assert_timelines_equivalent(parsed, _expected_timeline())


def test_parse_yaml_spec_matches_equivalent_builder_calls(tmp_path):
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(yaml.safe_dump(_sample_spec_dict()), encoding="utf-8")

    parsed = Script(str(spec_path)).parse().build()

    _assert_timelines_equivalent(parsed, _expected_timeline())


def test_parse_returns_not_yet_built_builder_that_can_chain_further_calls(tmp_path):
    spec_path = _write_json_spec(tmp_path, {"resolution": [320, 240]})

    builder = Script(str(spec_path)).parse()
    builder.clip("extra.mp4", start=0, end=1)
    timeline = builder.build()

    assert timeline.get_track("main").items()[0].asset.path == "extra.mp4"


def test_parse_rejects_unknown_top_level_field(tmp_path):
    spec_path = _write_json_spec(tmp_path, {"resolution": [320, 240], "bogus_field": 123})

    with pytest.raises(ScriptValidationError):
        Script(str(spec_path)).parse()


def test_parse_rejects_missing_required_field_in_nested_spec(tmp_path):
    spec_path = _write_json_spec(
        tmp_path, {"resolution": [320, 240], "clips": [{"start": 0, "end": 5}]}
    )

    with pytest.raises(ScriptValidationError):
        Script(str(spec_path)).parse()


def test_parse_rejects_hybrid_captions_missing_script_text(tmp_path):
    spec_path = _write_json_spec(
        tmp_path,
        {
            "resolution": [320, 240],
            "captions": {"source": "hybrid", "voice_audio": "v.mp3"},
        },
    )

    with pytest.raises(ScriptValidationError):
        Script(str(spec_path)).parse()
