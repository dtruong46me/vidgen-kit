"""
Lớp A — dựng chữ cho tiêu đề đầu video và màn kết.

Module này chỉ sinh CHỮ, không sinh frame. Nó trả lời "tiêu đề viết gì", còn
"lặng bao nhiêu frame trước câu 1" là việc của `timeline.py` (P-2).

Tiêu đề không còn là một cảnh riêng trên nền gradient. Nó hiện đè lên cảnh 1,
ở khoảng 1/4 khung hình từ trên xuống, và câu 1 được đọc sau một khoảng lặng
ngắn — video vào thẳng hình thật ngay từ frame đầu tiên.

Ngày tháng do máy suy ra từ tên file kịch bản, không phải gõ tay. Kịch bản tên
`2026-08-20.json` thì tiêu đề là 8月20日 — viết đúng như trong câu đọc
「今日は、8月20日です。」, để chữ trên màn hình và tiếng đọc là cùng một thứ.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


def title_date(day: date) -> str:
    """Ngày làm tiêu đề: 8月20日."""
    return f"{day.month}月{day.day}日"


def date_from_slug(slug: str) -> date | None:
    """Đọc ngày từ tên kịch bản. Tên không phải dạng ngày thì trả None, không lỗi:
    kịch bản đặt tên tự do vẫn phải dựng được, chỉ là tiêu đề không có ngày."""
    try:
        return date.fromisoformat(slug[:10])
    except ValueError:
        return None


@dataclass(frozen=True)
class TitleCard:
    """Tiêu đề đầu video đã dựng xong chữ. Khoảng lặng đi kèm nằm ở script.intro."""

    #: Chữ to: ngày tháng. Tên kịch bản không phải ngày thì là chủ đề.
    title: str
    #: Chữ nhỏ dưới tiêu đề: chủ đề của ngày. Rỗng khi chủ đề đã lên làm tiêu đề.
    subtitle: str


@dataclass(frozen=True)
class Outro:
    text: str
    seconds: float


def build_intro(spec, slug: str, fallback_title: str) -> TitleCard | None:
    """Ghép spec trong kịch bản với ngày suy từ slug. Không có spec = không có tiêu đề."""
    if spec is None:
        return None
    theme = spec.title or fallback_title
    day = date_from_slug(slug)
    if day is None:
        return TitleCard(title=theme, subtitle="")
    return TitleCard(title=title_date(day), subtitle=theme)


def build_outro(spec) -> Outro | None:
    if spec is None:
        return None
    return Outro(text=spec.text, seconds=spec.seconds)
