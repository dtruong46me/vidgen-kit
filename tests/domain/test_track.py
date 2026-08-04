import pytest

from vidgen.domain.asset import Asset
from vidgen.domain.clip import VideoClip
from vidgen.domain.errors import ClipOverlapError
from vidgen.domain.track import VideoTrack


def _clip(start: float, end: float | None) -> VideoClip:
    return VideoClip(start=start, end=end, asset=Asset(path="a.mp4", type="video"))


def test_several_closed_clips_then_one_open_ended_last_is_allowed():
    track = VideoTrack(name="main")
    track.add(_clip(0, 1))
    track.add(_clip(1, 2))
    track.add(_clip(2, None))

    assert [c.end for c in track.items()] == [1, 2, None]


def test_open_ended_clip_added_first_then_more_is_rejected():
    track = VideoTrack(name="main")
    track.add(_clip(0, None))

    with pytest.raises(ClipOverlapError):
        track.add(_clip(5, 10))


def test_two_open_ended_clips_are_rejected():
    track = VideoTrack(name="main")
    track.add(_clip(0, None))

    with pytest.raises(ClipOverlapError):
        track.add(_clip(5, None))
