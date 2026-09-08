"""
Lớp B — chọn clip nền cho từng cảnh, khi kịch bản không tự chỉ định.

Đây là thứ làm cho "một ngày một video" thành khả thi. Trước bước này, mỗi câu
trong kịch bản phải tự khai `clip` và `clipStartInSeconds`, tức là người viết
phải nhớ clip nào dài bao nhiêu và đã cắt tới đâu — việc đó làm bằng tay được
một hôm, không làm được ba trăm hôm.

Người viết vẫn thắng máy: câu nào đã ghi `clip` thì giữ nguyên, không hỏi lại.
Bộ chọn chỉ điền vào những câu bỏ trống.

Bốn quy tắc, theo đúng thứ tự ưu tiên:

  1. Đủ dài. Cảnh dài 7 giây thì đoạn clip còn lại phải ≥ 7 giây + biên an
     toàn. Không đủ thì Remotion cho clip chạy lặp, và mắt nhìn ra ngay.
  2. Đúng tag. Câu nào khai `tags` thì chỉ lấy clip có tag trùng.
  3. Không lặp lại clip của cảnh ngay trước. Hai cảnh liền nhau cùng một hình
     thì người xem tưởng video bị đứng.
  4. Ưu tiên đoạn hình CHƯA dùng. Mỗi clip có một con trỏ chạy dần về cuối;
     clip nào còn đủ chỗ phía trước con trỏ thì hơn clip phải quay về đầu.
  5. Trong số ngang nhau, clip nào dùng ít lần nhất thì đến lượt. Nhờ vậy cả
     thư viện được dùng đều thay vì mòn một clip.

Cùng một kịch bản và cùng một thư viện thì luôn ra cùng một kết quả — không có
random. Đó là điều kiện để `make content` chạy lại hai lần cho ra file giống
nhau, và để mốc hồi quy 1462 frame còn nghĩa lý.

Module này đo giây, không đổi ra frame (P-2).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from .library import Entry, Library
from .probe import ProbeError, duration_seconds
from .script import ScriptLine

#: Biên an toàn khi so độ dài cảnh với độ dài đoạn clip còn lại, tính bằng giây.
#:
#: Cần ít nhất 1/fps vì hai đầu làm tròn ngược chiều nhau: độ dài cảnh làm tròn
#: LÊN, còn độ dài clip làm tròn XUỐNG (xem timeline.py). Chọn sát mép thì hai
#: phép làm tròn đó chênh nhau một frame và cảnh lặp đúng một hình cuối.
#:
#: Lấy 0,25s chứ không lấy 1/30s vì lý do thứ hai: rất nhiều clip stock có cú
#: cắt hoặc cú rung máy ở vài frame cuối. Chừa ra một phần tư giây là tránh
#: được cả hai.
SAFETY_SECONDS = 0.25


@dataclass(frozen=True)
class Choice:
    """Clip đã chọn cho một cảnh, kèm lý do để in ra cho người đọc."""

    clip: str | None
    start_seconds: float
    #: True khi bộ chọn tự điền; False khi kịch bản đã chỉ định sẵn.
    automatic: bool
    reason: str = ""


def _durations(shots: list[Entry], public_dir: Path) -> dict[str, float]:
    """Đo độ dài mọi clip trong sổ. Clip thiếu file thì loại khỏi cuộc chọn."""
    out = {}
    for shot in shots:
        try:
            out[shot.id] = duration_seconds(public_dir / shot.file)
        except ProbeError:
            continue
    return out


def _start_for(
    shot: Entry, need: float, cursor: float, total: float
) -> tuple[float, bool] | None:
    """Cắt clip này từ giây thứ mấy, hoặc None nếu nó không đủ dài cho cảnh.

    Con trỏ `cursor` là chỗ lần dùng trước đã dừng lại. Đi tiếp từ đó thì hai
    lần dùng cùng một clip ra hai đoạn hình khác nhau; hết clip thì quay về đầu
    và chiếu lại đoạn đã chiếu.

    Trả về (điểm cắt, có phải quay vòng không). Cờ thứ hai là để bên gọi biết
    lựa chọn này "cũ" hay "mới" mà xếp hạng.
    """
    if total - cursor >= need:
        return cursor, False
    if total >= need:
        return 0.0, True
    return None


def choose(
    lines: list[ScriptLine],
    scene_seconds: list[float],
    library: Library,
    public_dir: Path,
    default_tags: tuple[str, ...] = (),
    log: Callable[[str], None] = print,
) -> list[Choice]:
    """Chọn clip cho từng cảnh. Trả về đúng một Choice cho mỗi câu."""
    shots = library.shots
    total = _durations(shots, public_dir)
    usable = [s for s in shots if s.id in total]
    # Thứ tự trong sổ là thứ tự phá hoà — nhờ vậy kết quả không phụ thuộc
    # thứ tự dict hay thứ tự hệ thống file.
    rank = {shot.id: i for i, shot in enumerate(usable)}

    cursor = {shot.id: 0.0 for shot in usable}
    uses = {shot.id: 0 for shot in usable}
    previous: str | None = None
    out: list[Choice] = []

    for line, need in zip(lines, scene_seconds):
        # --- người viết đã chọn: giữ nguyên, chỉ ghi nhận để máy tránh lặp lại
        if line.clip:
            entry = library.by_file(line.clip)
            if entry and entry.id in cursor:
                uses[entry.id] += 1
                cursor[entry.id] = line.clip_start_seconds + need
                previous = entry.id
            else:
                previous = None
            out.append(Choice(
                clip=line.clip,
                start_seconds=line.clip_start_seconds,
                automatic=False,
            ))
            continue

        # --- máy chọn
        if not usable:
            out.append(Choice(
                clip=None, start_seconds=0.0, automatic=True,
                reason="sổ chưa có clip nào dùng được -> nền gradient",
            ))
            continue

        wanted = line.tags or default_tags
        pool = [s for s in usable if s.matches(wanted)]
        note = ""
        if not pool:
            pool = usable
            note = f" (không clip nào có tag {', '.join(wanted)})"

        room = need + SAFETY_SECONDS
        fits = [
            (s, *found) for s in pool
            if (found := _start_for(s, room, cursor[s.id], total[s.id])) is not None
        ]

        if not fits:
            # Không clip nào đủ dài. Lấy clip dài nhất cho đỡ phải lặp nhiều
            # nhất, và nói thẳng là cảnh này sẽ lặp.
            best = max(pool, key=lambda s: (total[s.id], -rank[s.id]))
            out.append(Choice(
                clip=best.file, start_seconds=0.0, automatic=True,
                reason=(f"không clip nào đủ {need:.1f}s — dùng {best.id} "
                        f"({total[best.id]:.1f}s) và chấp nhận lặp"),
            ))
            uses[best.id] += 1
            cursor[best.id] = total[best.id]
            previous = best.id
            continue

        # Quy tắc 3: tránh clip của cảnh ngay trước, trừ khi nó là lựa chọn duy nhất.
        without_previous = [row for row in fits if row[0].id != previous]
        pick_from = without_previous or fits
        # Quy tắc 4 rồi 5: chưa quay vòng trước, rồi mới đến ít dùng nhất.
        # Thứ tự trong sổ phá hoà ở cuối, nên kết quả hoàn toàn tất định.
        shot, start, wrapped = min(
            pick_from,
            key=lambda row: (row[2], uses[row[0].id], rank[row[0].id]),
        )

        uses[shot.id] += 1
        cursor[shot.id] = start + need
        previous = shot.id
        out.append(Choice(
            # round(..., 3) làm tròn GIÂY cho build.json đỡ rác số thập phân.
            # Đây không phải phép đổi ra frame — chỗ đó chỉ có timeline.py (P-2).
            clip=shot.file, start_seconds=round(start, 3), automatic=True,
            reason=(f"{shot.id} từ giây {start:.1f}"
                    f"{' (quay vòng, đoạn hình dùng lại)' if wrapped else ''}{note}"),
        ))

    return out


def apply(lines: list[ScriptLine], choices: list[Choice]) -> list[ScriptLine]:
    """Trả về danh sách câu đã điền clip, để phần sau của dây chuyền không phải
    biết clip từ kịch bản hay từ bộ chọn mà ra."""
    return [
        replace(line, clip=choice.clip, clip_start_seconds=choice.start_seconds)
        for line, choice in zip(lines, choices)
    ]
