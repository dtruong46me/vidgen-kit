"""
Kiểm một MP4 đã dựng xong.

    python3 -m pipeline.check 2026-08-20

Hai phần, trả lời hai câu hỏi khác hẳn nhau:

1. SỐ ĐO — máy tự kết luận PASS/FAIL. Khổ hình, fps, có tiếng không, số frame
   thật có khớp build.json không, thời lượng có trong khoảng targetSeconds không.
   Mấy thứ này sai thì video hỏng mà nhìn ảnh tĩnh không thấy.

2. TRANG DUYỆT — người kết luận. Một frame giữa mỗi cảnh, đặt cạnh câu chữ lẽ ra
   phải hiện, có tô vùng mà TikTok/Reels che. Hai lỗi máy không bắt được nhưng
   mắt thấy trong một giây: chữ ra ô vuông (tofu, font thiếu glyph) và phụ đề
   bị giao diện nền tảng che mất.

Ghi ra: out/<slug>-check/index.html  (trang duyệt, kèm bảng số đo)
        out/<slug>-check/sheet.jpg   (ảnh ghép, mở thẳng trong VS Code được)

Module này KHÔNG tính timeline. Nó đọc vị trí cảnh từ build.json — cộng dồn
`durationInFrames` đúng như `getStarts` trong DailyVideo.tsx — rồi xem MP4 có
khớp không. Nó là người kiểm, không phải người dựng.
"""

from __future__ import annotations

import html
import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import script as script_mod
from .probe import ProbeError, count_frames, media_info
from .render import OUT_DIR

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"

#: Vùng giao diện nền tảng che, tính theo khung 1080×1920. Đáy 380px là quy ước
#: trong CLAUDE.md; dải phải 110px là SAFE_SIDE của Caption.tsx.
COVER_BOTTOM = 380
COVER_RIGHT = 110

#: Bề ngang ảnh trích ra. 360 là 1/3 khung gốc — đủ nét để thấy ô vuông tofu.
THUMB_WIDTH = 360
SHEET_COLUMNS = 6


class CheckError(RuntimeError):
    """Thiếu thứ để kiểm, hoặc ffmpeg không chạy được."""


@dataclass(frozen=True)
class Finding:
    label: str
    #: PASS, FAIL, WARN (đáng xem nhưng không hỏng), SKIP (không đủ dữ liệu để kiểm)
    status: str
    detail: str


@dataclass(frozen=True)
class Moment:
    """Một khung hình đáng trích: giữa mỗi cảnh, trong màn kết."""

    label: str
    frame: int
    line: dict | None


def total_frames(build: dict) -> int:
    """Tổng frame build.json hứa: các cảnh + kết. Cùng phép cộng với calculateMetadata."""
    outro = (build.get("outro") or {}).get("durationInFrames", 0)
    return sum(line["durationInFrames"] for line in build["lines"]) + outro


