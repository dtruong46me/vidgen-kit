"""
Lớp A — dựng chữ cho BÀI ĐĂNG: dòng caption và bộ hashtag.

Module này chỉ sinh CHỮ, giống `intro.py`. Nó không đọc file, không đo gì, không
biết frame là gì. Việc gói ra thư mục là của `export.py`.

Một video còn cần một dòng để dán lên TikTok/Reels/YouTube — dòng đó không nằm
trong video nên trước BƯỚC 7 không có chỗ nào giữ nó, và người đăng phải tự nghĩ
lại mỗi ngày. Giờ nó là trường `caption` trong kịch bản, và người viết CHỈ viết
câu chữ:

    "caption": "Có nhiều thứ không thể nắm giữ, không phải chuyện gì cũng có kết quả"

Máy ghép hai thứ vào đầu:

    11.09.26 🌿 Có nhiều thứ không thể nắm giữ, không phải chuyện gì cũng có kết quả

- Ngày tháng suy từ tên kịch bản, đúng tinh thần P-1: `2026-09-11` ra `11.09.26`.
- Emoji là MỘT cái cho mọi ngày (`EMOJI`). Bản trước để người viết tự chọn emoji
  hợp chủ đề từng ngày ngay trong chuỗi caption — 🍵, 🌅, 🪵… — nên lướt trang
  kênh thì mỗi bài một kiểu, không ra một kênh. Giờ nó là dấu nhận diện, cùng
  loại với định dạng ngày: đổi ở đây là đổi cho mọi ngày. Kịch bản còn để emoji
  ở đầu caption thì máy bỏ nó đi (`make content` nhắc một dòng), chứ không in
  hai emoji liền nhau.

`hashtags` thì ngược lại — nó là CÀI ĐẶT, không phải nội dung: kênh nào cũng
dùng một bộ thẻ, đổi một lần là mọi ngày sau theo (`make new` kế thừa nó như
kế thừa giọng đọc và nhạc nền).
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date

#: Ngày ở đầu caption. `11.09.26` — ngày.tháng.năm hai số, cách viết quen thuộc
#: với người Việt. Đổi ở đây là đổi cho mọi ngày, không phải sửa từng kịch bản.
DATE_FORMAT = "%d.%m.%y"

#: Emoji giữa ngày và câu caption — MỘT cái cho mọi ngày. Là dấu nhận diện của
#: kênh, không phải hình minh hoạ chủ đề từng ngày. Đổi ở đây là đổi cho mọi ngày.
EMOJI = "🌿"

#: Mảnh ghép không hiện hình của emoji: U+FE0F (bản emoji của ký hiệu, như ☁️)
#: và U+200D (nối nhiều emoji thành một).
_JOINERS = "️‍"


@dataclass(frozen=True)
class Post:
    """Chữ để đăng, đã ghép xong. Không dính gì tới video."""

    #: Nguyên dòng dán được ngay: "11.09.26 🌿 Có nhiều thứ không thể nắm giữ…"
    caption: str
    #: Phần người viết gõ, chưa có ngày và emoji ở đầu. Giữ lại để
    #: `metadata.json` nói được câu nào do người viết, phần nào do máy ghép.
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


def _split_emoji(text: str) -> tuple[str, str]:
    """Tách (emoji ở đầu, phần chữ còn lại).

    Nhận diện theo NHÓM Unicode chứ không theo danh sách emoji: emoji là ký hiệu
    `So`, tông da là `Sk`, cộng hai mảnh ghép trong `_JOINERS`. Chữ Việt, chữ số
    và dấu câu không thuộc mấy nhóm đó, nên câu chữ không bao giờ bị cắt nhầm.
    """
    i = 0
    while i < len(text) and (
        text[i].isspace() or text[i] in _JOINERS
        or unicodedata.category(text[i]) in ("So", "Sk")
    ):
        i += 1
    return text[:i].strip(), text[i:].strip()


def leading_emoji(caption: str | None) -> str:
    """Emoji người viết để ở đầu caption — thứ máy sẽ bỏ đi. Rỗng nếu không có."""
    return _split_emoji(caption or "")[0]


def build(caption: str | None, hashtags: tuple[str, ...], day: date | None,
          fallback: str = "") -> Post:
    """Ghép dòng caption: ngày, `EMOJI`, rồi câu chữ.

    `caption` bỏ trống thì mượn `fallback` — câu tiếng Việt cuối cùng của kịch
    bản, tức lời chúc chốt video. Đó là caption tạm được chứ không hay; cờ
    `borrowed` để `make content` và `make export` nhắc người viết đặt câu riêng.
    """
    _, own = _split_emoji((caption or "").strip())
    text = own or fallback.strip()
    label = date_label(day)
    return Post(
        caption=" ".join(part for part in (label, EMOJI, text) if part),
        text=text,
        date_label=label,
        hashtags=tuple(hashtags),
        borrowed=not own,
    )
