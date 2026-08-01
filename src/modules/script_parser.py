import json
from pathlib import Path
from src.models import ScriptInput

class ScriptParser:
    @staticmethod
    def parse(file_path: str | Path) -> ScriptInput:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Script file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return ScriptInput(
            title=data.get('title', ''),
            subtitle=data.get('subtitle', ''),
            ending_text=data.get('ending_text', ''),
            theme=data.get('theme', 'default'),
            segments=data.get('segments', []),
            voice=data.get('voice', 'zh-CN-YunxiNeural'),
            target_duration=data.get('target_duration', 35)
        )

def test_script_parser():
    # Test with a sample script JSON
    sample_script = {
        "title": "Sample Video",
        "subtitle": "This is a sample subtitle.",
        "ending_text": "Thank you for watching!",
        "theme": "nature",
        "segments": [
            {"text": "Hello, world!", "duration": 5},
            {"text": "This is a test.", "duration": 10}
        ],
        "voice": "en-US-JennyNeural",
        "target_duration": 20
    }
    
    # Write to a temporary file
    temp_path = Path("temp_script.json")
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(sample_script, f)
    
    # Parse the script
    parser = ScriptParser()
    parsed_script = parser.parse(temp_path)
    
    # Clean up
    temp_path.unlink()
    print("Parsed Script:", parsed_script)
    print("ScriptParser test passed.")

if __name__ == "__main__":
    test_script_parser()