def moments(build: dict) -> list[Moment]:
    """Chọn khung hình mà chữ đã hiện đủ và chưa bắt đầu tắt.

    - Mỗi cảnh: giữa cảnh. Chữ vào trong 26 frame, tắt trong 20, cảnh sau chồng
      vào 24 frame cuối — giữa cảnh luôn an toàn với cảnh dài hơn 2 giây. Ở cảnh
      1, giữa cảnh là lúc tiêu đề ngày và caption câu 1 cùng đang hiện đủ.
    - Kết: 40% màn. Chữ vào xong ở frame 30, bắt đầu nhạt ở 55%.
    """
    out: list[Moment] = []
    cursor = 0
    for i, line in enumerate(build["lines"], start=1):
        out.append(Moment(f"Cảnh {i}", cursor + line["durationInFrames"] // 2, line))
        cursor += line["durationInFrames"]
    outro = build.get("outro")
    if outro:
        out.append(Moment("Kết", cursor + outro["durationInFrames"] * 2 // 5, None))
    return out


# --------------------------------------------------------------------------
# Phần 1 — số đo
# --------------------------------------------------------------------------

def _load(slug: str) -> tuple[dict, Path, Path]:
    build_path = CONTENT_DIR / f"{slug}.build.json"
    if not build_path.exists():
        raise CheckError(
            f"Chưa có {build_path.relative_to(ROOT)} — chạy 'make video DAY={slug}' trước."
        )
    mp4 = OUT_DIR / f"{slug}.mp4"
    if not mp4.exists():
        raise CheckError(
            f"Chưa có {mp4.relative_to(ROOT)} — chạy 'make video DAY={slug}' trước."
        )
    return json.loads(build_path.read_text(encoding="utf-8")), build_path, mp4


def measure(slug: str, build: dict, build_path: Path, mp4: Path) -> list[Finding]:
    info = media_info(mp4)
    frames = count_frames(mp4)
    out: list[Finding] = []

    want = f"{build['width']}×{build['height']}"
    got = f"{info.width}×{info.height}"
    out.append(Finding("Khổ hình", "PASS" if got == want else "FAIL",
                       got if got == want else f"{got}, lẽ ra {want}"))

    fps_ok = info.fps is not None and abs(info.fps - build["fps"]) < 0.01
    out.append(Finding("fps", "PASS" if fps_ok else "FAIL",
                       f"{info.fps:g}" if fps_ok else f"{info.fps}, lẽ ra {build['fps']}"))

    out.append(Finding("Luồng tiếng", "PASS" if info.has_audio else "FAIL",
                       "có" if info.has_audio else "KHÔNG có — video câm"))

    # Phép kiểm đáng giá nhất: lệch ở đây là video cụt đuôi hoặc thừa đoạn đen,
    # mà Remotion lẫn timeline.py đều không báo lỗi gì.
    want_frames = total_frames(build)
    parts = [f"{sum(l['durationInFrames'] for l in build['lines'])} thoại"]
    if build.get("outro"):
        parts.append(f"{build['outro']['durationInFrames']} kết")
    breakdown = " + ".join(parts)
    out.append(Finding(
        "Số frame",
        "PASS" if frames == want_frames else "FAIL",
        f"{frames} = {breakdown}" if frames == want_frames
        else f"{frames}, build.json hứa {want_frames} ({breakdown})",
    ))

    try:
        target = script_mod.load(CONTENT_DIR, slug).target_seconds
    except script_mod.ScriptError:
        target = None
    if target is None:
        out.append(Finding("Thời lượng", "SKIP",
                           f"{info.seconds:.2f}s — kịch bản không khai targetSeconds"))
    else:
        lo, hi = target
        ok = lo <= info.seconds <= hi
        out.append(Finding("Thời lượng", "PASS" if ok else "FAIL",
                           f"{info.seconds:.2f}s, khoảng mong muốn {lo:g}–{hi:g}s"))

    # Đã từng xảy ra: tưởng đang xem bản mới, hoá ra MP4 là bản dựng từ trước.
    fresh = mp4.stat().st_mtime >= build_path.stat().st_mtime
    out.append(Finding(
        "Độ mới", "PASS" if fresh else "WARN",
        "MP4 dựng sau build.json" if fresh
        else "MP4 CŨ hơn build.json — có thể là bản dựng trước lần sửa gần nhất",
    ))
    return out


# --------------------------------------------------------------------------
# Phần 2 — trang duyệt
# --------------------------------------------------------------------------

def _ffmpeg(*args: str) -> None:
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", *args],
                       capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise CheckError("Không tìm thấy lệnh ffmpeg. Cài ffmpeg rồi chạy lại.") from exc
    except subprocess.CalledProcessError as exc:
        raise CheckError(f"ffmpeg lỗi:\n{exc.stderr.strip()}") from exc


def extract(build: dict, mp4: Path, dest_dir: Path) -> list[tuple[Moment, Path]]:
    """Trích mỗi khung một file jpg, rồi ghép thành sheet.jpg có tô vùng bị che."""
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True)

    picked = []
    for n, moment in enumerate(moments(build)):
        dest = dest_dir / f"{n:02d}.jpg"
        # Tua tới GIỮA frame (+0,5) chứ không phải mép, để làm tròn thời gian
        # không rơi sang frame liền trước.
        seconds = (moment.frame + 0.5) / build["fps"]
        _ffmpeg("-ss", f"{seconds:.4f}", "-i", str(mp4), "-frames:v", "1",
                "-vf", f"scale={THUMB_WIDTH}:-2", "-q:v", "3", str(dest))
        picked.append((moment, dest))

    scale = THUMB_WIDTH / build["width"]
    bottom = round(COVER_BOTTOM * scale)
    right = round(COVER_RIGHT * scale)
    columns = min(SHEET_COLUMNS, len(picked))
    rows = math.ceil(len(picked) / columns)
    _ffmpeg(
        "-framerate", "1", "-start_number", "0",
        "-i", str(dest_dir / "%02d.jpg"),
        "-vf",
        # Chỉ kẻ viền, không tô: ngay dưới phụ đề là dải phủ tối, tô đỏ lên đó là
        # che mất đúng thứ cần soi.
        f"drawbox=x=0:y=ih-{bottom}:w=iw:h={bottom}:color=red@0.85:t=2,"
        f"drawbox=x=iw-{right}:y=0:w={right}:h=ih-{bottom}:color=red@0.85:t=2,"
        f"tile={columns}x{rows}:padding=8:margin=8:color=0x0a0c0b",
        "-frames:v", "1", "-q:v", "3", str(dest_dir / "sheet.jpg"),
    )
    return picked


_STATUS_COLOR = {"PASS": "#8fbc7e", "FAIL": "#e0806f", "WARN": "#d3ab50", "SKIP": "#8a938c"}


def write_page(slug: str, build: dict, findings: list[Finding],
               picked: list[tuple[Moment, Path]], dest_dir: Path) -> Path:
    esc = html.escape
    rows = "".join(
        f'<tr><td>{esc(f.label)}</td>'
        f'<td style="color:{_STATUS_COLOR[f.status]};font-weight:600">{f.status}</td>'
        f'<td>{esc(f.detail)}</td></tr>'
        for f in findings
    )
    cards = []
    for moment, path in picked:
        line = moment.line or {}
        if moment.line is None and build.get("outro"):
            text = f'<p class="ja">{esc(build["outro"]["text"])}</p>'
        else:
            # Cảnh 1 còn có tiêu đề ngày đè lên ở 1/3 trên — cũng là chữ phải hiện.
            card = build.get("titleCard") if moment.label == "Cảnh 1" else None
            text = ((f'<p class="ja">{esc(card["title"])}　{esc(card.get("subtitle") or "")}</p>'
                     if card else "")
                    + f'<p class="ja">{esc(line.get("ja", ""))}</p>'
                    f'<p class="ro">{esc(line.get("romaji", ""))}</p>'
                    f'<p class="vi">{esc(line.get("vi", ""))}</p>')
        cards.append(
            f'<figure><div class="shot"><img src="{path.name}" alt="{esc(moment.label)}">'
            f'<i class="cover-b"></i><i class="cover-r"></i></div>'
            f'<figcaption><b>{esc(moment.label)}</b>'
            f'<span>frame {moment.frame} · {moment.frame / build["fps"]:.1f}s</span>'
            f'{text}</figcaption></figure>'
        )

    bottom_pct = COVER_BOTTOM / build["height"] * 100
    right_pct = COVER_RIGHT / build["width"] * 100
    page = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Duyệt {esc(slug)}</title>
<style>
  body {{ margin:0; background:#0f1211; color:#e6eae3;
         font:14px/1.5 system-ui, "Segoe UI", sans-serif; }}
  main {{ max-width:1200px; margin:0 auto; padding:28px 20px 60px; }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .hint {{ color:#929c93; margin:0 0 18px; max-width:70ch; }}
  table {{ border-collapse:collapse; margin:0 0 28px; font-variant-numeric:tabular-nums; }}
  td {{ padding:5px 14px 5px 0; border-bottom:1px solid #232823; vertical-align:top; }}
  .grid {{ display:grid; gap:18px; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); }}
  figure {{ margin:0; }}
  .shot {{ position:relative; aspect-ratio:{build["width"]}/{build["height"]};
          background:#000; overflow:hidden; }}
  .shot img {{ width:100%; height:100%; display:block; }}
  .shot i {{ position:absolute; background:rgba(224,80,60,.06);
            outline:1px dashed rgba(224,128,111,.8); outline-offset:-1px; }}
  .cover-b {{ left:0; right:0; bottom:0; height:{bottom_pct:.2f}%; }}
  .cover-r {{ top:0; right:0; width:{right_pct:.2f}%; bottom:{bottom_pct:.2f}%; }}
  figcaption {{ padding:8px 2px 0; }}
  figcaption b {{ margin-right:8px; }}
  figcaption span {{ color:#929c93; font-size:12px; }}
  figcaption p {{ margin:4px 0 0; }}
  .ja {{ font-family:"Hiragino Mincho ProN","Yu Mincho","Noto Serif JP",serif; font-size:15px; }}
  .ro {{ color:#c2c9be; font-size:13px; }}
  .vi {{ color:#929c93; font-size:13px; }}
</style></head><body><main>
<h1>Duyệt {esc(slug)}</h1>
<p class="hint">Mỗi ảnh là một khung giữa cảnh, chữ bên dưới là chữ LẼ RA phải hiện.
So hai bên: chữ trong ảnh ra ô vuông là thiếu font; chữ lấn vào vùng đỏ là bị
giao diện TikTok/Reels che.</p>
<table>{rows}</table>
<div class="grid">{"".join(cards)}</div>
</main></body></html>
"""
    dest = dest_dir / "index.html"
    dest.write_text(page, encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Thiếu ngày. Ví dụ: make check DAY=2026-08-20", file=sys.stderr)
        return 2
    slug = args[0]

    try:
        build, build_path, mp4 = _load(slug)
        print(f"Kiểm {mp4.relative_to(ROOT)}\n")
        findings = measure(slug, build, build_path, mp4)
        width = max(len(f.label) for f in findings)
        for f in findings:
            print(f"  {f.status:<4}  {f.label:<{width}}  {f.detail}")

        dest_dir = OUT_DIR / f"{slug}-check"
        picked = extract(build, mp4, dest_dir)
        page = write_page(slug, build, findings, picked, dest_dir)
    except (CheckError, ProbeError, script_mod.ScriptError) as exc:
        print(f"\n[lỗi] {exc}", file=sys.stderr)
        return 1

    failed = [f for f in findings if f.status == "FAIL"]
    print(f"\n  Trang duyệt: {page.relative_to(ROOT)}")
    print(f"  Ảnh ghép:    {(dest_dir / 'sheet.jpg').relative_to(ROOT)}  "
          f"({len(picked)} khung, vùng đỏ là chỗ nền tảng che)")
    print(f"\n{'FAIL' if failed else 'PASS'}"
          + (f" — {len(failed)} mục hỏng" if failed else "")
          + " · soi trang duyệt để bắt tofu và phụ đề bị che")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
