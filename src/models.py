from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict

@dataclass
class ScriptInput:
    """Đại diện cho file kịch bản đầu vào (ví dụ: example.json)"""
    title: str
    subtitle: str
    ending_text: str
    theme: str
    segments: List[Union[str, dict]]
    voice: str = "zh-CN-YunxiNeural"
    target_duration: int = 35

@dataclass
class ClipMetadata:
    """Đại diện cho 1 video clip stock trong hệ thống"""
    id: str
    path: str
    tags: List[str]
    duration: float
    theme: str

@dataclass
class TimedSegment:
    """Kết quả sau khi chạy qua VoiceService"""
    segment_id: int
    text: str
    subtitle_text: str
    audio_path: str
    duration: float
    start_time: float
    end_time: float

@dataclass
class TimelineItem:
    """Đại diện cho 1 phân đoạn video hoàn chỉnh trên timeline"""
    segment_info: TimedSegment
    clip_path: str
    clip_trim_start: float
    clip_trim_end: float
    transition: str = "crossfade"
    transition_duration: float = 0.5
