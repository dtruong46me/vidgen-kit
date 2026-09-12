"""
Lớp A — đọc kịch bản người viết và kiểm tra nó trước khi tốn công gọi TTS.

Bản cũ đọc thẳng dict rồi `line["ja"]` giữa vòng lặp: thiếu một trường là vỡ ở
câu thứ bảy, sau khi đã sinh sáu file mp3. Ở đây mọi thứ được kiểm ngay lúc
đọc, nên hỏng là hỏng trước khi chạm vào mạng.

Từ BƯỚC 8, kịch bản nằm ở `content/<ngày>/script.json` chứ không còn phẳng ở
`content/<ngày>.json`. Đường dẫn hỏi `paths.py`, module này không tự ghép.

Từ BƯỚC 3, kịch bản KHÔNG còn trường `romaji` — `pipeline/reading.py` sinh ra
nó. Trường `romaji` nếu còn sót lại trong file cũ thì bị bỏ qua, không phải lỗi.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import paths


class ScriptError(ValueError):
    """Kịch bản sai hoặc thiếu trường. Thông báo viết cho người đọc, không phải traceback."""


#: Ba kiểu chuyển cảnh. Mặc định là crossfade — đúng bằng hành vi đã có từ
#: trước BƯỚC 5, nên kịch bản cũ không khai gì thì video không đổi một frame nào.
TRANSITIONS = ("crossfade", "dip_to_black", "cut")

#: Mặc định khi kịch bản khai `intro`/`outro` mà không nói dài bao nhiêu.
#: Khoảng lặng đầu video: tiêu đề ngày hiện lên trên cảnh 1 rồi mới đọc câu 1.
#: 1,5 giây đủ để tiêu đề (vào trong 34 frame) hiện xong trước khi có tiếng.
DEFAULT_INTRO_PAUSE_SECONDS = 1.5
DEFAULT_OUTRO_SECONDS = 3.0
DEFAULT_OUTRO_TEXT = "またあした"
DEFAULT_TRANSITION_SECONDS = 0.8


@dataclass(frozen=True)
class IntroSpec:
    """Khai báo tiêu đề đầu video. Chữ ngày do máy suy ra (xem intro.py).

    Không còn là một cảnh riêng: tiêu đề đè lên cảnh 1, và cảnh 1 lặng thêm
    `pause_seconds` trước khi đọc để tiêu đề kịp hiện.
    """

    #: Chủ đề, hiện nhỏ dưới ngày. None thì lấy `title` của cả kịch bản.
    title: str | None
    pause_seconds: float


@dataclass(frozen=True)
class OutroSpec:
    text: str
    seconds: float


@dataclass(frozen=True)
class ScriptLine:
    """Một câu do người viết. Chưa có giọng đọc, chưa có frame."""

    #: Nguyên câu, đã ghép lại nếu người viết chia sẵn thành nhiều mảnh. Đây là
    #: thứ đem đi ĐỌC và đem đi XUẤT BẢN — giọng đọc phải liền hơi, nên TTS luôn
    #: nhận cả câu chứ không nhận từng mảnh.
    ja: str
    vi: str
    #: Người viết TỰ chia caption thành mấy mảnh, bằng cách viết "ja"/"vi" thành
    #: danh sách. Rỗng = để `phrase.py` tự quyết. Cùng quy ước với `clip`: bỏ
    #: trống thì máy làm hộ, ghi vào thì người viết thắng.
    ja_parts: tuple[str, ...] = ()
    vi_parts: tuple[str, ...] = ()
    #: Clip nền. Bỏ trống thì `shots.py` tự chọn từ library/shots.json.
    clip: str | None = None
    clip_start_seconds: float = 0.0
    #: Gợi ý cho bộ chọn clip: chỉ lấy clip có ít nhất một tag trùng. Bỏ trống
    #: thì dùng `tags` của cả kịch bản; bỏ trống nốt thì clip nào cũng được.
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Script:
    """Một ngày quay. Đúng bằng nội dung content/<slug>.json, đã kiểm."""

    slug: str
    title: str
    fps: int
    width: int
    height: int
    voice: str
    rate: str
    pitch: str
    lead_in: float
    pause_after: float
    bgm: str | None
    bgm_volume: float
    #: Tên provider sinh romaji. Đổi provider = sửa đúng dòng này trong kịch bản.
    reading: str
    #: Tag mặc định cho mọi câu chưa tự khai tag.
    tags: tuple[str, ...]
    #: Dòng để dán lên TikTok/Reels/YouTube, KHÔNG hiện trong video. Ngày tháng
    #: do máy ghép vào đầu (xem post.py), nên ở đây chỉ viết phần chữ. Bỏ trống
    #: thì `export.py` mượn tạm câu tiếng Việt cuối cùng và nhắc đặt câu riêng.
    caption: str | None
    #: Bộ thẻ dán kèm caption. Là CÀI ĐẶT chứ không phải nội dung — kênh nào
    #: cũng một bộ, nên `make new` kế thừa nó như kế thừa giọng đọc.
    hashtags: tuple[str, ...]
    #: None = không có tiêu đề ngày (cảnh 1 cũng không lặng thêm) / không có màn
    #: kết. Đó là mặc định, và nhờ vậy kịch bản
    #: viết trước BƯỚC 5 vẫn ra đúng số frame cũ.
    intro: IntroSpec | None
    outro: OutroSpec | None
    transition: str
    transition_seconds: float
    #: Hiện thêm dòng hiragana dưới romaji hay không. Mặc định TẮT: caption đã
    #: có ba dòng (Nhật, romaji, Việt), dòng thứ tư ép cỡ chữ nhỏ lại và lấn
    #: vào vùng an toàn 380px dưới đáy. Bật lên xem thử rồi tự quyết.
    show_hira: bool
    target_seconds: tuple[float, float] | None
    lines: list[ScriptLine]


def _require(doc: dict, key: str, where: str) -> object:
    if key not in doc:
        raise ScriptError(f"{where} thiếu trường bắt buộc \"{key}\".")
    return doc[key]


def _tags(raw: object, where: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or any(not isinstance(t, str) for t in raw):
        raise ScriptError(f"{where} có \"tags\" phải là danh sách chuỗi.")
    return tuple(raw)


def _seconds(raw: object, key: str, where: str, default: float) -> float:
    if raw is None:
        return default
    if not isinstance(raw, (int, float)) or raw <= 0:
        raise ScriptError(f"{where} có \"{key}\" phải là số giây dương.")
    return float(raw)


def _intro(raw: object, where: str) -> IntroSpec | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ScriptError(f"{where} có \"intro\" phải là object, ví dụ "
                          f"{{\"title\": \"小さな幸せ\", \"pauseSeconds\": 1.5}}.")
    if "seconds" in raw:
        # Bản cũ: màn mở đầu là một cảnh nền gradient dài `seconds` giây. Cảnh
        # đó đã bỏ. Lẳng lặng bỏ qua thì người sửa số này sẽ không hiểu vì sao
        # video không đổi — nên nói thẳng.
        raise ScriptError(
            f"{where} có \"intro.seconds\" — trường này đã bỏ cùng màn mở đầu nền "
            f"gradient. Tiêu đề giờ hiện trên cảnh 1; đổi thành \"pauseSeconds\" "
            f"(khoảng lặng trước câu 1, mặc định {DEFAULT_INTRO_PAUSE_SECONDS:g})."
        )
    title = raw.get("title")
    if title is not None and not isinstance(title, str):
        raise ScriptError(f"{where} có \"intro.title\" không phải chuỗi.")
    return IntroSpec(
        title=title or None,
        pause_seconds=_seconds(raw.get("pauseSeconds"), "intro.pauseSeconds",
                               where, DEFAULT_INTRO_PAUSE_SECONDS),
    )


def _outro(raw: object, where: str) -> OutroSpec | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ScriptError(f"{where} có \"outro\" phải là object, ví dụ "
                          f"{{\"text\": \"またあした\", \"seconds\": 3}}.")
    text = raw.get("text", DEFAULT_OUTRO_TEXT)
    if not isinstance(text, str) or not text.strip():
        raise ScriptError(f"{where} có \"outro.text\" rỗng hoặc không phải chuỗi.")
    return OutroSpec(
        text=text,
        seconds=_seconds(raw.get("seconds"), "outro.seconds", where,
                         DEFAULT_OUTRO_SECONDS),
    )


def _transition(raw: object, where: str) -> str:
    if raw is None:
        return "crossfade"
    if raw not in TRANSITIONS:
        raise ScriptError(
            f"{where} có \"transition\" là \"{raw}\", không có kiểu đó. "
            f"Chỉ có: {', '.join(TRANSITIONS)}."
        )
    return raw


def _caption(raw: object, where: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise ScriptError(
            f"{where} có \"caption\" phải là chuỗi, ví dụ "
            f"\"🌿 Có nhiều thứ không thể nắm giữ\". Đừng gõ ngày vào đây — "
            f"máy ghép ngày từ tên kịch bản."
        )
    return raw.strip() or None


def _text(value: object, key: str, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScriptError(f"{where} có \"{key}\" rỗng hoặc không phải chuỗi.")
    return value


def _parts(value: object, key: str, where: str, joiner: str) -> tuple[str, tuple[str, ...]]:
    """Đọc "ja"/"vi" — một chuỗi, hoặc một danh sách mảnh caption.

    Trả về `(nguyên câu, các mảnh)`. Chuỗi thì mảnh rỗng, tức để `phrase.py` tự
    quyết cắt hay không. Danh sách là người viết đã tự chia, và người viết thắng.

    Nguyên câu luôn được ghép lại từ các mảnh, vì TTS đọc CẢ CÂU: chia caption
    không được làm giọng đọc đứt hơi giữa chừng.
    """
    if isinstance(value, list):
        if not value or any(not isinstance(x, str) or not x.strip() for x in value):
            raise ScriptError(
                f"{where} có \"{key}\" là danh sách rỗng hoặc có mảnh rỗng. "
                f"Viết chuỗi để máy tự cắt, hoặc danh sách các mảnh caption."
            )
        parts = tuple(x.strip() for x in value)
        return joiner.join(parts), parts
    return _text(value, key, where), ()


def load(content_dir: Path, slug: str) -> Script:
    """Đọc content/<slug>.json thành một Script đã kiểm."""
    src = paths.script_path(slug, content_dir)
    if not src.exists():
        # Bố cục cũ để file phẳng ở content/<slug>.json. Không đọc lẳng lặng:
        # hai bố cục cùng sống thì không ai biết file nào đang được dùng.
        if paths.legacy_script(slug, content_dir) is not None:
            raise ScriptError(paths.move_hint(slug, content_dir))
        raise ScriptError(
            f"Không tìm thấy {src}.\n"
            f"Kịch bản đang có: "
            + (", ".join(paths.slugs(content_dir)) or "(chưa có cái nào)")
        )

    try:
        doc = json.loads(src.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScriptError(f"{src} không phải JSON hợp lệ: {exc}") from exc

    raw_lines = _require(doc, "lines", src.name)
    if not isinstance(raw_lines, list) or not raw_lines:
        raise ScriptError(f"{src.name} phải có ít nhất một câu trong \"lines\".")

    lines = []
    for i, raw in enumerate(raw_lines, start=1):
        where = f"{src.name} câu {i}"
        if not isinstance(raw, dict):
            raise ScriptError(f"{where} không phải object.")
        clip = raw.get("clip")
        if clip is not None and not isinstance(clip, str):
            raise ScriptError(f"{where} có \"clip\" không phải đường dẫn.")
        start = raw.get("clipStartInSeconds", 0)
        if not isinstance(start, (int, float)) or start < 0:
            raise ScriptError(f"{where} có \"clipStartInSeconds\" âm hoặc không phải số.")
        ja, ja_parts = _parts(_require(raw, "ja", where), "ja", where, "")
        raw_vi = raw.get("vi", "")
        vi, vi_parts = (
            _parts(raw_vi, "vi", where, " ") if raw_vi else ("", ())
        )
        if ja_parts and len(vi_parts) != len(ja_parts) and vi:
            # Hai bên hiện cùng lúc trên một khung caption. Lệch số mảnh thì
            # không có cách nào ghép đúng, và đoán bừa là dịch sai chỗ.
            raise ScriptError(
                f"{where} chia \"ja\" làm {len(ja_parts)} mảnh nhưng \"vi\" "
                f"làm {len(vi_parts) or 1} mảnh. Chia \"vi\" thành đúng "
                f"{len(ja_parts)} mảnh, hoặc để cả hai là chuỗi cho máy tự cắt."
            )
        lines.append(ScriptLine(
            ja=ja,
            vi=vi,
            ja_parts=ja_parts,
            vi_parts=vi_parts,
            clip=clip or None,
            clip_start_seconds=float(start),
            tags=_tags(raw.get("tags"), where),
        ))

    target = doc.get("targetSeconds")
    if target is not None:
        if not (isinstance(target, list) and len(target) == 2):
            raise ScriptError(f"{src.name} có \"targetSeconds\" phải là [thấp, cao].")
        target = (float(target[0]), float(target[1]))

    return Script(
        slug=_text(_require(doc, "id", src.name), "id", src.name),
        title=doc.get("title") or doc["id"],
        fps=int(doc.get("fps", 30)),
        width=int(doc.get("width", 1080)),
        height=int(doc.get("height", 1920)),
        voice=doc.get("voice", "ja-JP-NanamiNeural"),
        rate=doc.get("rate", "+0%"),
        pitch=doc.get("pitch", "+0Hz"),
        lead_in=float(doc.get("leadIn", 0.35)),
        pause_after=float(doc.get("pauseAfter", 0.7)),
        bgm=doc.get("bgm") or None,
        bgm_volume=float(doc.get("bgmVolume", 0.12)),
        reading=doc.get("reading", "cutlet"),
        tags=_tags(doc.get("tags"), src.name),
        caption=_caption(doc.get("caption"), src.name),
        hashtags=_tags(doc.get("hashtags"), src.name),
        intro=_intro(doc.get("intro"), src.name),
        outro=_outro(doc.get("outro"), src.name),
        transition=_transition(doc.get("transition"), src.name),
        transition_seconds=_seconds(
            doc.get("transitionSeconds"), "transitionSeconds", src.name,
            DEFAULT_TRANSITION_SECONDS,
        ),
        show_hira=bool(doc.get("showHira", False)),
        target_seconds=target,
        lines=lines,
    )
