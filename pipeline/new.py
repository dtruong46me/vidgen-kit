"""
Lớp A — tạo kịch bản cho một ngày mới: `content/<ngày>.json`.

    python3 -m pipeline.new 2026-09-10          có khoá thì nhờ Claude, không thì lấy ngân hàng
    python3 -m pipeline.new 2026-09-10 bank     luôn lấy từ ngân hàng, dù có khoá
    python3 -m pipeline.new 2026-09-10 sonnet   gọi Claude Sonnet (opus / sonnet / haiku)
    python3 -m pipeline.new --bank              in ngân hàng kèm ước lượng thời lượng

Kịch bản gồm hai phần tách bạch:

  NỘI DUNG  chủ đề, tag, các câu      ← lấy từ ngân hàng hoặc từ Claude
  CÀI ĐẶT   giọng, nhạc, nhịp, màn kết ← kế thừa từ kịch bản gần nhất

Nhờ vậy chỉnh giọng đọc hay đổi nhạc nền ở một ngày là mọi ngày sau tự theo,
không phải sửa ngân hàng, không phải sửa prompt.

File sinh ra là file NGƯỜI VIẾT — nó được commit, và bạn sửa thoải mái trước khi
`make content`. Vì vậy lệnh này không bao giờ đè lên kịch bản đã có.

Trường `clip` bỏ trống: `shots.py` chọn clip sau khi TTS đo xong độ dài từng câu.
Trường `source` ghi kịch bản từ đâu ra; `script.py` bỏ qua nó, còn lệnh này đọc
nó để không lấy lại một mục ngân hàng vừa dùng.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import env, library as library_mod, script as script_mod
from .intro import date_from_slug

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
BANK_PATH = ROOT / "library" / "bank.json"

#: Tốc độ đọc của edge-tts giọng Nanami, tính bằng chữ Nhật mỗi giây (không tính
#: dấu câu). Đo trên 2026-08-20: 166 chữ ra 39,27 giây audio.
#:
#: Chỉ dùng để ƯỚC LƯỢNG trước khi tốn công TTS. Con số thật vẫn do ffprobe đo
#: trên file mp3 (P-1) — `make content` in ra và cảnh báo nếu lệch khoảng.
CHARS_PER_SECOND = 4.23

#: Số câu nên có. 9 câu là nhịp của 2026-08-20; ít hơn 8 thì mỗi câu phải dài,
#: nhiều hơn 10 thì cảnh đổi quá dồn.
LINES_RANGE = (8, 10)

#: Câu dài hơn thế này thì phụ đề tiếng Nhật xuống ba dòng và đè lên romaji.
#: Câu dài nhất từng dựng ổn là 39 chữ (câu 5 của 2026-08-20).
MAX_LINE_CHARS = 40

#: Đưa bao nhiêu ngày gần nhất vào prompt để tránh lặp ý (chỉ khi dùng Claude).
RECENT_DAYS = 7

#: Không nhắm sát mép khoảng targetSeconds: ước lượng lệch vài giây là chuyện
#: thường, nên chừa mỗi đầu ngần này giây.
TARGET_MARGIN = 2.0

#: Trường thuộc về NỘI DUNG — không kế thừa từ ngày trước.
CONTENT_KEYS = ("id", "title", "tags", "lines", "source")

#: Cài đặt khi chưa có kịch bản nào để kế thừa. Đúng bằng cài đặt của 2026-08-20.
DEFAULT_SETTINGS = {
    "voice": "ja-JP-NanamiNeural",
    "rate": "+0%",
    "pitch": "+0Hz",
    "bgm": "audio/bgm-lonely-self.mp3",
    "bgmVolume": 0.12,
    "fps": 30,
    "width": 1080,
    "height": 1920,
    "leadIn": 0.35,
    "pauseAfter": 0.7,
    "intro": {"seconds": script_mod.DEFAULT_INTRO_SECONDS},
    "outro": {"text": script_mod.DEFAULT_OUTRO_TEXT,
              "seconds": script_mod.DEFAULT_OUTRO_SECONDS},
    "targetSeconds": [45, 60],
    "transition": "crossfade",
}

_NOT_SPOKEN = re.compile(r"[\s、。，,．！!？?「」『』（）()・…]")


class NewError(ValueError):
    """Không tạo được kịch bản. Thông báo viết cho người đọc, không phải traceback."""


@dataclass(frozen=True)
class Draft:
    """Phần nội dung của một ngày, chưa ghép cài đặt."""

    theme: str
    tags: tuple[str, ...]
    lines: list[dict]
    source: dict


# --------------------------------------------------------------------------
# Đọc những gì đã có
# --------------------------------------------------------------------------

def _scripts(content_dir: Path) -> list[tuple[str, dict]]:
    """Mọi kịch bản người viết, xếp theo tên (tức theo ngày)."""
    out = []
    for path in sorted(content_dir.glob("*.json")):
        if path.name.endswith(".build.json") or path.name.startswith("."):
            continue
        try:
            out.append((path.stem, json.loads(path.read_text(encoding="utf-8"))))
        except json.JSONDecodeError as exc:
            raise NewError(f"{path.name} không phải JSON hợp lệ: {exc}") from exc
    return out


def _template(scripts: list[tuple[str, dict]], slug: str) -> tuple[str | None, dict]:
    """Cài đặt của ngày gần nhất TRƯỚC ngày cần tạo (hoặc ngày mới nhất nếu không có)."""
    earlier = [row for row in scripts if row[0] < slug] or scripts
    if not earlier:
        return None, dict(DEFAULT_SETTINGS)
    name, doc = earlier[-1]
    return name, {k: v for k, v in doc.items() if k not in CONTENT_KEYS}


def load_bank(path: Path = BANK_PATH) -> list[dict]:
    """Đọc và kiểm ngân hàng. Hỏng ở mục nào thì nói đúng mục đó."""
    if not path.exists():
        raise NewError(f"Không có {path.relative_to(ROOT)} — ngân hàng kịch bản trống.")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NewError(f"{path.name} không phải JSON hợp lệ: {exc}") from exc

    entries = doc.get("scripts")
    if not isinstance(entries, list) or not entries:
        raise NewError(f"{path.name} phải có ít nhất một mục trong \"scripts\".")

    seen = set()
    for i, entry in enumerate(entries, start=1):
        where = f"{path.name} mục {i}"
        if not isinstance(entry, dict):
            raise NewError(f"{where} không phải object.")
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            raise NewError(f"{where} thiếu \"id\".")
        where = f"{path.name} mục \"{entry_id}\""
        if entry_id in seen:
            raise NewError(f"{where} bị trùng id.")
        seen.add(entry_id)
        if not isinstance(entry.get("theme"), str) or not entry["theme"].strip():
            raise NewError(f"{where} thiếu \"theme\".")
        tags = entry.get("tags", [])
        if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
            raise NewError(f"{where} có \"tags\" phải là danh sách chuỗi.")
        lines = entry.get("lines")
        if not isinstance(lines, list) or not lines:
            raise NewError(f"{where} phải có ít nhất một câu.")
        for n, line in enumerate(lines, start=1):
            if (not isinstance(line, dict) or not isinstance(line.get("ja"), str)
                    or not line["ja"].strip() or not isinstance(line.get("vi"), str)):
                raise NewError(f"{where} câu {n} phải có \"ja\" và \"vi\" là chuỗi.")
    return entries


def _bank_usage(scripts: list[tuple[str, dict]]) -> dict[str, str]:
    """Mục ngân hàng nào đã dùng, và dùng lần cuối ở ngày nào."""
    used: dict[str, str] = {}
    for slug, doc in scripts:
        source = doc.get("source")
        if isinstance(source, dict) and source.get("writer") == "bank" and source.get("id"):
            used[source["id"]] = max(slug, used.get(source["id"], ""))
    return used


# --------------------------------------------------------------------------
# Ước lượng độ dài — trước TTS, nên chỉ là ước lượng
# --------------------------------------------------------------------------

def spoken_chars(text: str) -> int:
    """Số chữ được đọc thành tiếng: bỏ dấu câu và khoảng trắng."""
    return len(_NOT_SPOKEN.sub("", text))


def _fixed_seconds(settings: dict, n_lines: int) -> float:
    """Phần thời lượng không phụ thuộc số chữ: nghỉ giữa câu, mở đầu, kết.

    Mặc định lấy đúng mặc định của script.py, để ước lượng khớp với cái mà
    `make content` sẽ thật sự dựng.
    """
    gap = float(settings.get("leadIn", 0.35)) + float(settings.get("pauseAfter", 0.7))
    intro = settings.get("intro")
    outro = settings.get("outro")
    return (
        n_lines * gap
        + (float(intro.get("seconds", script_mod.DEFAULT_INTRO_SECONDS))
           if isinstance(intro, dict) else 0.0)
        + (float(outro.get("seconds", script_mod.DEFAULT_OUTRO_SECONDS))
           if isinstance(outro, dict) else 0.0)
    )


def estimate_seconds(lines: list[dict], settings: dict) -> float:
    chars = sum(spoken_chars(line["ja"]) for line in lines)
    return chars / CHARS_PER_SECOND + _fixed_seconds(settings, len(lines))


def _target(settings: dict) -> tuple[float, float]:
    raw = settings.get("targetSeconds") or DEFAULT_SETTINGS["targetSeconds"]
    return float(raw[0]), float(raw[1])


def char_budget(settings: dict) -> tuple[int, int]:
    """Tổng số chữ nên có để video rơi vào khoảng targetSeconds, tính cho 9 câu."""
    lo, hi = _target(settings)
    fixed = _fixed_seconds(settings, sum(LINES_RANGE) // 2)
    return (
        max(0, round((lo + TARGET_MARGIN - fixed) * CHARS_PER_SECOND)),
        max(0, round((hi - TARGET_MARGIN - fixed) * CHARS_PER_SECOND)),
    )


# --------------------------------------------------------------------------
# Hai nguồn nội dung
# --------------------------------------------------------------------------

def _fill_date(text: str, day: date) -> str:
    return (text
            .replace("{date_vi}", f"ngày {day.day} tháng {day.month}")
            .replace("{date}", f"{day.month}月{day.day}日"))


def _from_bank(day: date, scripts: list[tuple[str, dict]]) -> Draft:
    """Mục chưa dùng đầu tiên; dùng hết thì mục dùng lâu nhất. Tất định, không random."""
    bank = load_bank()
    used = _bank_usage(scripts)
    fresh = [entry for entry in bank if entry["id"] not in used]
    if fresh:
        entry = fresh[0]
    else:
        order = {entry["id"]: i for i, entry in enumerate(bank)}
        entry = min(bank, key=lambda e: (used[e["id"]], order[e["id"]]))

    lines = []
    for raw in entry["lines"]:
        line = {"ja": _fill_date(raw["ja"], day), "vi": _fill_date(raw["vi"], day)}
        if raw.get("tags"):
            line["tags"] = list(raw["tags"])
        lines.append(line)
    return Draft(
        theme=entry["theme"],
        tags=tuple(entry.get("tags", [])),
        lines=lines,
        source={"writer": "bank", "id": entry["id"]},
    )


def _library_tags() -> tuple[str, ...]:
    """Mọi tag clip đang có, theo thứ tự xuất hiện trong sổ."""
    seen: dict[str, None] = {}
    for shot in library_mod.load().shots:
        for tag in shot.tags:
            seen.setdefault(tag, None)
    return tuple(seen)


def _from_llm(model: str | None, day: date, slug: str,
              scripts: list[tuple[str, dict]], settings: dict, log) -> Draft:
    # Nạp muộn: không dùng LLM thì không cần llm.py, cũng không cần thư viện anthropic.
    try:
        from . import llm
    except ImportError as exc:
        raise NewError(
            "Không nạp được pipeline/llm.py. Dùng `make new MODEL=bank` để lấy "
            "từ ngân hàng kịch bản."
        ) from exc

    earlier = [doc for name, doc in scripts if name < slug][-RECENT_DAYS:]
    brief = llm.Brief(
        day=day,
        chars=char_budget(settings),
        lines=LINES_RANGE,
        tags=_library_tags(),
        recent=tuple(line["ja"] for doc in earlier for line in doc.get("lines", [])
                     if isinstance(line, dict) and line.get("ja")),
        max_line_chars=MAX_LINE_CHARS,
    )
    name = model or llm.DEFAULT_MODEL
    try:
        data = llm.generate(name, brief, log=log)
    except llm.LLMError as exc:
        raise NewError(str(exc)) from exc

    lines = [{"ja": line["ja"].strip(), "vi": line["vi"].strip()}
             for line in data.get("lines", []) if line.get("ja", "").strip()]
    if not lines:
        raise NewError("Claude trả về kịch bản không có câu nào.")
    return Draft(
        theme=data.get("theme", "").strip() or f"{day.month}月{day.day}日",
        tags=tuple(data.get("tags", [])),
        lines=lines,
        source={"writer": llm.MODELS[name]},
    )


def _writer(model: str) -> str | None:
    """"bank", một tên model, hoặc None = Claude với model mặc định.

    Không nói gì thì có khoá mới gọi Claude. Đó là nghĩa của "mặc định tắt":
    chưa từng cắm khoá thì không bao giờ có lời gọi mạng nào tốn tiền.
    """
    name = model.strip().lower()
    if name == "bank":
        return "bank"
    if name:
        return name
    env.load()
    return None if os.environ.get("ANTHROPIC_API_KEY") else "bank"


# --------------------------------------------------------------------------
# Ghép và ghi
# --------------------------------------------------------------------------

def compose(slug: str, day: date, draft: Draft, settings: dict) -> dict:
    """Cài đặt ở trên, nội dung ở dưới — mở file ra là thấy ngay phần cần sửa."""
    doc: dict = {"id": slug, "title": f"{day.month}月{day.day}日 - {draft.theme}"}
    for key, value in settings.items():
        if key == "intro" and isinstance(value, dict):
            # Độ dài màn mở đầu là cài đặt, chữ trên nó là nội dung.
            value = {"title": draft.theme,
                     **{k: v for k, v in value.items() if k != "title"}}
        doc[key] = value
    if draft.tags:
        doc["tags"] = list(draft.tags)
    doc["lines"] = draft.lines
    doc["source"] = draft.source
    return doc


def _review(draft: Draft, settings: dict) -> list[str]:
    """Những chỗ đáng sửa tay trước khi `make content`. Cảnh báo, không chặn."""
    notes = []
    lo, hi = LINES_RANGE
    if not lo <= len(draft.lines) <= hi:
        notes.append(f"có {len(draft.lines)} câu, nhịp quen là {lo}–{hi} câu")
    for i, line in enumerate(draft.lines, start=1):
        n = spoken_chars(line["ja"])
        if n > MAX_LINE_CHARS:
            notes.append(f"câu {i} dài {n} chữ (quá {MAX_LINE_CHARS}), phụ đề dễ tràn")
        if not line["vi"].strip():
            notes.append(f"câu {i} chưa có bản dịch")
    t_lo, t_hi = _target(settings)
    seconds = estimate_seconds(draft.lines, settings)
    if not t_lo <= seconds <= t_hi:
        notes.append(f"ước lượng {seconds:.0f} giây, ngoài khoảng {t_lo:g}–{t_hi:g}")
    return notes


def create(slug: str, model: str = "", log=print) -> Path:
    """Tạo content/<slug>.json. Trả về đường dẫn file vừa ghi."""
    day = date_from_slug(slug)
    if day is None:
        raise NewError(f"\"{slug}\" không phải ngày. Ví dụ: make new DAY=2026-09-10")

    dest = CONTENT_DIR / f"{slug}.json"
    if dest.exists():
        raise NewError(
            f"Đã có {dest.relative_to(ROOT)}. Đó là file người viết nên máy không "
            f"đè. Muốn tạo lại thì xoá nó trước."
        )

    scripts = _scripts(CONTENT_DIR)
    template_slug, settings = _template(scripts, slug)
    log(f"Cài đặt kế thừa từ: {template_slug or '(mặc định, chưa có ngày nào)'}")

    writer = _writer(model)
    if writer == "bank":
        draft = _from_bank(day, scripts)
        log(f"Nội dung lấy từ ngân hàng: mục \"{draft.source['id']}\"")
    else:
        draft = _from_llm(writer, day, slug, scripts, settings, log)
        log(f"Nội dung do {draft.source['writer']} viết")

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(compose(slug, day, draft, settings), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    # Kiểm bằng CHÍNH bộ kiểm mà `make content` dùng. Không qua được thì xoá
    # file đi — để lại một kịch bản hỏng là đẩy lỗi sang lệnh sau.
    try:
        script_mod.load(CONTENT_DIR, slug)
    except script_mod.ScriptError as exc:
        dest.unlink()
        raise NewError(f"Kịch bản vừa sinh không qua được script.py: {exc}") from exc

    chars = sum(spoken_chars(line["ja"]) for line in draft.lines)
    log(f"\nĐã ghi {dest.relative_to(ROOT)}  —  {draft.theme}")
    log(f"  {len(draft.lines)} câu, {chars} chữ, ước lượng "
        f"~{estimate_seconds(draft.lines, settings):.0f} giây "
        f"(số thật do TTS quyết)")
    for i, line in enumerate(draft.lines, start=1):
        log(f"  {i:2d}. {line['ja']}")
    notes = _review(draft, settings)
    if notes:
        log("\n[!] Nên xem lại trước khi dựng:")
        for note in notes:
            log(f"    - {note}")
    log(f"\nSửa file nếu muốn, rồi: make content DAY={slug}")
    return dest


def report_bank(log=print) -> int:
    """In cả ngân hàng: mỗi mục bao nhiêu câu, bao nhiêu chữ, ước lượng bao lâu, đã dùng chưa."""
    bank = load_bank()
    scripts = _scripts(CONTENT_DIR)
    used = _bank_usage(scripts)
    _, settings = _template(scripts, "9999")
    lo, hi = _target(settings)
    sample = date.today()

    log(f"Ngân hàng: {len(bank)} mục  (ước lượng theo cài đặt của ngày mới nhất, "
        f"khoảng mong muốn {lo:g}–{hi:g}s)\n")
    log(f"  {'id':<16} {'chủ đề':<10} {'câu':>3} {'chữ':>4} {'~giây':>6}  đã dùng")
    fresh = 0
    for entry in bank:
        lines = [{"ja": _fill_date(l["ja"], sample)} for l in entry["lines"]]
        seconds = estimate_seconds(lines, settings)
        chars = sum(spoken_chars(l["ja"]) for l in lines)
        flag = "" if lo <= seconds <= hi else "  [!] ngoài khoảng"
        if entry["id"] not in used:
            fresh += 1
        log(f"  {entry['id']:<16} {entry['theme']:<10} {len(lines):>3} {chars:>4} "
            f"{seconds:>6.1f}  {used.get(entry['id'], '—')}{flag}")
    log(f"\nCòn {fresh} mục chưa dùng. Hết thì `make new` quay lại mục dùng lâu nhất.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args[:1] == ["--bank"]:
            return report_bank()
        if not args:
            print("Thiếu ngày. Ví dụ: make new DAY=2026-09-10", file=sys.stderr)
            return 2
        create(args[0], args[1] if len(args) > 1 else "")
    except (NewError, script_mod.ScriptError, library_mod.LibraryError) as exc:
        print(f"\n[lỗi] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
