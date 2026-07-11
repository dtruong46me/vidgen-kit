import os
import json
import logging
from pathlib import Path

base_dir = Path(__file__).parent.resolve()

def create_dummy_data():
    print("Setting up dummy data...")
    # Create directories
    (base_dir / "assets/clips/zen").mkdir(parents=True, exist_ok=True)
    (base_dir / "assets/music").mkdir(parents=True, exist_ok=True)
    (base_dir / "assets/fonts").mkdir(parents=True, exist_ok=True)
    (base_dir / "assets/metadata").mkdir(parents=True, exist_ok=True)
    (base_dir / "input/scripts").mkdir(parents=True, exist_ok=True)

    from moviepy import ColorClip
    # Create 2 dummy video clips with different colors to test crossfade
    clip1_path = base_dir / "assets/clips/zen/dummy_clip_green.mp4"
    if not clip1_path.exists():
        clip1 = ColorClip(size=(1080, 1920), color=(0, 255, 0), duration=5)
        clip1.write_videofile(str(clip1_path), fps=30, codec="libx264")
        
    clip2_path = base_dir / "assets/clips/zen/dummy_clip_blue.mp4"
    if not clip2_path.exists():
        clip2 = ColorClip(size=(1080, 1920), color=(0, 0, 255), duration=5)
        clip2.write_videofile(str(clip2_path), fps=30, codec="libx264")

    # Create dummy bg music (just a silent or tone clip using moviepy)
    bg_music_path = base_dir / "assets/music/dummy_bg.mp3"
    if not bg_music_path.exists():
        # Create a 5s blank audio
        from moviepy import AudioArrayClip
        import numpy as np
        # 44100 Hz, 2 channels, 5 seconds
        blank_audio = AudioArrayClip(np.zeros((44100 * 5, 2)), fps=44100)
        blank_audio.write_audiofile(str(bg_music_path), fps=44100)

    # Create clips.json
    clips_json = base_dir / "assets/metadata/clips.json"
    clips_data = {
        "clips": [
            {
                "id": "zen_green",
                "path": "assets/clips/zen/dummy_clip_green.mp4",
                "tags": ["zen", "green"],
                "duration": 5.0,
                "theme": "zen"
            },
            {
                "id": "zen_blue",
                "path": "assets/clips/zen/dummy_clip_blue.mp4",
                "tags": ["zen", "blue"],
                "duration": 5.0,
                "theme": "zen"
            }
        ]
    }
    with open(clips_json, "w", encoding="utf-8") as f:
        json.dump(clips_data, f)
    print("Created clips.json")

    # Create example.json with bilingual text
    example_json = base_dir / "input/scripts/example.json"
    example_data = {
        "title": "Zen Moments",
        "subtitle": "Relax and enjoy",
        "ending_text": "Stay calm",
        "theme": "zen",
        "voice": "zh-CN-YunxiNeural",
        "target_duration": 10,
        "segments": [
            {
                "voice_text": "当你看清了一个人而不揭穿，你就懂得了格局的意义。",
                "subtitle_text": "当你看清了一个人而不揭穿\n(Khi bạn nhìn rõ một người mà không vạch trần)"
            },
            {
                "voice_text": "当你讨厌一个人而不翻脸，你就明白了释然的重要性。",
                "subtitle_text": "当你讨厌一个人而不翻脸\n(Khi bạn ghét một người mà không trở mặt)"
            }
        ]
    }
    with open(example_json, "w", encoding="utf-8") as f:
        json.dump(example_data, f)
    print("Created bilingual example.json")

def test_pipeline():
    print("Running pipeline...")
    from src.pipeline.faceless_pipeline import FacelessPipeline
    pipeline = FacelessPipeline()
    pipeline.run(str(base_dir / "input/scripts/example.json"))
    print("Pipeline completed successfully! Check the output directory.")

if __name__ == "__main__":
    try:
        create_dummy_data()
        test_pipeline()
    except Exception as e:
        print(f"Error occurred: {e}")
