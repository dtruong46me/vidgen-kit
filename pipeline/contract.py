"""
Ghi `content/<slug>.build.json` — HỢP ĐỒNG giữa Python và React.

File này là ranh giới. Mọi thứ bên trái nó là Python, mọi thứ bên phải là
Remotion, và hai bên chỉ biết nhau qua hình dạng JSON dựng ở đây.

P-3 sống ở module này: thêm tính năng = thêm một trường có giá trị mặc định.
Đừng đổi tên trường cũ, đừng bỏ trường cũ — Remotion bản cũ phải render được
build.json bản mới. Thêm trường xong thì khai báo nó trong studio/src/types.ts,
ở một commit khác.
"""

from __future__ import annotations

import json
from pathlib import Path

from .assets import SceneClip, Soundtrack
from .script import Script
from .timeline import Timeline
from .tts import Voiceover

#: Đổi số này khi hình dạng hợp đồng đổi theo kiểu Remotion cũ không đọc nổi.
#: Thêm trường có mặc định thì KHÔNG phải đổi.
VERSION = 1


def compose(
    script: Script,
    voices: list[Voiceover],
    clips: list[SceneClip],
    bgm: Soundtrack,
    timeline: Timeline,
) -> dict:
    """Ghép bốn nguồn lại thành đúng hình dạng Remotion đang chờ."""
    return {
        "id": script.slug,
        "title": script.title,
        "fps": script.fps,
        "width": script.width,
        "height": script.height,
        "bgm": bgm.path,
        "bgmDurationInFrames": timeline.bgm_duration_in_frames,
        "bgmVolume": script.bgm_volume,
        "lines": [
            {
                "ja": line.ja,
                "romaji": line.romaji,
                "vi": line.vi,
                "audio": voice.rel_path,
                "audioDurationInFrames": scene.audio_duration_in_frames,
                "durationInFrames": scene.duration_in_frames,
                "audioStartInFrames": scene.audio_start_in_frames,
                "clip": clip.path,
                "clipDurationInFrames": scene.clip_duration_in_frames,
                "clipStartInSeconds": clip.start_seconds,
            }
            for line, voice, clip, scene in zip(
                script.lines, voices, clips, timeline.scenes
            )
        ],
    }


def write(build: dict, dest: Path) -> Path:
    """Ghi ra đĩa, thụt lề 2 và giữ nguyên chữ Nhật (P-4: mở ra đọc được bằng mắt)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(build, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return dest
