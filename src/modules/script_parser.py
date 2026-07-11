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
