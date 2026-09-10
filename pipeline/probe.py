"""
Đo độ dài thật của file media, đơn vị giây.

Đây là chỗ duy nhất trong dự án gọi ffprobe. Module này cố tình không biết
frame là gì (P-2) và cũng không biết kịch bản là gì — nó chỉ trả lời hai câu:
file này dài bao nhiêu giây, và khung hình nó to bao nhiêu.

Hai hàm chứ không phải một, vì hai chỗ dùng khác nhau hẳn: `duration_seconds`
chạy mỗi câu mỗi lần trong lúc dựng, còn `media_info` chỉ chạy khi soi sổ tài
sản. Gộp lại thì mỗi câu phải giải mã thêm một cục JSON không ai đọc tới.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


class ProbeError(RuntimeError):
    """ffprobe không đọc nổi file — hỏng, rỗng, hoặc không phải media."""


def duration_seconds(path: Path) -> float:
    """Độ dài thật của file audio/video, tính bằng giây."""
    if not path.exists():
        raise ProbeError(f"Không có file để đo: {path}")

    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(path),
            ],
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

    text = out.stdout.strip()
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
    """Đo độ dài, bề ngang, bề dọc và fps trong đúng một lần gọi ffprobe."""
    if not path.exists():
        raise ProbeError(f"Không có file để đo: {path}")

    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration:stream=width,height,r_frame_rate",
                "-of", "json",
                str(path),
            ],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError as exc:
        raise ProbeError(
            "Không tìm thấy lệnh ffprobe. Cài ffmpeg rồi chạy lại."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ProbeError(
            f"ffprobe không đọc được {path}:\n{exc.stderr.strip()}"
        ) from exc

    try:
        doc = json.loads(out.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError(f"ffprobe trả về thứ không phải JSON cho {path}") from exc

    # File mp3 cũng có "stream", nhưng không stream nào có width. Lấy stream
    # đầu tiên CÓ width thì audio ra (None, None) mà không cần phân biệt trước.
    video = next(
        (s for s in doc.get("streams", []) if s.get("width")), {}
    )
    raw_seconds = doc.get("format", {}).get("duration")
    if raw_seconds in (None, "", "N/A"):
        raise ProbeError(f"ffprobe không tìm thấy độ dài trong {path}")

    return MediaInfo(
        seconds=float(raw_seconds),
        width=video.get("width"),
        height=video.get("height"),
        fps=_fps(video.get("r_frame_rate")),
    )
