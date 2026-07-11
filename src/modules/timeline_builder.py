from typing import List
from src.models import TimedSegment, TimelineItem
from src.modules.asset_loader import AssetLoader

class TimelineBuilder:
    def __init__(self, asset_loader: AssetLoader):
        self.asset_loader = asset_loader
        
    def build_timeline(self, segments: List[TimedSegment], theme: str) -> List[TimelineItem]:
        timeline = []
        
        for segment in segments:
            clip = self.asset_loader.get_random_clip_by_theme(theme)
            
            if not clip:
                raise ValueError("No video clips available to build timeline")
                
            clip_duration = clip.duration
            segment_duration = segment.duration
            
            trim_start = 0.0
            trim_end = min(clip_duration, segment_duration)
            
            item = TimelineItem(
                segment_info=segment,
                clip_path=clip.path,
                clip_trim_start=trim_start,
                clip_trim_end=trim_end,
                transition="crossfade",
                transition_duration=0.5
            )
            timeline.append(item)
            
        return timeline
