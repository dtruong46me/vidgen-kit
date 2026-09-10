"""
NƠI DUY NHẤT TRONG DỰ ÁN ĐƯỢC ĐỔI GIÂY RA FRAME (P-2).

Nếu chữ chạy lệch tiếng, bug chỉ có thể nằm trong file này. Đó là toàn bộ lý do
module này tồn tại tách riêng: không module nào khác — kể cả `contract.py` ngay
bên cạnh — được phép nhân với fps.

Cách một cảnh được xếp:

    |<-- leadIn -->|<------- giọng đọc ------->|<-- pauseAfter -->|
    |              |                           |                  |
    0     audioStartInFrames        (hết tiếng)          durationInFrames

Ba phép làm tròn, mỗi phép có lý do riêng:

  ceil  cho độ dài cảnh và độ dài tiếng — thà thừa một frame còn hơn cắt cụt
        âm cuối câu.
  floor cho clip nền và nhạc nền — đây là số hình/tiếng CÓ THẬT; làm tròn lên
        là hứa nhiều hơn file có, và Remotion sẽ trả về frame đen.
  round cho điểm vào của giọng đọc — sai một frame ở đây tai không nghe ra.
  round cho màn mở đầu, màn kết và độ dài chuyển cảnh — ba thứ này là con số
        thẩm mỹ người viết chọn, không đo từ file nào, nên không có bên nào để
        mà thà thừa hay thà thiếu.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .assets import SceneClip, Soundtrack
from .script import Script
from .tts import Voiceover


@dataclass(frozen=True)
class Scene:
    """Một cảnh đã quy ra frame. Từ đây trở đi không còn đơn vị giây."""

    audio_duration_in_frames: int
    duration_in_frames: int
    audio_start_in_frames: int
    clip_duration_in_frames: int | None


@dataclass(frozen=True)
class Timeline:
    fps: int
    scenes: list[Scene]
    bgm_duration_in_frames: int | None
    #: None khi kịch bản không khai `intro`/`outro`. Đó là mặc định — nhờ vậy
    #: kịch bản viết trước BƯỚC 5 ra đúng số frame cũ, không lệch một frame nào.
    intro_duration_in_frames: int | None = None
    outro_duration_in_frames: int | None = None
    #: Độ dài đoạn mờ chồng giữa hai cảnh. KHÔNG cộng vào tổng: cảnh sau bắt đầu
    #: sớm hơn và chồng lên cuối cảnh trước, chứ không kéo dài video ra.
    transition_in_frames: int = 24

    @property
    def scenes_frames(self) -> int:
        return sum(s.duration_in_frames for s in self.scenes)

    @property
    def total_frames(self) -> int:
        return (
            (self.intro_duration_in_frames or 0)
            + self.scenes_frames
            + (self.outro_duration_in_frames or 0)
        )

    @property
    def seconds(self) -> float:
        return self.total_frames / self.fps


def scene_seconds(script: Script, voices: list[Voiceover]) -> list[float]:
    """Mỗi cảnh dài bao nhiêu GIÂY — chưa đổi ra frame.

    Hàm này tồn tại vì `shots.py` phải biết cảnh dài bao nhiêu mới chọn được
    clip đủ dài, mà nó chạy TRƯỚC lúc quy ra frame. Đặt công thức ở đây để nó
    vẫn chỉ có đúng một bản: `_scene` bên dưới cũng gọi chính hàm này chứ không
    tự cộng lại lần nữa. Cộng lại lần nữa là mở đường cho hai chỗ lệch nhau.
    """
    return [script.lead_in + v.seconds + script.pause_after for v in voices]


def _scene(
    fps: int, seconds: float,
    voice: Voiceover, clip: SceneClip, lead_in: float,
) -> Scene:
    return Scene(
        audio_duration_in_frames=math.ceil(voice.seconds * fps),
        duration_in_frames=math.ceil(seconds * fps),
        # round() của Python làm tròn về số chẵn khi đúng .5 — leadIn 0,35s ở
        # 30fps ra 10 chứ không phải 11. Giữ nguyên: lệch tối đa một frame ở
        # điểm vào giọng đọc, và không ảnh hưởng tổng thời lượng.
        audio_start_in_frames=round(lead_in * fps),
        clip_duration_in_frames=(
            math.floor(clip.remaining_seconds * fps)
            if clip.remaining_seconds is not None else None
        ),
    )


def build(
    script: Script,
    voices: list[Voiceover],
    clips: list[SceneClip],
    bgm: Soundtrack,
    intro=None,
    outro=None,
) -> Timeline:
    """Xếp toàn bộ video ra frame. Mọi đầu vào tính bằng giây, mọi đầu ra tính bằng frame."""
    if not (len(voices) == len(clips) == len(script.lines)):
        raise ValueError(
            f"Số câu không khớp: {len(script.lines)} câu kịch bản, "
            f"{len(voices)} giọng đọc, {len(clips)} clip."
        )

    return Timeline(
        fps=script.fps,
        scenes=[
            _scene(script.fps, seconds, voice, clip, script.lead_in)
            for voice, clip, seconds in zip(
                voices, clips, scene_seconds(script, voices)
            )
        ],
        bgm_duration_in_frames=(
            math.floor(bgm.seconds * script.fps) if bgm.seconds is not None else None
        ),
        intro_duration_in_frames=(
            round(intro.seconds * script.fps) if intro is not None else None
        ),
        outro_duration_in_frames=(
            round(outro.seconds * script.fps) if outro is not None else None
        ),
        transition_in_frames=round(script.transition_seconds * script.fps),
    )
