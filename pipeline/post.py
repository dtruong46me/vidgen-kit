"""
Lớp A — dựng chữ cho BÀI ĐĂNG: dòng caption và bộ hashtag.

Module này chỉ sinh CHỮ, giống `intro.py`. Nó không đọc file, không đo gì, không
biết frame là gì. Việc gói ra thư mục là của `export.py`.

Một video còn cần một dòng để dán lên TikTok/Reels/YouTube — dòng đó không nằm
trong video nên trước BƯỚC 7 không có chỗ nào giữ nó, và người đăng phải tự nghĩ
lại mỗi ngày. Giờ nó là trường `caption` trong kịch bản:

    "caption": "🌿 Có nhiều thứ không thể nắm giữ, không phải chuyện gì cũng có kết quả"

Ngày tháng KHÔNG gõ tay — suy từ tên kịch bản, đúng tinh thần P-1. `2026-09-11`
ra `11.09.26`, ghép thành:

    11.09.26 🌿 Có nhiều thứ không thể nắm giữ, không phải chuyện gì cũng có kết quả

Emoji nằm trong chính chuỗi `caption` chứ không phải một trường riêng: mỗi ngày
một chủ đề khác nhau thì emoji cũng khác, mà tách ra thành trường riêng thì chỉ
tổ phải nhớ thứ tự ghép. Người viết nhìn thấy nguyên câu mình sẽ đăng.

`hashtags` thì ngược lại — nó là CÀI ĐẶT, không phải nội dung: kênh nào cũng
dùng một bộ thẻ, đổi một lần là mọi ngày sau theo (`make new` kế thừa nó như
kế thừa giọng đọc và nhạc nền).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

#: Ngày ở đầu caption. `11.09.26` — ngày.tháng.năm hai số, cách viết quen thuộc
#: với người Việt. Đổi ở đây là đổi cho mọi ngày, không phải sửa từng kịch bản.
DATE_FORMAT = "%d.%m.%y"


@dataclass(frozen=True)
class Post:
    """Chữ để đăng, đã ghép xong. Không dính gì tới video."""

    #: Nguyên dòng dán được ngay: "11.09.26 🌿 Có nhiều thứ không thể nắm giữ…"
    caption: str
    #: Phần người viết gõ, chưa có ngày ở đầu. Giữ lại để `metadata.json` nói
    #: được câu nào do người viết, phần nào do máy ghép.
    text: str
    #: "11.09.26"
    date_label: str
    hashtags: tuple[str, ...]
    #: True khi kịch bản không khai `caption` và máy phải mượn câu chốt.
    borrowed: bool

    @property
    def hashtag_line(self) -> str:
        """"#tiengnhat #hoctiengnhat" — rỗng khi không khai thẻ nào."""
        return " ".join(f"#{tag.lstrip('#')}" for tag in self.hashtags)

    @property
    def full(self) -> str:
        """Caption kèm hashtag, cách nhau một dòng trống. Dán thẳng lên TikTok."""
        return f"{self.caption}\n\n{self.hashtag_line}" if self.hashtags else self.caption


def date_label(day: date | None) -> str:
    return day.strftime(DATE_FORMAT) if day is not None else ""


def build(caption: str | None, hashtags: tuple[str, ...], day: date | None,
          fallback: str = "") -> Post:
    """Ghép dòng caption.

    `caption` bỏ trống thì mượn `fallback` — câu tiếng Việt cuối cùng của kịch
    bản, tức lời chúc chốt video. Đó là caption tạm được chứ không hay; cờ
    `borrowed` để `make content` và `make export` nhắc người viết đặt câu riêng.
    """
    text = (caption or "").strip() or fallback.strip()
    label = date_label(day)
    caption_line = f"{label} {text}".strip() if label else text
    return Post(
        caption=caption_line,
        text=text,
        date_label=label,
        hashtags=tuple(hashtags),
        borrowed=not (caption or "").strip(),
    )
