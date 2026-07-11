import asyncio
import edge_tts
from pathlib import Path
from typing import List
from mutagen.mp3 import MP3
from src.models import ScriptInput, TimedSegment
from src.config import VOICES_DIR

class VoiceGenerator:
    def __init__(self):
        VOICES_DIR.mkdir(parents=True, exist_ok=True)
        
    async def _generate_audio(self, text: str, voice: str, output_path: Path):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        
    def generate_voices(self, script: ScriptInput) -> List[TimedSegment]:
        segments = []
        current_start_time = 0.0
        
        for i, segment_data in enumerate(script.segments):
            if isinstance(segment_data, dict):
                read_text = segment_data.get('voice_text', '')
                sub_text = segment_data.get('subtitle_text', read_text)
            else:
                read_text = segment_data
                sub_text = segment_data

            output_filename = f"segment_{i}.mp3"
            output_path = VOICES_DIR / output_filename
            
            # Generate audio using asyncio
            # Thêm rate và pitch để giọng đọc chậm rãi và trầm ấm hơn
            communicate = edge_tts.Communicate(read_text, script.voice, rate="-15%", pitch="-10Hz")
            asyncio.run(communicate.save(str(output_path)))
            
            # Get duration using mutagen
            audio = MP3(output_path)
            duration = audio.info.length
            
            segment = TimedSegment(
                segment_id=i,
                text=read_text,
                subtitle_text=sub_text,
                audio_path=str(output_path),
                duration=duration,
                start_time=current_start_time,
                end_time=current_start_time + duration
            )
            segments.append(segment)
            current_start_time += duration
            
        return segments
