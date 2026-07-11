import os
import random
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips
from moviepy.video.tools.subtitles import SubtitlesClip
import moviepy.video.fx as vfx
import moviepy.audio.fx as afx
from typing import List
from src.models import TimelineItem
from src.config import VIDEOS_DIR, DEFAULT_FPS, DEFAULT_FONT_NAME, DEFAULT_TRANSITION_DURATION, MUSIC_DIR

class VideoComposer:
    def __init__(self):
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        
    def compose(self, timeline: List[TimelineItem], subtitle_path: str, output_filename: str):
        video_clips = []
        
        for item in timeline:
            # Load clip
            clip = VideoFileClip(item.clip_path)
            
            # Loop if clip is shorter than segment duration, otherwise trim
            segment_duration = item.segment_info.duration
            if clip.duration < segment_duration:
                # Add loop effect
                clip = clip.with_effects([vfx.Loop(duration=segment_duration)])
            
            # Trim clip to exactly match segment duration
            clip = clip.subclipped(item.clip_trim_start, item.clip_trim_start + segment_duration)
            
            # Load audio
            audio = AudioFileClip(item.segment_info.audio_path)
            
            # Set audio to clip
            clip = clip.with_audio(audio)
            
            # Apply crossfade if needed
            if len(video_clips) > 0 and item.transition == "crossfade":
                clip = clip.with_effects([vfx.CrossFadeIn(item.transition_duration)])
                
            video_clips.append(clip)
            
        # Concatenate
        final_clip = concatenate_videoclips(video_clips, padding=-DEFAULT_TRANSITION_DURATION, method="compose")
        
        # Add background music
        music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
        if music_files:
            bg_music_path = random.choice(music_files)
            bg_audio = AudioFileClip(str(bg_music_path))
            
            # Loop bg music to match video duration
            bg_audio = bg_audio.with_effects([afx.AudioLoop(duration=final_clip.duration)])
            
            # Lower volume
            bg_audio = bg_audio.with_effects([afx.MultiplyVolume(0.1)])
            
            # Mix with original audio
            mixed_audio = CompositeAudioClip([final_clip.audio, bg_audio])
            final_clip = final_clip.with_audio(mixed_audio)
        
        # Add Subtitles
        generator = lambda txt: TextClip(text=txt, font=DEFAULT_FONT_NAME, font_size=40, color='white', bg_color='black')
        subs = SubtitlesClip(subtitle_path, make_textclip=generator)
        
        final_video = CompositeVideoClip([final_clip, subs.with_position(('center', 'bottom'))])
        
        output_path = VIDEOS_DIR / output_filename
        
        final_video.write_videofile(
            str(output_path),
            fps=DEFAULT_FPS,
            codec="libx264",
            audio_codec="aac"
        )
        
        return str(output_path)
