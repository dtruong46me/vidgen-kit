"""
Gói một ngày thành thư mục đăng được: `out/<slug>/`.

    python3 -m pipeline.export 2026-08-20        gói một ngày
    python3 -m pipeline.export --all             gói mọi ngày đã có build.json

Video dựng xong rồi vẫn chưa đăng được: còn thiếu dòng caption, còn thiếu bản
chữ để soát lại, còn thiếu chỗ ghi công tác giả clip. Trước BƯỚC 7 những thứ đó
nằm rải trong đầu người đăng. Giờ chúng nằm trong một thư mục:

    out/2026-08-20/
      caption.txt        dòng caption + hashtag — dán TikTok/Reels
      description.txt    caption + toàn bộ lời Nhật–Việt + ghi công — dán YouTube
      script.txt         bảng đọc: Nhật / romaji / hiragana / Việt, từng câu
      metadata.json      mọi số đo và mọi trường máy đọc được
      credits.txt        nguồn, tác giả, giấy phép của từng clip và bản nhạc
      audio/line-XX.mp3  giọng đọc từng câu
      2026-08-20.mp4     video (nếu đã dựng)
      2026-08-20-thumbnail.png

Module này KHÔNG tính gì cả. Nó đọc `content/<slug>/build.json` — hợp đồng đã
chốt — cộng thêm số đo thật của MP4 nếu có. Nó là người đóng gói, không phải
người dựng. Vì vậy sửa nó không bao giờ làm lệch một frame nào.

Phép cộng frame duy nhất ở đây mượn nguyên của `check.py` (`total_frames`,
`moments`), chứ không viết lại — P-2: đếm frame sai thì chỉ có thể sai ở một chỗ.

KHÔNG ghi thời điểm chạy vào metadata.json. Gói hai lần phải ra hai thư mục
giống hệt nhau, y như bộ chọn clip phải tất định: có dấu thời gian thì `diff`
lúc nào cũng khác nhau và mất luôn tác dụng làm mốc.
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from . import library as library_mod, paths
from .check import total_frames
from .probe import ProbeError, count_frames, media_info
from .render import OUT_DIR

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
PUBLIC_DIR = ROOT / "studio" / "public"

#: Bề ngang khung chữ trong script.txt và description.txt.
RULE = "─" * 64


class ExportError(RuntimeError):
    """Thiếu thứ để gói. Thông báo viết cho người đọc, không phải traceback."""


@dataclass(frozen=True)
class Package:
    """Kết quả một lần gói."""

    slug: str
    dest: Path
    files: list[str]
    #: Chỗ chưa ổn, in ra cuối lệnh. Không chặn — gói vẫn dùng được.
    notes: list[str]


# --------------------------------------------------------------------------
# Đọc
# --------------------------------------------------------------------------

def days(content_dir: Path = CONTENT_DIR) -> list[str]:
    """Mọi ngày đã có build.json, xếp theo tên tức theo ngày."""
    return paths.built_slugs(content_dir)


def _build(slug: str) -> dict:
    path = paths.build_path(slug)
    if not path.exists():
        raise ExportError(
            f"Chưa có {path.relative_to(ROOT)} — chạy `make content DAY={slug}` trước.\n"
            f"    Ngày đã dựng nội dung: " + (", ".join(days()) or "(chưa có ngày nào)")
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ExportError(f"{path.name} không phải JSON hợp lệ: {exc}") from exc


def _post(build: dict) -> dict:
    """Phần bài đăng. build.json dựng trước BƯỚC 7 không có trường này."""
    return build.get("post") or {}


def _seconds(build: dict) -> float:
    return total_frames(build) / build.get("fps", 30)


# --------------------------------------------------------------------------
# Sinh từng file
# --------------------------------------------------------------------------

def caption_text(build: dict) -> str:
    post = _post(build)
    caption = post.get("caption", "")
    tags = post.get("hashtags") or []
    line = " ".join(f"#{t.lstrip('#')}" for t in tags)
    return f"{caption}\n\n{line}\n" if line else f"{caption}\n"


def script_text(build: dict) -> str:
    """Bảng đọc từng câu. Cùng bố cục với `make reading`, thêm dòng tiếng Việt."""
    out = [
        build.get("title", build["id"]),
        f"{build['id']} · {len(build['lines'])} câu · {_seconds(build):.1f} giây",
        "",
        RULE,
        "",
    ]
    for i, line in enumerate(build["lines"], start=1):
        out.append(f"{i:2d}. {line['ja']}")
        out.append(f"    {line.get('romaji', '')}")
        if line.get("hira") and line["hira"] != line["ja"]:
            out.append(f"    {line['hira']}")
        out.append(f"    {line.get('vi', '')}")
        out.append("")
    outro = build.get("outro")
    if outro:
        out.append(f"    (kết) {outro.get('text', '')}")
        out.append("")
    return "\n".join(out)


def description_text(build: dict, credits: list[str]) -> str:
    """Bản dài để dán YouTube: caption, lời Nhật–Việt, rồi ghi công."""
    post = _post(build)
    out = [post.get("caption", ""), ""]
    out += [RULE, ""]
    for line in build["lines"]:
        out.append(line["ja"])
        out.append(line.get("vi", ""))
        out.append("")
    if credits:
        out += [RULE, "", "Hình ảnh và âm nhạc:", ""]
        out += [f"  {row}" for row in credits]
        out.append("")
    tags = post.get("hashtags") or []
    if tags:
        out.append(" ".join(f"#{t.lstrip('#')}" for t in tags))
        out.append("")
    return "\n".join(out)


def _used_assets(build: dict) -> list[str]:
    """File tài sản ngày này dùng, không trùng lặp, giữ thứ tự xuất hiện."""
    seen: dict[str, None] = {}
    for line in build["lines"]:
        if line.get("clip"):
            seen.setdefault(line["clip"], None)
    if build.get("bgm"):
        seen.setdefault(build["bgm"], None)
    return list(seen)


def credit_rows(build: dict, library) -> tuple[list[str], list[str]]:
    """Một dòng ghi công cho mỗi tài sản. Trả về (dòng ghi công, chỗ thiếu)."""
    rows, notes = [], []
    for rel in _used_assets(build):
        entry = library.by_file(rel)
        if entry is None:
            notes.append(f"{rel} không có dòng nào trong library/shots.json")
            rows.append(f"{rel} — chưa ghi sổ")
            continue
        bits = [entry.author or "(chưa rõ tác giả)"]
        if entry.license:
            bits.append(entry.license)
        if entry.url:
            bits.append(entry.url)
        rows.append(f"{entry.id} — " + " · ".join(bits))
        missing = [what for what, value in
                   (("tác giả", entry.author), ("giấy phép", entry.license),
                    ("nguồn", entry.url)) if not value]
        if missing:
            notes.append(f"{entry.id} thiếu {', '.join(missing)} trong library/shots.json")
    return rows, notes


def metadata(build: dict, mp4: Path | None) -> dict:
    """Mọi thứ máy đọc được, gộp một chỗ. Số đo lấy từ CHÍNH file MP4 nếu có."""
    fps = build.get("fps", 30)
    promised = total_frames(build)

    video: dict = {"file": mp4.name if mp4 else None, "rendered": mp4 is not None}
    if mp4 is not None:
        try:
            info = media_info(mp4)
            video.update({
                "width": info.width, "height": info.height, "fps": info.fps,
                # Đếm gói trên chính MP4, không tin `duration × fps` — độ dài
                # container tính cả luồng tiếng (xem check.py).
                "frames": count_frames(mp4),
                "seconds": round(info.seconds, 3),
            })
        except ProbeError as exc:
            video["error"] = str(exc)

    cursor = 0
    lines = []
    for i, line in enumerate(build["lines"], start=1):
        lines.append({
            "n": i,
            "ja": line["ja"],
            "romaji": line.get("romaji", ""),
            "hira": line.get("hira", ""),
            "vi": line.get("vi", ""),
            "startInFrames": cursor,
            "durationInFrames": line["durationInFrames"],
            "seconds": round(line["durationInFrames"] / fps, 3),
            "audio": line.get("audio"),
            "clip": line.get("clip"),
            "clipStartInSeconds": line.get("clipStartInSeconds"),
            # Câu dài hiện làm mấy màn chữ. null = hiện nguyên một màn.
            "segments": line.get("segments"),
        })
        cursor += line["durationInFrames"]

    return {
        "id": build["id"],
        "title": build.get("title"),
        "theme": (build.get("titleCard") or {}).get("subtitle", ""),
        "dateLabel": (build.get("titleCard") or {}).get("title", ""),
        "fps": fps,
        "width": build.get("width"),
        "height": build.get("height"),
        "lineCount": len(build["lines"]),
        "durationInFrames": promised,
        "seconds": round(promised / fps, 3),
        "post": _post(build),
        "video": video,
        "bgm": build.get("bgm"),
        "assets": _used_assets(build),
        "lines": lines,
    }


# --------------------------------------------------------------------------
# Gói
# --------------------------------------------------------------------------

def _copy_audio(build: dict, dest_dir: Path) -> tuple[int, list[str]]:
    """Chép giọng đọc từng câu vào gói. Đường dẫn lấy từ build.json, không đoán."""
    notes: list[str] = []
    copied = 0
    audio_dir = dest_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    for i, line in enumerate(build["lines"], start=1):
        rel = line.get("audio")
        if not rel:
            notes.append(f"câu {i} không có file giọng trong build.json")
            continue
        src = PUBLIC_DIR / rel
        if not src.exists():
            notes.append(f"thiếu {rel} — chạy `make content DAY={build['id']}` lại")
            continue
        shutil.copy2(src, audio_dir / Path(rel).name)
        copied += 1
    return copied, notes


def _copy_if_exists(src: Path, dest_dir: Path, out: list[str]) -> None:
    if src.exists():
        shutil.copy2(src, dest_dir / src.name)
        out.append(src.name)


def package(slug: str, log=print) -> Package:
    """Gói một ngày. Trả về Package; ném ExportError khi chưa có build.json."""
    build = _build(slug)
    dest_dir = OUT_DIR / slug
    # Xoá thư mục cũ trước: gói lại sau khi bớt một câu mà còn line-09.mp3 nằm
    # lại thì người đăng sẽ tưởng video có chín câu.
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    library = library_mod.load()
    credits, notes = credit_rows(build, library)

    mp4 = OUT_DIR / f"{slug}.mp4"
    written = []

    (dest_dir / "caption.txt").write_text(caption_text(build), encoding="utf-8")
    written.append("caption.txt")
    (dest_dir / "description.txt").write_text(
        description_text(build, credits), encoding="utf-8")
    written.append("description.txt")
    (dest_dir / "script.txt").write_text(script_text(build), encoding="utf-8")
    written.append("script.txt")
    (dest_dir / "credits.txt").write_text(
        "\n".join(credits) + "\n" if credits else "", encoding="utf-8")
    written.append("credits.txt")
    (dest_dir / "metadata.json").write_text(
        json.dumps(metadata(build, mp4 if mp4.exists() else None),
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    written.append("metadata.json")

    copied, audio_notes = _copy_audio(build, dest_dir)
    notes += audio_notes
    written.append(f"audio/ ({copied} file)")

    _copy_if_exists(mp4, dest_dir, written)
    _copy_if_exists(OUT_DIR / f"{slug}-thumbnail.png", dest_dir, written)

    if not mp4.exists():
        notes.append(f"chưa có {mp4.relative_to(ROOT)} — gói thiếu video, "
                     f"chạy `make video DAY={slug}`")
    post = _post(build)
    if not post:
        notes.append("build.json chưa có trường \"post\" — dựng bằng bản pipeline "
                     "cũ. Chạy `make content` lại để có caption")
    elif post.get("borrowed"):
        notes.append(f"caption đang mượn câu chốt — thêm \"caption\" vào "
                     f"content/{slug}/script.json")

    log(f"{slug} → {dest_dir.relative_to(ROOT)}")
    log(f"  {', '.join(written)}")
    if post.get("caption"):
        log(f"  caption: {post['caption']}")
    for note in notes:
        log(f"  [!] {note}")
    return Package(slug=slug, dest=dest_dir, files=written, notes=notes)


def package_all(log=print) -> list[Package]:
    todo = days()
    if not todo:
        raise ExportError(
            "Chưa ngày nào có content/<ngày>.build.json. "
            "Chạy `make content DAY=...` hoặc `make video DAY=...` trước."
        )
    log(f"Gói {len(todo)} ngày: {', '.join(todo)}\n")
    out = []
    for slug in todo:
        out.append(package(slug, log=log))
        log("")
    flagged = sum(1 for p in out if p.notes)
    log(f"Xong {len(out)} gói trong {OUT_DIR.relative_to(ROOT)}/"
        + (f" — {flagged} gói có chỗ cần xem lại." if flagged else " — không có cảnh báo nào."))
    return out


USAGE = """Cách dùng:
    python3 -m pipeline.export <ngày>     gói một ngày
    python3 -m pipeline.export --all      gói mọi ngày đã có build.json

Thường thì gọi qua Makefile: make export DAY=... / make export-all."""


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(USAGE, file=sys.stderr)
        return 2
    try:
        if args[0] == "--all":
            package_all()
        else:
            package(args[0])
    except (ExportError, library_mod.LibraryError, ProbeError) as exc:
        print(f"\n[lỗi] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
