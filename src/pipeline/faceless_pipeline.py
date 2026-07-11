from src.modules.script_parser import ScriptParser
from src.modules.voice_generator import VoiceGenerator
from src.modules.asset_loader import AssetLoader
from src.modules.timeline_builder import TimelineBuilder
from src.modules.subtitle_generator import SubtitleGenerator
from src.modules.video_composer import VideoComposer
from src.modules.thumbnail_generator import ThumbnailGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FacelessPipeline:
    def __init__(self):
        self.script_parser = ScriptParser()
        self.voice_generator = VoiceGenerator()
        self.asset_loader = AssetLoader()
        self.timeline_builder = TimelineBuilder(self.asset_loader)
        self.subtitle_generator = SubtitleGenerator()
        self.video_composer = VideoComposer()
        self.thumbnail_generator = ThumbnailGenerator()
        
    def run(self, script_path: str):
        logger.info(f"Starting pipeline for script: {script_path}")
        
        # 1. Parse Script
        script = self.script_parser.parse(script_path)
        logger.info(f"Parsed script: {script.title}")
        
        # 2. Generate Voices
        logger.info("Generating voices...")
        segments = self.voice_generator.generate_voices(script)
        
        # 3. Build Timeline
        logger.info("Building timeline...")
        timeline = self.timeline_builder.build_timeline(segments, script.theme)
        
        # 4. Generate Subtitles
        logger.info("Generating subtitles...")
        subtitle_path = self.subtitle_generator.generate_subtitles(segments)
        
        # 5. Compose Video
        logger.info("Composing video...")
        video_filename = f"{script.title.replace(' ', '_')}.mp4"
        video_path = self.video_composer.compose(timeline, subtitle_path, video_filename)
        
        # 6. Generate Thumbnail
        logger.info("Generating thumbnail...")
        thumb_filename = f"{script.title.replace(' ', '_')}_thumb.jpg"
        thumb_path = self.thumbnail_generator.generate(video_path, script.title, script.subtitle, thumb_filename)
        
        logger.info(f"Pipeline completed successfully!")
        logger.info(f"Video: {video_path}")
        logger.info(f"Thumbnail: {thumb_path}")
