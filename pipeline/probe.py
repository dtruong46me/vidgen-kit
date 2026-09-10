"""
Đo độ dài thật của file media, đơn vị giây.

Đây là chỗ duy nhất trong dự án gọi ffprobe. Module này cố tình không biết
frame là gì (P-2) và cũng không biết kịch bản là gì — nó chỉ trả lời ba câu:
file này dài bao nhiêu giây, khung hình nó ra sao, và nó thật sự có bao nhiêu
frame.

Ba hàm chứ không phải một, vì ba chỗ dùng khác nhau hẳn: `duration_seconds`
chạy mỗi câu mỗi lần trong lúc dựng, `media_info` chạy khi soi sổ tài sản và
khi kiểm MP4, còn `count_frames` phải đọc hết cả file nên chỉ `make check` gọi.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


class ProbeError(RuntimeError):
    """ffprobe không đọc nổi file — hỏng, rỗng, hoặc không phải media."""


def _ffprobe(path: Path, *args: str) -> str:
    """Chạy ffprobe trên một file, trả về stdout. Mọi lỗi đổi thành ProbeError."""
    if not path.exists():
        raise ProbeError(f"Không có file để đo: {path}")

    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", *args, str(path)],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError as exc:  # chưa cài ffmpeg
        raise ProbeError(
            "Không tìm thấy lệnh ffprobe. Cài ffmpeg rồi chạy lại."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ProbeError(
            f"ffprobe không đọc được {path}:\n{exc.stderr.strip()}"
        ) from exc
    return out.stdout.strip()


def duration_seconds(path: Path) -> float:
    """Độ dài thật của file audio/video, tính bằng giây."""
    text = _ffprobe(path, "-show_entries", "format=duration", "-of", "csv=p=0")
    if not text or text == "N/A":
        raise ProbeError(f"ffprobe không tìm thấy độ dài trong {path}")
    return float(text)


@dataclass(frozen=True)
class MediaInfo:
    """Kích thước và độ dài thật của một file media. Không đoán, chỉ đo."""

    seconds: float
    width: int | None
    height: int | None
    #: Khung hình mỗi giây của clip nguồn. Khác fps của video đích thì Remotion
    #: phải nhân đôi hoặc bỏ bớt frame — clip lia chậm sẽ hơi giật.
    fps: float | None
    #: Có luồng tiếng hay không. MP4 dựng ra mà thiếu luồng này là video câm —
    #: thứ mắt không bắt được khi chỉ xem ảnh tĩnh.
    has_audio: bool = False

    @property
    def is_vertical(self) -> bool:
        return bool(self.width and self.height and self.height > self.width)


def _fps(raw: str | None) -> float | None:
    """r_frame_rate của ffprobe ra dạng phân số "25/1". Đổi ra số thật."""
    if not raw or "/" not in raw:
        return None
    num, den = raw.split("/", 1)
    try:
        return float(num) / float(den) if float(den) else None
    except ValueError:
        return None


def media_info(path: Path) -> MediaInfo:
    """Đo độ dài, bề ngang, bề dọc, fps và luồng tiếng trong đúng một lần gọi."""
    raw = _ffprobe(
        path,
        "-show_entries",
        "format=duration:stream=codec_type,width,height,r_frame_rate",
        "-of", "json",
    )
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProbeError(f"ffprobe trả về thứ không phải JSON cho {path}") from exc

    streams = doc.get("streams", [])
    # File mp3 cũng có "stream", nhưng không stream nào có width. Lấy stream
    # đầu tiên CÓ width thì audio ra (None, None) mà không cần phân biệt trước.
    video = next((s for s in streams if s.get("width")), {})
    raw_seconds = doc.get("format", {}).get("duration")
    if raw_seconds in (None, "", "N/A"):
        raise ProbeError(f"ffprobe không tìm thấy độ dài trong {path}")

    return MediaInfo(
        seconds=float(raw_seconds),
        width=video.get("width"),
        height=video.get("height"),
        fps=_fps(video.get("r_frame_rate")),
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
    )


def count_frames(path: Path) -> int:
    """Đếm số frame THẬT của luồng hình đầu tiên.

    Đếm gói (`-count_packets`) chứ không giải mã từng frame (`-count_frames`):
    với MP4 H.264 mà Remotion xuất ra, mỗi gói hình đúng một frame, nên hai
    cách ra cùng một số — mà đếm gói nhanh hơn cả chục lần vì không phải giải
    mã 1080×1920. Đừng tin `duration × fps`: độ dài của container tính cả
    luồng tiếng, lệch vài chục mili giây là lệch một frame.
    """
    text = _ffprobe(
        path,
        "-select_streams", "v:0",
        "-count_packets",
        "-show_entries", "stream=nb_read_packets",
        "-of", "csv=p=0",
    )
    try:
        return int(text.strip().rstrip(","))
    except ValueError as exc:
        raise ProbeError(f"ffprobe không đếm được frame trong {path}: {text!r}") from exc
