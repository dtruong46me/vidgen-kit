import pytest
from src.models import ScriptInput, TimedSegment, TimelineItem

def test_script_input_creation():
    script = ScriptInput(
        title="Test",
        subtitle="Sub",
        ending_text="End",
        theme="zen",
        segments=["Hello"]
    )
    assert script.title == "Test"
    assert script.voice == "zh-CN-YunxiNeural"
    assert script.target_duration == 35

def test_timed_segment_creation():
    segment = TimedSegment(
        segment_id=0,
        text="Hello",
        audio_path="test.mp3",
        duration=2.0,
        start_time=0.0,
        end_time=2.0
    )
    assert segment.duration == 2.0

def test_timeline_item_creation():
    segment = TimedSegment(
        segment_id=0,
        text="Hello",
        audio_path="test.mp3",
        duration=2.0,
        start_time=0.0,
        end_time=2.0
    )
    item = TimelineItem(
        segment_info=segment,
        clip_path="clip.mp4",
        clip_trim_start=0.0,
        clip_trim_end=2.0
    )
    assert item.transition == "crossfade"
