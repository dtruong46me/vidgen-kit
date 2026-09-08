"""
Lớp A — dựng nội dung cho màn mở đầu và màn kết.

Module này chỉ sinh CHỮ, không sinh frame. Nó trả lời "màn mở đầu viết gì",
còn "màn mở đầu dài bao nhiêu frame" là việc của `timeline.py` (P-2).

Ngày tháng do máy suy ra từ tên file kịch bản, không phải gõ tay. Kịch bản tên
`2026-08-20.json` thì màn mở đầu ghi 八月二十日　木曜日 — và thứ trong tuần cũng
tính ra từ chính ngày đó. Gõ tay thứ mấy là kiểu sai mà không ai soi lại: sai
rồi thì phải tự nhớ mới phát hiện, mà chẳng ai nhớ.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

#: Chữ số Nhật cho ngày và tháng. Không dùng 1 2 3 vì màn mở đầu là thư pháp —
#: chữ số Ả Rập lọt vào giữa hàng kanji là gãy hẳn mạch.
_DIGITS = "〇一二三四五六七八九"
_WEEKDAYS = "月火水木金土日"  # datetime: thứ hai = 0


def _kanji_number(n: int) -> str:
    """Số 1–31 sang chữ Nhật: 1 -> 一, 10 -> 十, 20 -> 二十, 24 -> 二十四."""
    if n < 10:
        return _DIGITS[n]
    if n == 10:
        return "十"
    tens, ones = divmod(n, 10)
    head = "十" if tens == 1 else _DIGITS[tens] + "十"
    return head + (_DIGITS[ones] if ones else "")


def japanese_date(day: date) -> str:
    """Ngày kiểu Nhật kèm thứ, cách nhau bằng dấu cách toàn rộng: 八月二十日　木曜日."""
    return (
        f"{_kanji_number(day.month)}月{_kanji_number(day.day)}日"
        f"　{_WEEKDAYS[day.weekday()]}曜日"
    )


def date_from_slug(slug: str) -> date | None:
    """Đọc ngày từ tên kịch bản. Tên không phải dạng ngày thì trả None, không lỗi:
    kịch bản đặt tên tự do vẫn phải dựng được, chỉ là không có dòng ngày."""
    try:
        return date.fromisoformat(slug[:10])
    except ValueError:
        return None


@dataclass(frozen=True)
class Intro:
    """Màn mở đầu đã dựng xong chữ."""

    title: str
    #: Dòng ngày. Rỗng khi tên kịch bản không phải dạng ngày.
    date_text: str
    seconds: float


@dataclass(frozen=True)
class Outro:
    text: str
    seconds: float


def build_intro(spec, slug: str, fallback_title: str) -> Intro | None:
    """Ghép spec trong kịch bản với ngày suy từ slug. Không có spec = không có màn mở đầu."""
    if spec is None:
        return None
    day = date_from_slug(slug)
    return Intro(
        title=spec.title or fallback_title,
        date_text=japanese_date(day) if day else "",
        seconds=spec.seconds,
    )


def build_outro(spec) -> Outro | None:
    if spec is None:
        return None
    return Outro(text=spec.text, seconds=spec.seconds)
