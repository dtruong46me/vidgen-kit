"""
Lớp A — đọc kịch bản người viết và kiểm tra nó trước khi tốn công gọi TTS.

Bản cũ đọc thẳng dict rồi `line["ja"]` giữa vòng lặp: thiếu một trường là vỡ ở
câu thứ bảy, sau khi đã sinh sáu file mp3. Ở đây mọi thứ được kiểm ngay lúc
đọc, nên hỏng là hỏng trước khi chạm vào mạng.

Từ BƯỚC 3, kịch bản KHÔNG còn trường `romaji` — `pipeline/reading.py` sinh ra
nó. Trường `romaji` nếu còn sót lại trong file cũ thì bị bỏ qua, không phải lỗi.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class ScriptError(ValueError):
    """Kịch bản sai hoặc thiếu trường. Thông báo viết cho người đọc, không phải traceback."""


#: Ba kiểu chuyển cảnh. Mặc định là crossfade — đúng bằng hành vi đã có từ
#: trước BƯỚC 5, nên kịch bản cũ không khai gì thì video không đổi một frame nào.
TRANSITIONS = ("crossfade", "dip_to_black", "cut")

#: Mặc định khi kịch bản khai `intro`/`outro` mà không nói dài bao nhiêu.
DEFAULT_INTRO_SECONDS = 4.5
DEFAULT_OUTRO_SECONDS = 3.0
DEFAULT_OUTRO_TEXT = "またあした"
DEFAULT_TRANSITION_SECONDS = 0.8


@dataclass(frozen=True)
class IntroSpec:
    """Khai báo màn mở đầu trong kịch bản. Chữ ngày do máy suy ra (xem intro.py)."""

    #: None thì lấy `title` của cả kịch bản.
    title: str | None
    seconds: float


@dataclass(frozen=True)
class OutroSpec:
    text: str
    seconds: float


@dataclass(frozen=True)
class ScriptLine:
    """Một câu do người viết. Chưa có giọng đọc, chưa có frame."""

    ja: str
    vi: str
    #: Clip nền. Bỏ trống thì `shots.py` tự chọn từ library/shots.json.
    clip: str | None
    clip_start_seconds: float
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
    #: None = không có màn mở đầu / màn kết. Đó là mặc định, và nhờ vậy kịch bản
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
                          f"{{\"title\": \"小さな幸せ\", \"seconds\": 4.5}}.")
    title = raw.get("title")
    if title is not None and not isinstance(title, str):
        raise ScriptError(f"{where} có \"intro.title\" không phải chuỗi.")
    return IntroSpec(
        title=title or None,
        seconds=_seconds(raw.get("seconds"), "intro.seconds", where,
                         DEFAULT_INTRO_SECONDS),
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


def _text(value: object, key: str, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScriptError(f"{where} có \"{key}\" rỗng hoặc không phải chuỗi.")
    return value


def load(content_dir: Path, slug: str) -> Script:
    """Đọc content/<slug>.json thành một Script đã kiểm."""
    src = content_dir / f"{slug}.json"
    if not src.exists():
        raise ScriptError(
            f"Không tìm thấy {src}.\n"
            f"Kịch bản đang có: "
            + (", ".join(sorted(
                p.stem for p in content_dir.glob("*.json")
                if not p.name.endswith(".build.json")
                and not p.name.startswith(".")
            )) or "(chưa có cái nào)")
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
        lines.append(ScriptLine(
            ja=_text(_require(raw, "ja", where), "ja", where),
            vi=raw.get("vi", ""),
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
