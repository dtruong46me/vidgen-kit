import pytest
from unittest.mock import patch, MagicMock
from src.pipeline.faceless_pipeline import FacelessPipeline

@patch('src.pipeline.faceless_pipeline.ScriptParser')
@patch('src.pipeline.faceless_pipeline.VoiceGenerator')
@patch('src.pipeline.faceless_pipeline.AssetLoader')
@patch('src.pipeline.faceless_pipeline.TimelineBuilder')
@patch('src.pipeline.faceless_pipeline.SubtitleGenerator')
@patch('src.pipeline.faceless_pipeline.VideoComposer')
@patch('src.pipeline.faceless_pipeline.ThumbnailGenerator')
def test_pipeline_run(MockThumbnailGenerator, MockVideoComposer, MockSubtitleGenerator, MockTimelineBuilder, MockAssetLoader, MockVoiceGenerator, MockScriptParser):
    # Setup mocks
    mock_script_parser = MockScriptParser.return_value
    mock_script = MagicMock()
    mock_script.title = "Test Script"
    mock_script.theme = "zen"
    mock_script.subtitle = "Subtitle"
    mock_script_parser.parse.return_value = mock_script
    
    mock_voice_generator = MockVoiceGenerator.return_value
    mock_voice_generator.generate_voices.return_value = ["segment1", "segment2"]
    
    mock_timeline_builder = MockTimelineBuilder.return_value
    mock_timeline_builder.build_timeline.return_value = ["item1", "item2"]
    
    mock_subtitle_generator = MockSubtitleGenerator.return_value
    mock_subtitle_generator.generate_subtitles.return_value = "subtitles.srt"
    
    mock_video_composer = MockVideoComposer.return_value
    mock_video_composer.compose.return_value = "video.mp4"
    
    mock_thumbnail_generator = MockThumbnailGenerator.return_value
    mock_thumbnail_generator.generate.return_value = "thumb.jpg"
    
    # Run pipeline
    pipeline = FacelessPipeline()
    pipeline.run("dummy.json")
    
    # Assertions
    mock_script_parser.parse.assert_called_once_with("dummy.json")
    mock_voice_generator.generate_voices.assert_called_once_with(mock_script)
    mock_timeline_builder.build_timeline.assert_called_once_with(["segment1", "segment2"], "zen")
    mock_subtitle_generator.generate_subtitles.assert_called_once_with(["segment1", "segment2"])
    mock_video_composer.compose.assert_called_once_with(["item1", "item2"], "subtitles.srt", "Test_Script.mp4")
    mock_thumbnail_generator.generate.assert_called_once_with("video.mp4", "Test Script", "Subtitle", "Test_Script_thumb.jpg")
