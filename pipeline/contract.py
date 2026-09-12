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
from .reading import Reading
from .script import Script
from .timeline import Timeline
from .tts import Voiceover

#: Đổi số này khi hình dạng hợp đồng đổi theo kiểu Remotion cũ không đọc nổi.
#: Thêm trường có mặc định thì KHÔNG phải đổi.
VERSION = 1


def _segments(parts, readings, scene) -> list[dict] | None:
    """Các MẢNH caption của một câu. None khi câu hiện nguyên — tức đa số câu.

    Mảnh không phải cảnh: `from` tính từ đầu cảnh, và cộng lại đúng bằng độ dài
    cảnh. Remotion bản cũ không biết trường này thì hiện nguyên `ja`/`vi` như
    trước, chỉ là cỡ chữ câu đó nhỏ hơn (P-3).
    """
    if len(scene.segments) <= 1:
        return None
    return [
        {
            "ja": part.ja,
            "romaji": reading.romaji,
            "hira": reading.hira,
            "vi": part.vi,
            "fromInFrames": seg.from_in_frames,
            "durationInFrames": seg.duration_in_frames,
        }
        for part, reading, seg in zip(parts, readings, scene.segments)
    ]


def compose(
    script: Script,
    voices: list[Voiceover],
    clips: list[SceneClip],
    bgm: Soundtrack,
    timeline: Timeline,
    readings: list[Reading],
    intro=None,
    outro=None,
    post=None,
    parts=None,
    part_readings=None,
) -> dict:
    """Ghép các nguồn lại thành đúng hình dạng Remotion đang chờ."""
    parts = parts or [[] for _ in script.lines]
    part_readings = part_readings or [[] for _ in script.lines]
    return {
        "id": script.slug,
        "title": script.title,
        "fps": script.fps,
        "width": script.width,
        "height": script.height,
        "bgm": bgm.path,
        "bgmDurationInFrames": timeline.bgm_duration_in_frames,
        "bgmVolume": script.bgm_volume,
        # Bốn trường của BƯỚC 5. Cả bốn đều có mặc định "không đổi gì cả":
        # intro/outro là null, transition là crossfade 24 frame — đúng bằng
        # hằng số CROSSFADE mà DailyVideo.tsx vẫn dùng từ trước. Nhờ vậy bản
        # Remotion CŨ đọc build.json MỚI vẫn ra y hệt video cũ (P-3).
        # Màn mở đầu nền gradient đã bỏ, nên `intro` luôn là null. Giữ trường
        # chứ không xoá (P-3): Remotion cũ cộng intro.durationInFrames vào tổng,
        # null tức 0 — khớp đúng tổng của timeline.py.
        "intro": None,
        # Tiêu đề hiện đè lên cảnh 1. Remotion cũ không biết trường này thì
        # video chỉ thiếu tiêu đề, số frame vẫn đúng.
        "titleCard": (
            {"title": intro.title, "subtitle": intro.subtitle}
            if intro is not None else None
        ),
        "outro": (
            {
                "text": outro.text,
                "durationInFrames": timeline.outro_duration_in_frames,
            }
            if outro is not None else None
        ),
        "transition": script.transition,
        "transitionInFrames": timeline.transition_in_frames,
        # Trường `hira` đã có từ BƯỚC 3 nhưng chưa ai hiện nó. Đây là công tắc.
        # Mặc định tắt — xem lý do ở script.py.
        "showHira": script.show_hira,
        # Frame làm ảnh bìa, do timeline.py chọn. `make thumbnail` đọc nó;
        # Remotion không dùng, nên bản cũ bỏ qua cũng không sao.
        "thumbnailFrame": timeline.thumbnail_frame,
        # Chữ để ĐĂNG, không phải chữ để vẽ: dòng caption và bộ hashtag.
        # Remotion không đụng tới, y như `thumbnailFrame` — nhưng nó nằm đây
        # chứ không nằm riêng một file, để `make export` chỉ phải đọc MỘT file
        # và để mở build.json ra là thấy đủ một ngày (P-4).
        "post": (
            {
                "caption": post.caption,
                "text": post.text,
                "dateLabel": post.date_label,
                "hashtags": list(post.hashtags),
                # True = kịch bản chưa khai caption, máy mượn tạm câu chốt.
                "borrowed": post.borrowed,
            }
            if post is not None else None
        ),
        "lines": [
            {
                "ja": line.ja,
                "romaji": reading.romaji,
                # Trường mới ở BƯỚC 3. Remotion chưa dùng tới — theo P-3, thêm
                # trường thì bản Remotion cũ vẫn render được build.json mới.
                # BƯỚC 5 sẽ quyết có hiện dòng hiragana này hay không.
                "hira": reading.hira,
                "vi": line.vi,
                "audio": voice.rel_path,
                "audioDurationInFrames": scene.audio_duration_in_frames,
                "durationInFrames": scene.duration_in_frames,
                "audioStartInFrames": scene.audio_start_in_frames,
                # Mặc định 0 = caption vào ngay đầu cảnh, đúng hành vi cũ.
                "captionStartInFrames": scene.caption_start_in_frames,
                "clip": clip.path,
                "clipDurationInFrames": scene.clip_duration_in_frames,
                "clipStartInSeconds": clip.start_seconds,
                # Câu dài được cắt thành mấy mảnh caption nối tiếp nhau TRONG
                # CÙNG cảnh này. null = hiện nguyên câu, và đó là mặc định.
                # `ja`/`vi` bên trên vẫn là NGUYÊN câu: `make export` và
                # `make reading` đọc chúng, không đọc mảnh.
                "segments": _segments(parts[i], part_readings[i], scene),
            }
            for i, (line, voice, clip, scene, reading) in enumerate(zip(
                script.lines, voices, clips, timeline.scenes, readings
            ))
        ],
    }


def write(build: dict, dest: Path) -> Path:
    """Ghi ra đĩa, thụt lề 2 và giữ nguyên chữ Nhật (P-4: mở ra đọc được bằng mắt)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(build, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return dest
