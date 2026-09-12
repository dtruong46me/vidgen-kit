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

Câu dài được `phrase.py` cắt thành mấy MẢNH caption. Mảnh KHÔNG phải cảnh: cùng
một cảnh, cùng một clip, cùng một file mp3, chỉ có chữ là đổi giữa chừng. Nên
cắt mảnh không cộng thêm một frame nào vào tổng — mốc hồi quy không nhúc nhích.

Mảnh sau vào ở đâu thì không đoán: `tts.py` ghi lại giọng đọc chạm vào từng chữ
ở giây thứ mấy (`WordBoundary`), ở đây chỉ việc tra chữ đầu của mảnh rồi lùi
lại đúng `leadIn` — bằng đúng khoảng chữ đi trước tiếng ở đầu mỗi cảnh. Không có
mốc từng chữ (cache đời cũ) thì chia theo tỉ lệ số ký tự, và nói ra ở đường lui.

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


#: Caption vào xong trong bao nhiêu frame — phải khớp `IN_FRAMES` của
#: `studio/src/Caption.tsx`. Chỉ dùng để CHỌN frame làm ảnh bìa, không tham gia
#: phép cộng nào: lệch một hai frame thì ảnh bìa xấu đi chứ timeline không lệch.
CAPTION_IN_FRAMES = 26
#: Chờ thêm bấy nhiêu frame sau khi chữ vào xong rồi mới chụp ảnh bìa — một
#: nhịp thở, để chắc chắn bắt được chữ đứng yên chứ không phải frame cuối của
#: animation.
THUMBNAIL_SETTLE = 6

#: Mảnh caption ngắn nhất được phép. Ngắn hơn thì chữ vừa hiện xong đã phải tắt,
#: đọc ra là giật. Dùng để ép các mốc không dồn cục khi giọng đọc lướt nhanh.
MIN_SEGMENT_FRAMES = 15


