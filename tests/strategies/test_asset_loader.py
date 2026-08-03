from pathlib import Path

import pytest

from vidgen.domain.asset import Asset
from vidgen.strategies.asset.loader import AssetLoader
from vidgen.strategies.errors import AssetResolutionError

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_VIDEO = next((REPO_ROOT / "assets" / "clips").glob("*.mp4"))
SAMPLE_AUDIO = next((REPO_ROOT / "assets" / "music").glob("*.mp3"))


def test_resolve_video_fills_duration_resolution_fps():
    asset = Asset(path=str(SAMPLE_VIDEO), type="video")

    resolved = AssetLoader().resolve(asset)

    assert resolved.duration is not None and resolved.duration > 0
    assert resolved.resolution is not None and len(resolved.resolution) == 2
    assert all(dim > 0 for dim in resolved.resolution)
    assert resolved.fps is not None and resolved.fps > 0


def test_resolve_audio_fills_duration_only():
    asset = Asset(path=str(SAMPLE_AUDIO), type="audio")

    resolved = AssetLoader().resolve(asset)

    assert resolved.duration is not None and resolved.duration > 0
    assert resolved.resolution is None
    assert resolved.fps is None


def test_resolve_does_not_mutate_input_asset():
    asset = Asset(path=str(SAMPLE_VIDEO), type="video")

    resolved = AssetLoader().resolve(asset)

    assert resolved is not asset
    assert asset.duration is None


def test_resolve_is_idempotent_for_already_resolved_asset():
    already_resolved = Asset(
        path=str(SAMPLE_VIDEO), type="video", duration=5.0, resolution=(1, 1), fps=1.0
    )

    resolved = AssetLoader().resolve(already_resolved)

    assert resolved is already_resolved


def test_resolve_missing_file_raises_asset_resolution_error():
    asset = Asset(path=str(REPO_ROOT / "assets" / "clips" / "does-not-exist.mp4"), type="video")

    with pytest.raises(AssetResolutionError):
        AssetLoader().resolve(asset)
