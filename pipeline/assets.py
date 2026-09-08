"""
Lớp B — trả lời "lấy hình ảnh và nhạc ở đâu", và trả lời trung thực.

Nguyên tắc: thiếu tài sản thì video vẫn phải dựng được, chỉ nhạt hơn. Clip
không tồn tại rơi về nền gradient, nhạc nền không tồn tại thì bỏ tiếng nhạc.
Không bao giờ ném lỗi vì một file media vắng mặt — nhưng luôn nói ra.

Module này đo giây, không đổi ra frame (P-2).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .probe import duration_seconds
from .script import Script, ScriptLine


@dataclass(frozen=True)
class SceneClip:
    """Clip nền của một cảnh, sau khi đã xác minh là có thật."""

    path: str | None
    start_seconds: float
    #: Phần CÒN LẠI SAU ĐIỂM CẮT, không phải độ dài cả clip. Background.tsx cắt
    #: bằng trimBefore rồi mới loop, nên đây mới là số hình thật sự còn dùng được.
    remaining_seconds: float | None


@dataclass(frozen=True)
class Soundtrack:
    path: str | None
    seconds: float | None


def resolve_clip(
    line: ScriptLine,
    public_dir: Path,
    log: Callable[[str], None] = print,
) -> SceneClip:
    if not line.clip:
        return SceneClip(path=None, start_seconds=0.0, remaining_seconds=None)

    if not (public_dir / line.clip).exists():
        log(f"          (thiếu {line.clip} -> dùng nền gradient)")
        return SceneClip(path=None, start_seconds=0.0, remaining_seconds=None)

    total = duration_seconds(public_dir / line.clip)
    start = line.clip_start_seconds
    if start >= total:
        log(
            f"          (clipStartInSeconds={start} vượt quá độ dài "
            f"clip {total:.1f}s -> cắt từ đầu)"
        )
        start = 0.0

    return SceneClip(path=line.clip, start_seconds=start, remaining_seconds=total - start)


def resolve_bgm(
    script: Script,
    public_dir: Path,
    log: Callable[[str], None] = print,
) -> Soundtrack:
    if not script.bgm:
        return Soundtrack(path=None, seconds=None)
    if not (public_dir / script.bgm).exists():
        log(f"  (thiếu nhạc nền {script.bgm} -> bỏ qua)")
        return Soundtrack(path=None, seconds=None)
    return Soundtrack(path=script.bgm, seconds=duration_seconds(public_dir / script.bgm))
