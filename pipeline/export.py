"""
Gói ngày thành thư mục đăng được: `out/<ngày>/`.

    python3 -m pipeline.export 2026-09-12               gói một ngày
    python3 -m pipeline.export 2026-09-12..2026-09-30   gói một khoảng, tính cả hai đầu
    python3 -m pipeline.export 2026-09-12..             từ ngày đó tới ngày cuối cùng đã dựng
    python3 -m pipeline.export 2026-09                  gói cả tháng
    python3 -m pipeline.export --all                    gói mọi ngày đã có build.json

Video dựng xong rồi vẫn chưa đăng được: còn thiếu dòng caption, còn thiếu bản
chữ để soát lại, còn thiếu chỗ ghi công tác giả clip. Trước BƯỚC 7 những thứ đó
nằm rải trong đầu người đăng. Giờ mọi thứ của một ngày nằm trong MỘT thư mục:

    out/2026-09-12/
      2026-09-12.mp4            video để đăng        ┐ Remotion dựng thẳng
      2026-09-12-thumbnail.png  ảnh bìa              ┘ vào đây (render.py)
      caption.txt               dòng caption + hashtag — dán TikTok/Reels
      description.txt           caption + toàn bộ lời Nhật–Việt + ghi công — dán YouTube
      script.txt                bảng đọc: Nhật / romaji / hiragana / Việt, từng câu
      credits.txt               nguồn, tác giả, giấy phép của từng clip và bản nhạc
      metadata.json             mọi số đo và mọi trường máy đọc được
      audio/line-XX.mp3         giọng đọc từng câu

Video và ảnh bìa KHÔNG do module này viết, và cũng không được chép: trước đây
chúng nằm lẻ ở `out/<ngày>.mp4` rồi được chép vào gói, nên mỗi video nằm hai
chỗ. Gặp bố cục cũ đó thì module này DỜI file vào thư mục ngày, một lần là xong.

Module này KHÔNG tính gì cả. Nó đọc `content/<slug>/build.json` — hợp đồng đã
chốt — cộng thêm số đo thật của MP4 nếu có. Nó là người đóng gói, không phải
người dựng. Vì vậy sửa nó không bao giờ làm lệch một frame nào.

Một ngoại lệ, đúng một thứ: **ảnh bìa còn thiếu thì gọi Remotion dựng luôn.**
Gói không có ảnh bìa là gói chưa đăng được, mà ảnh bìa chỉ tốn MỘT frame chứ
không phải cả video. Ngoại lệ này không phá nguyên tắc ở trên, vì nó không tính
frame nào cả: frame chụp là `thumbnailFrame` đã ghi sẵn trong hợp đồng, do
`timeline.py` chọn (P-2). Ngày nào đã có ảnh bìa thì không dựng lại, nên lần gói
thứ hai vẫn nhanh và vẫn ra thư mục giống hệt.

Gói lại thì xoá và viết lại ĐÚNG những thứ module này sinh ra (`GENERATED`),
không xoá cả thư mục: video nằm ngay cạnh, xoá theo là mất nửa tiếng render.

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

from . import library as library_mod, paths, render as render_mod
from .check import total_frames
from .probe import ProbeError, count_frames, media_info

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
PUBLIC_DIR = ROOT / "studio" / "public"

#: Bề ngang khung chữ trong script.txt và description.txt.
RULE = "─" * 64

#: Thứ module này viết ra trong `out/<ngày>/` — gói lại thì CHỈ những thứ này bị
#: xoá. Phải xoá: bớt một câu rồi gói lại mà còn `line-09.mp3` nằm lại thì người
#: đăng sẽ tưởng video có chín câu. Nhưng video và ảnh bìa nằm cùng thư mục là
#: của Remotion — không có tên trong đây thì không bao giờ bị đụng tới.
GENERATED = ("caption.txt", "description.txt", "script.txt", "credits.txt",
             "metadata.json", "audio")


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
    has_video: bool = False


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
            f"    Ngày đã dựng nội dung: " + (paths.span(days()) or "(chưa có ngày nào)")
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


def metadata(build: dict, mp4: Path | None, thumb: Path | None = None) -> dict:
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

    # Ảnh bìa: ghi cả frame đã chụp, để sau này nhìn metadata là biết ảnh bìa
    # lấy ở đâu ra mà không phải mở build.json.
    thumbnail = {
        "file": thumb.name if thumb else None,
        "rendered": thumb is not None,
        "frame": build.get("thumbnailFrame"),
    }

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
        "thumbnail": thumbnail,
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


def _clear_generated(dest_dir: Path) -> None:
    """Xoá đúng những thứ trong GENERATED — video và ảnh bìa nằm yên."""
    for name in GENERATED:
        target = dest_dir / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def _adopt_legacy(slug: str, log) -> list[str]:
    """Dời video/ảnh bìa bố cục CŨ (`out/<ngày>.mp4` nằm lẻ) vào thư mục ngày.

    DỜI chứ không chép: chép thì mỗi video nằm hai chỗ, đúng cái lộn xộn mà bố
    cục mới sinh ra để bỏ. Thư mục ngày đã có bản của nó thì bản cũ không bị
    đụng tới — chỉ nhắc, vì không biết bản nào là bản người đăng muốn giữ.
    """
    notes: list[str] = []
    for old, new in paths.legacy_outputs(slug):
        if not old.exists():
            continue
        if new.exists():
            notes.append(f"còn bản cũ {old.relative_to(ROOT)} nằm lẻ ngoài — gói dùng "
                         f"{new.relative_to(ROOT)}, bản cũ xoá được")
            continue
        shutil.move(old, new)
        log(f"  dời {old.relative_to(ROOT)} → {new.relative_to(ROOT)} (bố cục cũ)")
    return notes


def _thumbnail_stale(thumb: Path, slug: str) -> bool:
    """Ảnh bìa cần dựng lại chưa? Thiếu, hoặc cũ hơn hợp đồng.

    So mtime với `build.json` vì `thumbnailFrame` nằm trong đó: dựng lại nội
    dung xong mà ảnh bìa vẫn là bản chụp ở frame cũ thì gói mang một cái bìa
    không còn đúng với video — mà nhìn file thì không thấy.
    """
    if not thumb.exists():
        return True
    return thumb.stat().st_mtime < paths.build_path(slug).stat().st_mtime


def _ensure_thumbnail(thumb: Path, slug: str, log) -> list[str]:
    """Lo cho gói có ảnh bìa mới. Trả về ghi chú, KHÔNG ném lỗi.

    Hỏng thì không chặn: máy nào chưa dựng được video thì vẫn phải gói được
    phần chữ. Nói ra một dòng là đủ — nhưng phải nói đủ hai chuyện khác nhau:
    không dựng được, và gói đang mang bản chụp cũ.
    """
    if not _thumbnail_stale(thumb, slug):
        return []

    log(f"  dựng ảnh bìa {thumb.relative_to(ROOT)} (chưa có hoặc đã cũ)…")
    try:
        render_mod.thumbnail(slug)
        return []
    except (render_mod.RenderError, OSError) as exc:
        notes = [f"chưa dựng được ảnh bìa: {exc}"]
    if thumb.exists():
        notes.append(
            f"{thumb.name} là bản chụp từ lần dựng trước, cũ hơn build.json — "
            f"frame có thể không còn đúng. Chạy `make thumbnail DAY={slug}`"
        )
    return notes


def package(slug: str, log=print) -> Package:
    """Gói một ngày. Trả về Package; ném ExportError khi chưa có build.json."""
    build = _build(slug)
    # Đọc sổ tài sản TRƯỚC khi xoá gì: sổ hỏng thì gói cũ vẫn còn nguyên.
    library = library_mod.load()
    credits, credit_notes = credit_rows(build, library)

    dest_dir = paths.out_dir(slug)
    dest_dir.mkdir(parents=True, exist_ok=True)
    notes = _adopt_legacy(slug, log) + credit_notes
    _clear_generated(dest_dir)

    mp4 = paths.video_path(slug)
    thumb = paths.thumbnail_path(slug)
    notes += _ensure_thumbnail(thumb, slug, log)
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
        json.dumps(metadata(build, mp4 if mp4.exists() else None,
                            thumb if thumb.exists() else None),
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    written.append("metadata.json")

    copied, audio_notes = _copy_audio(build, dest_dir)
    notes += audio_notes
    written.append(f"audio/ ({copied} file)")

    # Video và ảnh bìa đã nằm sẵn trong thư mục — không chép, chỉ điểm danh.
    written += [media.name for media in (mp4, thumb) if media.exists()]

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
    return Package(slug=slug, dest=dest_dir, files=written, notes=notes,
                   has_video=mp4.exists())


def package_many(slugs: list[str], log=print) -> list[Package]:
    """Gói lần lượt từng ngày, rồi tóm tắt một dòng."""
    log(f"Gói {len(slugs)} ngày: {paths.span(slugs)}\n")
    out = []
    for slug in slugs:
        out.append(package(slug, log=log))
        log("")
    flagged = sum(1 for p in out if p.notes)
    videos = sum(1 for p in out if p.has_video)
    log(f"Xong {len(out)} gói trong {paths.OUT_DIR.relative_to(ROOT)}/ — "
        f"{videos}/{len(out)} gói có video"
        + (f", {flagged} gói có chỗ cần xem lại." if flagged else ", không có cảnh báo nào."))
    return out


def package_all(log=print) -> list[Package]:
    todo = days()
    if not todo:
        raise ExportError(
            "Chưa ngày nào có content/<ngày>/build.json. "
            "Chạy `make content DAY=...` hoặc `make video DAY=...` trước."
        )
    return package_many(todo, log=log)


USAGE = f"""Cách dùng:
    python3 -m pipeline.export <ngày>          gói một ngày
    python3 -m pipeline.export <từ>..<đến>     gói một khoảng, tính cả hai đầu
    python3 -m pipeline.export <từ>..          từ ngày đó tới ngày cuối cùng đã dựng
    python3 -m pipeline.export 2026-09         gói cả tháng
    python3 -m pipeline.export --all           gói mọi ngày đã có build.json

{paths.SPEC_HELP}

Thường thì gọi qua Makefile:
    make export DAY=2026-09-12
    make export FROM=2026-09-12 TO=2026-09-30    (bỏ TO = tới ngày cuối cùng)
    make export MONTH=2026-09
    make export-all"""


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print(USAGE, file=sys.stderr)
        return 2
    spec = args[0]
    try:
        if spec == "--all":
            package_all()
        elif paths.is_range(spec):
            chosen = paths.select(spec, days())
            if not chosen:
                raise ExportError(
                    f"Không ngày nào khớp '{spec}' mà đã dựng nội dung.\n"
                    f"    Ngày đã dựng: " + (paths.span(days()) or "(chưa có ngày nào)")
                )
            package_many(chosen)
        else:
            package(spec)
    except paths.SpecError as exc:
        print(f"\n[lỗi] {exc}", file=sys.stderr)
        return 2
    except (ExportError, library_mod.LibraryError, ProbeError) as exc:
        print(f"\n[lỗi] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
