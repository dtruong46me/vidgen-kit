"""
Lớp A — sinh giọng đọc cho từng câu, đo lại độ dài thật, và ghi lại GIỌNG ĐỌC
CHẠM VÀO TỪNG CHỮ Ở GIÂY THỨ MẤY.

P-1 nằm ở đây: file mp3 là nguồn sự thật. Module này không suy ra thời lượng từ
số ký tự hay tốc độ đọc — nó gọi ffprobe đo đúng file vừa sinh ra.

Mốc từng chữ (`Voiceover.words`) cũng vậy: không ước lượng theo số mora, mà lấy
chính sự kiện `WordBoundary` do máy chủ đọc trả về trong cùng một lượt gọi. Nhờ
nó, `timeline.py` biết nửa sau của một câu dài bắt đầu ở đúng giây nào để đổi
caption, thay vì chia đôi theo số ký tự rồi hy vọng. Đó là lý do module này gọi
thư viện `edge_tts` trực tiếp thay vì chạy lệnh `python3 -m edge_tts` như trước:
mốc từng chữ chỉ có trong luồng dữ liệu, lệnh ngoài gộp mất. Đã đối chiếu 8 câu
của 2026-08-20 — độ dài mp3 giống hệt từng mili giây so với đường lệnh cũ, nên
mốc hồi quy 1562 frame không đổi.

Cache đánh theo VÂN TAY NỘI DUNG, không theo ngày sửa file: chỉ `ja`, giọng,
tốc độ và cao độ mới làm câu phải đọc lại. Đổi nhịp nghỉ hay đổi clip nền thì
không câu nào phải sinh lại — đó là lý do sửa `pauseAfter` xong chạy `make
content` chỉ mất vài giây. Mốc từng chữ nằm luôn trong cache cạnh vân tay, vì
nó cũng đến từ chính lượt đọc đó và cũng sinh lại được y hệt.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .probe import duration_seconds
from .script import Script


class TTSError(RuntimeError):
    """edge-tts không sinh được file."""


@dataclass(frozen=True)
class Word:
    """Một chữ trong câu, kèm giây nó được đọc lên. Mốc tính từ đầu file mp3."""

    start_seconds: float
    seconds: float
    text: str


@dataclass(frozen=True)
class Voiceover:
    """Giọng đọc của một câu, đã đo xong."""

    rel_path: str      # đường dẫn Remotion dùng, tương đối so với studio/public/
    abs_path: Path
    seconds: float
    #: Mốc từng chữ. Rỗng khi đọc từ cache đời cũ — `timeline.py` có đường lui.
    words: tuple[Word, ...] = ()


def _fingerprint(ja: str, voice: str, rate: str, pitch: str) -> str:
    return hashlib.sha1(f"{ja}|{voice}|{rate}|{pitch}".encode("utf-8")).hexdigest()


async def _stream(text: str, voice: str, rate: str, pitch: str, dest: Path) -> list[Word]:
    import edge_tts

    words: list[Word] = []
    chunks: list[bytes] = []
    communicate = edge_tts.Communicate(
        text, voice, rate=rate, pitch=pitch,
        # Mặc định của edge-tts là SentenceBoundary — gộp cả câu thành một mốc,
        # tức đúng thứ không dùng được. Xin mốc từng chữ ngay từ lượt gọi này.
        boundary="WordBoundary",
    )
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            # edge-tts đo bằng đơn vị 100 nano giây.
            words.append(Word(
                start_seconds=chunk["offset"] / 1e7,
                seconds=chunk["duration"] / 1e7,
                text=chunk["text"],
            ))

    if not chunks:
        raise TTSError(
            f"edge-tts không trả về tiếng nào cho câu \"{text[:24]}...\". "
            f"Thử lại, thường do mạng."
        )
    # Ghi một lần sau khi đã nhận đủ: hỏng giữa chừng thì không để lại file cụt
    # mà lần chạy sau lại tưởng là file tốt.
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"".join(chunks))
    return words


def _speak(text: str, voice: str, rate: str, pitch: str, dest: Path) -> list[Word]:
    try:
        return asyncio.run(_stream(text, voice, rate, pitch, dest))
    except TTSError:
        raise
    except ImportError as exc:
        raise TTSError(
            f"Thiếu thư viện edge-tts ở {sys.executable}.\n"
            f"Cài bằng: make setup"
        ) from exc
    except Exception as exc:
        raise TTSError(
            f"edge-tts hỏng ở câu \"{text[:24]}...\":\n{exc}"
        ) from exc


def _cached_words(entry: object) -> tuple[str, tuple[Word, ...]] | None:
    """Đọc một mục cache. None = không dùng được, đọc lại câu đó.

    Cache đời cũ ghi thẳng chuỗi vân tay và không có mốc từng chữ. Bỏ qua chứ
    không cố dùng: đọc lại một câu mất hai giây, còn caption đổi sai chỗ thì
    phải xem video mới biết.
    """
    if not isinstance(entry, dict) or "stamp" not in entry:
        return None
    words = tuple(
        Word(start_seconds=float(w[0]), seconds=float(w[1]), text=str(w[2]))
        for w in entry.get("words", [])
    )
    return str(entry["stamp"]), words


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

    fresh: dict[str, dict] = {}
    voices = []

    for i, line in enumerate(script.lines, start=1):
        name = f"line-{i:02d}.mp3"
        rel = f"audio/{script.slug}/{name}"
        dest = public_dir / rel
        stamp = _fingerprint(line.ja, script.voice, script.rate, script.pitch)

        hit = _cached_words(cache.get(name))
        if hit is not None and hit[0] == stamp and dest.exists():
            log(f"  [cache] {name}")
            words = hit[1]
        else:
            log(f"  [tts]   {name}  {line.ja[:24]}...")
            words = tuple(_speak(line.ja, script.voice, script.rate, script.pitch, dest))

        fresh[name] = {
            "stamp": stamp,
            "words": [[round(w.start_seconds, 4), round(w.seconds, 4), w.text] for w in words],
        }
        # Ghi cache ngay sau từng câu. Bản cũ ghi một lần ở cuối, nên hỏng ở câu
        # thứ bảy là mất luôn công của sáu câu trước.
        cache_path.write_text(
            json.dumps(fresh, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        voices.append(Voiceover(
            rel_path=rel, abs_path=dest,
            seconds=duration_seconds(dest), words=words,
        ))

    return voices
