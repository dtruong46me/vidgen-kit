"""
Lớp A — CHỖ DUY NHẤT biết cắt một câu dài thành mấy mảnh caption.

Vấn đề nó giải: một câu như

    毎日の生活は、同じことの繰り返しに見えるけれど、小さな変化が、きっとどこかにあります。

dài 43 chữ. Nhét cả câu vào một khung caption thì chỉ còn hai đường: hoặc tràn
khung, hoặc bóp cỡ chữ nhỏ lại. Bản cũ chọn đường thứ hai, nên cảnh nào câu dài
là cảnh đó chữ nhỏ hơn hẳn các cảnh khác — người xem thấy cỡ chữ nhảy qua nhảy
lại suốt video.

Đường thứ ba là cắt câu ra: cắt ở 「けれど、」 rồi cho nửa sau hiện tiếp TRONG
CÙNG MỘT CẢNH. Vẫn một file giọng đọc, vẫn một clip nền, frame chạy tiếp — chỉ
có chữ là đổi. Nhờ vậy mảnh nào cũng ngắn, và cỡ chữ không phải co lại bao giờ.

    |<------------------ MỘT cảnh, MỘT clip, MỘT file mp3 ------------------>|
    | 毎日の生活は、同じことの繰り返しに見えるけれど、| 小さな変化が、きっとどこかにあります。|
                                                 ^
                                    đổi chữ ở đây, không cắt cảnh

**Cắt ở đâu là việc của module này; cắt vào frame thứ mấy là việc của
`timeline.py` (P-2).** Ở đây chỉ có chữ và số ký tự, không có một phép nhân fps
nào.

Ở đây có HAI cặp ngưỡng, và lẫn chúng với nhau là hỏng cả hai việc:

    JA_MAX / VI_MAX    bao nhiêu chữ thì ĐỌC MỘT MÀN là vừa    -> quyết cắt hay không
    JA_FIT / VI_FIT    bao nhiêu chữ thì CÒN VỪA cỡ chữ chuẩn  -> quyết có kêu hay không

Cặp đầu chặt hơn cặp sau, cố ý. Nhờ khoảng đệm đó, câu nào không cắt được (bản
dịch không có dấu ngắt nào) thì vẫn hiện nguyên ở đúng cỡ chữ như mọi cảnh khác
— chỉ là một màn chữ hơi dày. Chỉ khi vượt luôn cặp sau thì `Caption.tsx` mới
phải co chữ lại, và ĐÓ mới là lúc đáng kêu: cảnh nào chữ nhỏ hơn các cảnh khác
là người xem thấy ngay.

Cặp sau phải khớp với thang cỡ chữ trong `studio/src/Caption.tsx` — nó là chỗ
chữ bắt đầu phải xuống dòng thứ ba. Đổi một bên thì đổi cả bên kia.

Đo trên 286 câu đang có: 6 câu được cắt, 0 câu phải co chữ. Nên đây là van an
toàn cho câu cá biệt, không phải thứ bổ đôi mọi câu.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

#: Dài hơn thế này thì CẮT. Không phải vì tràn khung, mà vì một màn chữ dày quá
#: thì người xem đọc không kịp trong khi giọng đọc đã đi tiếp.
JA_MAX = 24
VI_MAX = 60

#: Dài hơn thế này thì `Caption.tsx` buộc phải co chữ — đây là chỗ chữ xuống
#: dòng thứ ba. 860px bề ngang dùng được: chữ Nhật cỡ 56 + letterSpacing 1 ra
#: 15 chữ một dòng, chữ Việt cỡ 38 rộng trung bình nửa em ra ~45 ký tự một dòng.
JA_FIT = 30
VI_FIT = 88

#: Cắt câu Nhật SAU các dấu này. Toàn dấu ngắt ý, nên cắt ở đây là cắt đúng chỗ
#: người đọc vốn đã nghỉ hơi — mà giọng đọc cũng nghỉ ở đúng đó.
JA_BREAKS = "、。！？"

#: Dấu ngắt của tiếng Việt. Có cả dấu chấm vì bản dịch hay tách thành hai câu
#: ngắn trong khi bản tiếng Nhật chỉ là một câu.
VI_BREAKS = ",;.:!?"

#: Không cắt ra mảnh cụt lủn. Một mảnh 3 chữ hiện lên rồi biến mất ngay đọc ra
#: là giật, chứ không ra thong thả.
JA_MIN = 6
VI_MIN = 12


@dataclass(frozen=True)
class Part:
    """Một mảnh caption: câu Nhật và bản dịch của CHÍNH mảnh đó."""

    ja: str
    vi: str


def _break_points(text: str, marks: str, min_len: int) -> list[int]:
    """Các chỗ cắt được, tính bằng chỉ số ký tự BẮT ĐẦU mảnh sau.

    Cắt ngay SAU dấu, để dấu phẩy ở lại cuối mảnh trước — nó chính là thứ báo
    cho người xem biết câu còn chưa hết.
    """
    points = []
    for i, ch in enumerate(text):
        if ch not in marks:
            continue
        # Nuốt luôn khoảng trắng sau dấu: mảnh sau không nên mở đầu bằng dấu cách.
        j = i + 1
        while j < len(text) and text[j] == " ":
            j += 1
        if min_len <= j <= len(text) - min_len:
            points.append(j)
    return points


def _cut(text: str, points: list[int], n: int) -> list[str] | None:
    """Cắt `text` thành đúng `n` mảnh, chọn cách cân nhất. None = không đủ chỗ cắt."""
    if n <= 1:
        return [text]
    if len(points) < n - 1:
        return None

    best = None
    for combo in combinations(points, n - 1):
        edges = (0, *combo, len(text))
        parts = [text[a:b].strip() for a, b in zip(edges, edges[1:])]
        if any(not p for p in parts):
            continue
        # Cân = mảnh dài nhất càng ngắn càng tốt. Cùng điểm thì lấy cách có
        # tổng chênh lệch nhỏ hơn, để "20+20" thắng "20+12+... " đều nhau hơn.
        score = (max(map(len, parts)), max(map(len, parts)) - min(map(len, parts)))
        if best is None or score < best[0]:
            best = (score, parts)
    return best[1] if best else None


def _parts_needed(text: str, points: list[int], max_len: int) -> int:
    """Ít nhất mấy mảnh thì mảnh nào cũng dưới ngưỡng. Cắt hết cỡ vẫn quá thì trả về số mảnh tối đa."""
    for n in range(1, len(points) + 2):
        parts = _cut(text, points, n)
        if parts is not None and max(map(len, parts)) <= max_len:
            return n
    return len(points) + 1


def split(ja: str, vi: str) -> tuple[list[Part], str | None]:
    """Cắt một câu thành các mảnh caption.

    Trả về `(mảnh, lời kêu)`. Một mảnh duy nhất tức là câu vốn đã vừa khung —
    đó là trường hợp thường gặp và nó ra đúng hành vi cũ, không lệch một frame.

    `lời kêu` khác None khi câu quá dài mà KHÔNG cắt được: hoặc không có dấu
    ngắt nào, hoặc bản dịch không có đủ dấu để chia làm bấy nhiêu mảnh. Lúc đó
    câu giữ nguyên và cỡ chữ đành co lại — nói thẳng ra, đừng để người viết tự
    phát hiện bằng cách xem video.
    """
    ja_points = _break_points(ja, JA_BREAKS, JA_MIN)
    vi_points = _break_points(vi, VI_BREAKS, VI_MIN) if vi else []

    n = max(
        _parts_needed(ja, ja_points, JA_MAX),
        _parts_needed(vi, vi_points, VI_MAX) if vi else 1,
    )
    whole = [Part(ja=ja, vi=vi)]
    if n <= 1:
        # Hoặc câu vốn đã vừa khung — trường hợp thường gặp, và nó ra đúng hành
        # vi cũ. Hoặc câu quá dài mà KHÔNG có lấy một dấu ngắt nào, nên `n` vẫn
        # là 1: lúc đó `_overflow` phải kêu, đừng để nó lọt qua vì `n` nhỏ.
        return whole, _overflow(whole)

    ja_parts = _cut(ja, ja_points, n)
    vi_parts = _cut(vi, vi_points, n) if vi else [""] * n

    if ja_parts is None or vi_parts is None:
        # Không đủ dấu ngắt ở một trong hai bên. Giữ nguyên câu — và chỉ kêu nếu
        # nguyên câu thật sự làm co chữ. Dưới ngưỡng FIT thì một màn chữ hơi
        # dày là hết chuyện, không đáng làm người viết lo.
        return whole, _overflow(whole)

    parts = [Part(ja=a, vi=b) for a, b in zip(ja_parts, vi_parts)]
    return parts, _overflow(parts)


def _overflow(parts: list[Part]) -> str | None:
    """Màn chữ nào còn quá ngưỡng CỠ CHỮ thì nói ra. None = màn nào cũng vừa.

    Chỉ kêu ở đây, không kêu ở chỗ "không cắt được": không cắt được mà vẫn vừa
    cỡ chữ thì chẳng có gì hỏng, và kêu bừa thì vài lần sau người ta thôi đọc.
    """
    over = [
        (i, p) for i, p in enumerate(parts, start=1)
        if len(p.ja) > JA_FIT or len(p.vi) > VI_FIT
    ]
    if not over:
        return None
    cho = (
        ", ".join(f"mảnh {i} ({len(p.ja)} chữ / {len(p.vi)} ký tự)" for i, p in over)
        if len(parts) > 1
        else f"dài {len(parts[0].ja)} chữ / {len(parts[0].vi)} ký tự"
    )
    return (
        f"{cho} mà không có đủ dấu ngắt để cắt nhỏ ra. "
        f"CỠ CHỮ CẢNH NÀY SẼ NHỎ HƠN các cảnh khác. Thêm dấu phẩy vào chỗ ngắt ý, "
        f"hoặc tự chia bằng cách viết \"ja\"/\"vi\" thành danh sách."
    )


def from_lists(ja_parts: tuple[str, ...], vi_parts: tuple[str, ...]) -> tuple[list[Part], str | None]:
    """Người viết tự chia sẵn. Người viết luôn thắng máy — chỉ kiểm số mảnh có khớp."""
    if len(vi_parts) not in (0, len(ja_parts)):
        return [], (
            f"\"ja\" chia làm {len(ja_parts)} mảnh nhưng \"vi\" chia làm "
            f"{len(vi_parts)} mảnh. Hai bên hiện cùng lúc nên phải bằng nhau."
        )
    vi = vi_parts or ("",) * len(ja_parts)
    return [Part(ja=a, vi=b) for a, b in zip(ja_parts, vi)], None
