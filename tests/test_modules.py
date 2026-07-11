import pytest
from unittest.mock import patch, MagicMock
from src.modules.script_parser import ScriptParser
from src.modules.asset_loader import AssetLoader
from src.models import ClipMetadata

@patch('src.modules.script_parser.Path.exists')
@patch('builtins.open')
@patch('json.load')
def test_script_parser(mock_json_load, mock_open, mock_exists):
    mock_exists.return_value = True
    mock_json_load.return_value = {
        "title": "Test Title",
        "segments": ["Seg 1", "Seg 2"]
    }
    
    script = ScriptParser.parse("dummy.json")
    
    assert script.title == "Test Title"
    assert len(script.segments) == 2

@patch('src.modules.asset_loader.CLIPS_JSON_PATH.exists')
@patch('builtins.open')
@patch('json.load')
def test_asset_loader(mock_json_load, mock_open, mock_exists):
    mock_exists.return_value = True
    mock_json_load.return_value = {
        "clips": [
            {
                "id": "clip_1",
                "path": "path/to/clip.mp4",
                "duration": 5.0,
                "theme": "zen"
            }
        ]
    }
    
    loader = AssetLoader()
    clip = loader.get_random_clip_by_theme("zen")
    
    assert clip is not None
    assert clip.id == "clip_1"
