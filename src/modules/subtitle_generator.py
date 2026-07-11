import srt
from datetime import timedelta
from typing import List
from src.models import TimedSegment
from src.config import SUBTITLES_DIR

class SubtitleGenerator:
    def __init__(self):
        SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
        
    def generate_subtitles(self, segments: List[TimedSegment], output_filename: str = "subtitles.srt") -> str:
        subs = []
        for segment in segments:
            sub = srt.Subtitle(
                index=segment.segment_id + 1,
                start=timedelta(seconds=segment.start_time),
                end=timedelta(seconds=segment.end_time),
                content=segment.subtitle_text
            )
            subs.append(sub)
            
        srt_content = srt.compose(subs)
        output_path = SUBTITLES_DIR / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
        return str(output_path)
