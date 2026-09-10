"""
NƠI DUY NHẤT TRONG DỰ ÁN ĐƯỢC ĐỔI GIÂY RA FRAME (P-2).

Nếu chữ chạy lệch tiếng, bug chỉ có thể nằm trong file này. Đó là toàn bộ lý do
module này tồn tại tách riêng: không module nào khác — kể cả `contract.py` ngay
bên cạnh — được phép nhân với fps.

Cách một cảnh được xếp:

    |<-- leadIn -->|<------- giọng đọc ------->|<-- pauseAfter -->|
    |              |                           |                  |
    0     audioStartInFrames        (hết tiếng)          durationInFrames

Cảnh 1 lặng thêm một đoạn ở đầu để tiêu đề ngày kịp hiện trên hình. Caption
câu 1 cũng chờ hết đoạn đó mới vào, để tiêu đề và caption không hiện cùng lúc:

    |<- pause ->|<-- leadIn -->|<------- giọng đọc ------->|<-- pauseAfter -->|
    0   captionStartInFrames   audioStartInFrames                durationInFrames

Không có cảnh mở đầu riêng nữa, nên tổng frame = các cảnh + màn kết.

Ba phép làm tròn, mỗi phép có lý do riêng:

  ceil  cho độ dài cảnh và độ dài tiếng — thà thừa một frame còn hơn cắt cụt
        âm cuối câu.
  floor cho clip nền và nhạc nền — đây là số hình/tiếng CÓ THẬT; làm tròn lên
        là hứa nhiều hơn file có, và Remotion sẽ trả về frame đen.
  round cho điểm vào của giọng đọc — sai một frame ở đây tai không nghe ra.
  round cho khoảng lặng đầu video, màn kết và độ dài chuyển cảnh — ba thứ này
        là con số thẩm mỹ người viết chọn, không đo từ file nào, nên không có
        bên nào để mà thà thừa hay thà thiếu.
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
    #: Caption vào ở frame thứ mấy trong cảnh. 0 ở mọi cảnh trừ cảnh 1 khi có
    #: tiêu đề — ở đó caption chờ tiêu đề hiện xong.
    caption_start_in_frames: int = 0


@dataclass(frozen=True)
class Timeline:
    fps: int
    scenes: list[Scene]
    bgm_duration_in_frames: int | None
    #: None khi kịch bản không khai `outro`.
    outro_duration_in_frames: int | None = None
    #: Độ dài đoạn mờ chồng giữa hai cảnh. KHÔNG cộng vào tổng: cảnh sau bắt đầu
    #: sớm hơn và chồng lên cuối cảnh trước, chứ không kéo dài video ra.
    transition_in_frames: int = 24

    @property
    def scenes_frames(self) -> int:
        return sum(s.duration_in_frames for s in self.scenes)

    @property
    def total_frames(self) -> int:
        return self.scenes_frames + (self.outro_duration_in_frames or 0)

    @property
    def seconds(self) -> float:
        return self.total_frames / self.fps

    @property
    def thumbnail_frame(self) -> int:
        """Frame làm ảnh bìa: tiêu đề ngày đã hiện đủ, câu 1 chưa đọc.

        Chính là lúc caption cảnh 1 bắt đầu vào. Ở frame đó caption còn trong suốt
        hoàn toàn và giọng đọc chưa cất lên, còn TitleCard.tsx cho ngày và chủ đề
        vào xong ở frame 44 — kịp trước khoảng lặng mặc định 45 frame. Không có
        tiêu đề thì là frame 0.
        """
        return self.scenes[0].caption_start_in_frames if self.scenes else 0


def _opening_pause(script: Script) -> float:
    """Khoảng lặng thêm ở đầu cảnh 1 cho tiêu đề. 0 khi kịch bản không khai `intro`."""
    return script.intro.pause_seconds if script.intro is not None else 0.0


def scene_seconds(script: Script, voices: list[Voiceover]) -> list[float]:
    """Mỗi cảnh dài bao nhiêu GIÂY — chưa đổi ra frame.

    Hàm này tồn tại vì `shots.py` phải biết cảnh dài bao nhiêu mới chọn được
    clip đủ dài, mà nó chạy TRƯỚC lúc quy ra frame. Đặt công thức ở đây để nó
    vẫn chỉ có đúng một bản: `build` bên dưới cũng gọi chính hàm này chứ không
    tự cộng lại lần nữa. Cộng lại lần nữa là mở đường cho hai chỗ lệch nhau.
    """
    pause = _opening_pause(script)
    return [
        (pause if i == 0 else 0.0) + script.lead_in + v.seconds + script.pause_after
        for i, v in enumerate(voices)
    ]


def _scene(
    fps: int, seconds: float,
    voice: Voiceover, clip: SceneClip,
    caption_start: int, lead_frames: int,
) -> Scene:
    return Scene(
        audio_duration_in_frames=math.ceil(voice.seconds * fps),
        duration_in_frames=math.ceil(seconds * fps),
        # Giọng đọc vào sau caption đúng leadIn, ở mọi cảnh như nhau — kể cả cảnh
        # 1, nơi caption đã lùi lại chờ tiêu đề.
        audio_start_in_frames=caption_start + lead_frames,
        clip_duration_in_frames=(
            math.floor(clip.remaining_seconds * fps)
            if clip.remaining_seconds is not None else None
        ),
        caption_start_in_frames=caption_start,
    )


def build(
    script: Script,
    voices: list[Voiceover],
    clips: list[SceneClip],
    bgm: Soundtrack,
    outro=None,
) -> Timeline:
    """Xếp toàn bộ video ra frame. Mọi đầu vào tính bằng giây, mọi đầu ra tính bằng frame."""
    if not (len(voices) == len(clips) == len(script.lines)):
        raise ValueError(
            f"Số câu không khớp: {len(script.lines)} câu kịch bản, "
            f"{len(voices)} giọng đọc, {len(clips)} clip."
        )

    fps = script.fps
    pause_frames = round(_opening_pause(script) * fps)
    # round() của Python làm tròn về số chẵn khi đúng .5 — leadIn 0,35s ở 30fps
    # ra 10 chứ không phải 11. Giữ nguyên: lệch tối đa một frame ở điểm vào
    # giọng đọc, và không ảnh hưởng tổng thời lượng.
    lead_frames = round(script.lead_in * fps)

    return Timeline(
        fps=fps,
        scenes=[
            _scene(fps, seconds, voice, clip,
                   caption_start=pause_frames if i == 0 else 0,
                   lead_frames=lead_frames)
            for i, (voice, clip, seconds) in enumerate(
                zip(voices, clips, scene_seconds(script, voices))
            )
        ],
        bgm_duration_in_frames=(
            math.floor(bgm.seconds * fps) if bgm.seconds is not None else None
        ),
        outro_duration_in_frames=(
            round(outro.seconds * fps) if outro is not None else None
        ),
        transition_in_frames=round(script.transition_seconds * fps),
    )
