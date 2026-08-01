import json
import random
from pathlib import Path
from typing import List, Dict
from src.models import ClipMetadata
from src.config import CLIPS_JSON_PATH, BASE_DIR

class AssetLoader:
    def __init__(self):
        self.clips: List[ClipMetadata] = []
        self._load_metadata()
        
    def _load_metadata(self):
        if not CLIPS_JSON_PATH.exists():
            print(f"Warning: Clip metadata not found at {CLIPS_JSON_PATH}")
            return
            
        with open(CLIPS_JSON_PATH, 'r', encoding='utf-8') as f:
            data: dict = json.load(f)
            
        for clip_data in data.get('clips', []):
            # Resolve path relative to BASE_DIR if it's relative
            path_str = clip_data['path']
            full_path = BASE_DIR / path_str
            
            clip = ClipMetadata(
                id=clip_data['id'],
                path=str(full_path),
                tags=clip_data.get('tags', []),
                duration=clip_data['duration'],
                theme=clip_data['theme']
            )
            self.clips.append(clip)
            
    def get_random_clip_by_theme(self, theme: str) -> ClipMetadata | None:
        matching_clips = [c for c in self.clips if c.theme == theme]
        if not matching_clips:
            # Fallback to any clip if no theme matches
            matching_clips = self.clips
            
        if not matching_clips:
            return None
            
        return random.choice(matching_clips)
