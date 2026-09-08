"""
Đo độ dài thật của file media, đơn vị giây.

Đây là chỗ duy nhất trong dự án gọi ffprobe. Module này cố tình không biết
frame là gì (P-2) và cũng không biết kịch bản là gì — nó chỉ trả lời đúng một
câu: file này dài bao nhiêu giây.
"""

from __future__ import annotations

import subprocess
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
