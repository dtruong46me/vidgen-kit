import os
import json
from pathlib import Path
from moviepy import VideoFileClip

base_dir = Path(__file__).parent.resolve()

# 1. Delete dummy files
dummy_bg = base_dir / "assets/music/dummy_bg.mp3"
if dummy_bg.exists():
    dummy_bg.unlink()

for f in (base_dir / "assets/clips/zen").glob("dummy_clip_*.mp4"):
    f.unlink()

# 2. Build clips.json from grok-video files
clips_dir = base_dir / "assets/clips"
clips_data = {"clips": []}

for i, video_file in enumerate(clips_dir.glob("grok-video-*.mp4")):
    try:
        # get duration
        clip = VideoFileClip(str(video_file))
        duration = clip.duration
        clip.close()
        
        clips_data["clips"].append({
            "id": f"grok_{i}",
            "path": f"assets/clips/{video_file.name}",
            "tags": ["zen", "grok"],
            "duration": duration,
            "theme": "zen" # Set them to zen so they get picked up
        })
    except Exception as e:
        print(f"Failed to read {video_file}: {e}")

with open(base_dir / "assets/metadata/clips.json", "w", encoding="utf-8") as f:
    json.dump(clips_data, f, indent=4)

# 3. Restore example.json
example_data = {
    "title": "Zen Moments",
    "subtitle": "Relax and enjoy",
    "ending_text": "Stay calm",
    "theme": "zen",
    "voice": "zh-CN-YunxiNeural",
    "target_duration": 30,
    "segments": [
        {
            "voice_text": "当你看清了一个人而不揭穿，你就懂得了格局的意义。",
            "subtitle_text": "当你看清了一个人而不揭穿\n(Khi bạn nhìn rõ một người mà không vạch trần)"
        },
        {
            "voice_text": "当你讨厌一个人而不翻脸，你就明白了释然的重要性。",
            "subtitle_text": "当你讨厌一个人而不翻脸\n(Khi bạn ghét một người mà không trở mặt)"
        },
        {
            "voice_text": "茶不过两个姿态，沉浮；饮茶人不过两个动作，拿起，放下。",
            "subtitle_text": "茶不过两个姿态，沉浮\n(Trà chỉ có hai trạng thái: chìm và nổi, người uống trà cũng chỉ có hai động tác: cầm lên và đặt xuống)"
        }
    ]
}
with open(base_dir / "input/scripts/example.json", "w", encoding="utf-8") as f:
    json.dump(example_data, f, ensure_ascii=False, indent=4)
