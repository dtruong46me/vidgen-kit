"""
Xâu cả dây chuyền lại thành một lệnh.

    python3 -m pipeline.run 2026-08-20              chỉ chuẩn bị nội dung
    python3 -m pipeline.run 2026-08-20 --render     chuẩn bị rồi dựng MP4
    python3 -m pipeline.run 2026-08-20 --still 300  chỉ render 1 frame ra PNG

Đọc  : content/<slug>.json
Ghi  : studio/public/audio/<slug>/line-XX.mp3
       content/<slug>.build.json
       content/.<slug>.cache.json

Module này chỉ điều phối và in ra màn hình. Nó không tính toán gì cả — mọi phép
tính nằm ở module chuyên trách. Đó là cách giữ cho "bug ở đâu" luôn có một câu
trả lời duy nhất.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import (
    assets, contract, intro as intro_mod, library as library_mod,
    reading as reading_mod, render, script as script_mod, shots as shots_mod,
    timeline as timeline_mod, tts,
)
from .library import LibraryError
from .probe import ProbeError, duration_seconds

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
PUBLIC_DIR = ROOT / "studio" / "public"


def build_day(slug: str, log=print) -> Path:
    """Dựng nguyên liệu cho một ngày, trả về đường dẫn build.json."""
    doc = script_mod.load(CONTENT_DIR, slug)
    log(f"{doc.title}  —  {len(doc.lines)} câu, {doc.fps}fps")

    reader = reading_mod.make_provider(doc.reading)
    readings = []
    for i, line in enumerate(doc.lines, start=1):
        readings.append(reader.read(line.ja))
        if reader.unread:
            log(f"  [!] câu {i}: chưa đọc được số {', '.join(reader.unread)} "
                f"— romaji sẽ giữ nguyên chữ số")

    voices = tts.synthesize(
        doc, PUBLIC_DIR, CONTENT_DIR / f".{slug}.cache.json", log=log
    )

    # Chọn clip PHẢI đứng sau TTS: muốn biết clip có đủ dài không thì trước hết
    # phải biết cảnh dài bao nhiêu, mà cảnh dài bao nhiêu là do giọng đọc quyết
    # định (P-1). Câu nào kịch bản đã ghi clip thì bộ chọn không đụng vào.
    lines = _pick_clips(doc, voices, log)

    clips = [assets.resolve_clip(line, PUBLIC_DIR, log=log) for line in lines]
    bgm = assets.resolve_bgm(doc, PUBLIC_DIR, log=log)

    intro = intro_mod.build_intro(doc.intro, slug, doc.title)
    outro = intro_mod.build_outro(doc.outro)

    timeline = timeline_mod.build(doc, voices, clips, bgm, intro, outro)
    dest = contract.write(
        contract.compose(doc, voices, clips, bgm, timeline, readings, intro, outro),
        CONTENT_DIR / f"{slug}.build.json",
    )

    log(f"\nĐã ghi {dest.relative_to(ROOT)}")
    if intro or outro:
        parts = [f"{timeline.scenes_frames} frame thoại"]
        if intro:
            parts.insert(0, f"{timeline.intro_duration_in_frames} frame mở đầu")
        if outro:
            parts.append(f"{timeline.outro_duration_in_frames} frame kết")
        log(f"  {' + '.join(parts)}")
    log(f"{len(timeline.scenes)} câu — tổng {timeline.total_frames} frame "
        f"= {timeline.seconds:.1f} giây")

    _warn_if_off_target(doc, timeline.seconds, log)
    _warn_if_clip_loops(doc, clips, timeline, log)
    return dest


def _pick_clips(doc, voices, log):
    """Điền clip cho những câu bỏ trống. Trả về danh sách câu đã đủ clip."""
    blanks = sum(1 for line in doc.lines if not line.clip)
    if not blanks:
        return doc.lines

    choices = shots_mod.choose(
        doc.lines,
        timeline_mod.scene_seconds(doc, voices),
        library_mod.load(),
        PUBLIC_DIR,
        default_tags=doc.tags,
        log=log,
    )
    log(f"\n  Chọn clip cho {blanks}/{len(doc.lines)} câu bỏ trống:")
    for i, choice in enumerate(choices, start=1):
        if choice.automatic:
            log(f"    câu {i}: {choice.reason}")
    return shots_mod.apply(doc.lines, choices)


def _warn_if_off_target(doc, seconds: float, log) -> None:
    if not doc.target_seconds:
        return
    lo, hi = doc.target_seconds
    if lo <= seconds <= hi:
        return
    huong = "dài" if seconds > hi else "ngắn"
    log(
        f"\n[!] Video đang {huong} hơn khoảng mong muốn {lo:g}-{hi:g}s.\n"
        f"    Cách chỉnh: sửa \"rate\" (vd. \"+8%\" đọc nhanh hơn), giảm/tăng "
        f"\"pauseAfter\",\n    hoặc thêm/bớt câu trong \"lines\"."
    )


def _warn_if_clip_loops(doc, clips, timeline, log) -> None:
    """Cảnh nào clip ngắn hơn thoại thì Remotion cho chạy lặp — nói ra, đừng để tự phát hiện."""
    looping = [
        (i, clips[i - 1].path)
        for i, scene in enumerate(timeline.scenes, start=1)
        if scene.clip_duration_in_frames is not None
        and scene.clip_duration_in_frames < scene.duration_in_frames
    ]
    if looping:
        log("\n[!] Clip phải chạy lặp ở các cảnh: "
            + ", ".join(f"{i} ({name})" for i, name in looping))
        log("    Cắt từ điểm sớm hơn qua \"clipStartInSeconds\", hoặc thay clip dài hơn.")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Thiếu tham số. Ví dụ: make content DAY=2026-08-20", file=sys.stderr)
        return 2

    slug, flags = args[0], args[1:]

    # Đọc --still ra trước khi vào try, để ValueError của chỗ khác không bị
    # thông báo "thiếu số frame" nuốt mất.
    still_frame = None
    if "--still" in flags:
        rest = flags[flags.index("--still") + 1:]
        if not rest or not rest[0].lstrip("-").isdigit():
            print("--still cần một số frame. Ví dụ: make still DAY=2026-08-20 FRAME=300",
                  file=sys.stderr)
            return 2
        still_frame = int(rest[0])

    try:
        if still_frame is not None:
            # Chỉ vẽ một frame từ build.json đã có — không dựng lại nội dung,
            # vì mục đích của still là soi font và bố cục thật nhanh.
            print(f"Đã ghi {render.still(slug, still_frame).relative_to(ROOT)}")
            return 0

        build_day(slug)
        if "--render" in flags:
            print()
            dest = render.video(slug)
            # Đo lại file vừa dựng ra, không tin con số đã tính. Lệch giữa hai
            # số này nghĩa là Remotion và timeline đang hiểu khác nhau.
            print(f"\nXong: {dest.relative_to(ROOT)}")
            print(f"      thời lượng {duration_seconds(dest):.2f} giây")
    except (script_mod.ScriptError, tts.TTSError, ProbeError, LibraryError,
            reading_mod.ReadingError, render.RenderError) as exc:
        print(f"\n[lỗi] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
