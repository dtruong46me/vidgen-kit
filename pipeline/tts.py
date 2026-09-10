"""
Lớp A — sinh giọng đọc cho từng câu, và đo lại độ dài thật của nó.

P-1 nằm ở đây: file mp3 là nguồn sự thật. Module này không suy ra thời lượng từ
số ký tự hay tốc độ đọc — nó gọi ffprobe đo đúng file vừa sinh ra.

Cache đánh theo VÂN TAY NỘI DUNG, không theo ngày sửa file: chỉ `ja`, giọng,
tốc độ và cao độ mới làm câu phải đọc lại. Đổi nhịp nghỉ hay đổi clip nền thì
không câu nào phải sinh lại — đó là lý do sửa `pauseAfter` xong chạy `make
content` chỉ mất vài giây.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .probe import duration_seconds
from .script import Script


class TTSError(RuntimeError):
    """edge-tts không sinh được file."""


@dataclass(frozen=True)
class Voiceover:
    """Giọng đọc của một câu, đã đo xong."""

    rel_path: str      # đường dẫn Remotion dùng, tương đối so với studio/public/
    abs_path: Path
    seconds: float


def _fingerprint(ja: str, voice: str, rate: str, pitch: str) -> str:
    return hashlib.sha1(f"{ja}|{voice}|{rate}|{pitch}".encode("utf-8")).hexdigest()


def _speak(text: str, voice: str, rate: str, pitch: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                sys.executable, "-m", "edge_tts",
                "--voice", voice,
                # dạng --rate=-10%: giá trị âm viết rời sẽ bị argparse hiểu là tên flag
                f"--rate={rate}",
                f"--pitch={pitch}",
                "--text", text,
                "--write-media", str(dest),
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise TTSError(
            f"edge-tts hỏng ở câu \"{text[:24]}...\":\n{exc.stderr.strip()}"
        ) from exc

    if not dest.exists() or dest.stat().st_size == 0:
        raise TTSError(f"edge-tts chạy xong nhưng {dest.name} rỗng. Thử lại, thường do mạng.")


def synthesize(
    script: Script,
    public_dir: Path,
    cache_path: Path,
    log: Callable[[str], None] = print,
) -> list[Voiceover]:
    """Đảm bảo mọi câu đều có mp3 đúng nội dung, rồi trả về độ dài thật từng câu."""
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log("  (cache hỏng, bỏ qua và đọc lại toàn bộ)")

    fresh: dict[str, str] = {}
    voices = []

    for i, line in enumerate(script.lines, start=1):
        name = f"line-{i:02d}.mp3"
        rel = f"audio/{script.slug}/{name}"
        dest = public_dir / rel
        stamp = _fingerprint(line.ja, script.voice, script.rate, script.pitch)

        if cache.get(name) == stamp and dest.exists():
            log(f"  [cache] {name}")
        else:
            log(f"  [tts]   {name}  {line.ja[:24]}...")
            _speak(line.ja, script.voice, script.rate, script.pitch, dest)

        fresh[name] = stamp
        # Ghi cache ngay sau từng câu. Bản cũ ghi một lần ở cuối, nên hỏng ở câu
        # thứ bảy là mất luôn công của sáu câu trước.
        cache_path.write_text(json.dumps(fresh, indent=2), encoding="utf-8")

        voices.append(Voiceover(rel_path=rel, abs_path=dest, seconds=duration_seconds(dest)))

    return voices