@dataclass(frozen=True)
class SceneSegment:
    """Một mảnh caption trong cảnh. Mốc tính từ ĐẦU CẢNH, như mọi số khác ở đây."""

    from_in_frames: int
    duration_in_frames: int


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
    #: Các mảnh caption. RỖNG khi câu đủ ngắn để hiện nguyên — đó là đa số, và
    #: nó ra đúng hành vi có từ trước.
    segments: tuple[SceneSegment, ...] = ()


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
        """Frame làm ảnh bìa: ngày tháng VÀ câu chào cùng hiện đủ trên hình.

        Bản trước chụp đúng lúc caption cảnh 1 BẮT ĐẦU vào — ở frame đó caption
        còn trong suốt hoàn toàn, nên ảnh bìa chỉ có mỗi tiêu đề ngày nằm trên
        clip. Mà câu 1 của mọi kịch bản là
        `今日は、<ngày>です。おはようございます。`: bỏ nó đi là bỏ mất lời chào,
        thứ nói cho người lướt biết đây là video gì.

        Giờ lùi lại `CAPTION_IN_FRAMES + THUMBNAIL_SETTLE` frame, tức caption đã
        vào xong và đứng yên một nhịp. Tiêu đề ngày vẫn còn nguyên — nó sống hết
        cảnh 1 và chỉ mờ đi ở đoạn chuyển sang cảnh 2. Không có tiêu đề thì
        caption vào ngay từ frame 0 và công thức vẫn đúng.
        """
        if not self.scenes:
            return 0
        scene = self.scenes[0]
        start = scene.caption_start_in_frames
        span = scene.duration_in_frames - start
        if scene.segments:
            # Câu 1 mà bị cắt mảnh thì lời chào nằm ở mảnh CUỐI — lấy mảnh đó.
            start = scene.segments[-1].from_in_frames
            span = scene.segments[-1].duration_in_frames
        # `span // 2` là lưới an toàn cho mảnh quá ngắn: thà lấy giữa mảnh còn
        # hơn rơi vào đoạn chữ đang tắt đi.
        return start + min(CAPTION_IN_FRAMES + THUMBNAIL_SETTLE, span // 2)


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


def _word_marks(text: str, words) -> list[tuple[int, float]]:
    """Mỗi chữ nằm ở ký tự thứ mấy trong câu, và được đọc lên ở giây thứ mấy.

    Danh sách `words` bỏ qua dấu câu, nên không dò được bằng cách cộng dồn độ
    dài — phải tìm từng chữ trong câu gốc, tiếp nối từ chỗ chữ trước kết thúc.
    """
    marks, cursor = [], 0
    for w in words:
        idx = text.find(w.text, cursor)
        if idx < 0:
            idx = cursor
        marks.append((idx, w.start_seconds))
        cursor = idx + len(w.text)
    return marks


def _speech_seconds_at(text: str, words, char_index: int, total_seconds: float) -> float:
    """Giọng đọc chạm tới ký tự thứ `char_index` ở giây thứ mấy trong file mp3."""
    for idx, start in _word_marks(text, words):
        if idx >= char_index:
            return start
    # Đường lui: không có mốc từng chữ (cache đời cũ, hoặc máy chủ không trả
    # về chữ nào) thì chia theo tỉ lệ ký tự. Sai vài phần mười giây, nhưng vẫn
    # hơn là để cả câu dài chen vào một khung.
    return total_seconds * char_index / max(len(text), 1)


def _segments(
    ja_parts: tuple[str, ...], voice: Voiceover, fps: int,
    caption_start: int, audio_start: int, lead_frames: int, scene_frames: int,
) -> tuple[SceneSegment, ...]:
    """Chia cảnh thành các mảnh caption. Rỗng khi câu hiện nguyên cả."""
    if len(ja_parts) <= 1:
        return ()

    text = "".join(ja_parts)
    starts = [caption_start]
    at = 0
    for part in ja_parts[:-1]:
        at += len(part)
        seconds = _speech_seconds_at(text, voice.words, at, voice.seconds)
        # Chữ đi trước tiếng đúng leadIn — bằng đúng khoảng ở đầu mỗi cảnh, để
        # mảnh sau cũng kịp hiện xong trước khi giọng đọc tới nó.
        frame = audio_start + round(seconds * fps) - lead_frames
        # Ép tăng dần và chừa chỗ cho mảnh cuối: giọng đọc lướt nhanh qua một
        # vế ngắn cũng không được làm hai mảnh chồng lên nhau.
        lo = starts[-1] + MIN_SEGMENT_FRAMES
        hi = scene_frames - MIN_SEGMENT_FRAMES * (len(ja_parts) - len(starts))
        starts.append(max(lo, min(frame, max(lo, hi))))

    edges = (*starts, scene_frames)
    return tuple(
        SceneSegment(from_in_frames=a, duration_in_frames=b - a)
        for a, b in zip(edges, edges[1:])
    )


def _scene(
    fps: int, seconds: float,
    voice: Voiceover, clip: SceneClip,
    caption_start: int, lead_frames: int,
    ja_parts: tuple[str, ...] = (),
) -> Scene:
    scene_frames = math.ceil(seconds * fps)
    # Giọng đọc vào sau caption đúng leadIn, ở mọi cảnh như nhau — kể cả cảnh
    # 1, nơi caption đã lùi lại chờ tiêu đề.
    audio_start = caption_start + lead_frames
    return Scene(
        audio_duration_in_frames=math.ceil(voice.seconds * fps),
        duration_in_frames=scene_frames,
        audio_start_in_frames=audio_start,
        clip_duration_in_frames=(
            math.floor(clip.remaining_seconds * fps)
            if clip.remaining_seconds is not None else None
        ),
        caption_start_in_frames=caption_start,
        segments=_segments(ja_parts, voice, fps, caption_start, audio_start,
                           lead_frames, scene_frames),
    )


def build(
    script: Script,
    voices: list[Voiceover],
    clips: list[SceneClip],
    bgm: Soundtrack,
    outro=None,
    parts: list[tuple[str, ...]] | None = None,
) -> Timeline:
    """Xếp toàn bộ video ra frame. Mọi đầu vào tính bằng giây, mọi đầu ra tính bằng frame.

    `parts` là câu Nhật của từng MẢNH caption, do `phrase.py` chia. Bỏ trống thì
    câu nào cũng hiện nguyên — đúng hành vi có từ trước BƯỚC 9.
    """
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

    splits = parts or [()] * len(script.lines)

    return Timeline(
        fps=fps,
        scenes=[
            _scene(fps, seconds, voice, clip,
                   caption_start=pause_frames if i == 0 else 0,
                   lead_frames=lead_frames, ja_parts=tuple(ja_parts))
            for i, (voice, clip, seconds, ja_parts) in enumerate(
                zip(voices, clips, scene_seconds(script, voices), splits)
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
