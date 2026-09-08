#!/usr/bin/env python3
"""
Soi tài sản media: file nào còn thiếu, file nào còn là hàng mẫu.

Cách dùng:
    make assets

Chỉ ĐỌC, không sửa gì, và luôn thoát bằng 0 — đây là bản báo cáo chứ không phải
cổng chặn. Cổng chặn thật sự là `make check` ở BƯỚC 6.

Xem docs/tai-san-can-tai.md để biết tải ở đâu, lưu vào đâu.
"""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
PUBLIC_DIR = ROOT / "studio" / "public"

# md5 của mấy file mẫu trong assets/. Trùng md5 nghĩa là chưa thay hàng thật.
PLACEHOLDERS = {
    "b402473130c79fdc8ec88f5f244fc796": "test tone của samplelib.com",
}

# Nhạc nền ngắn hơn video thì phải lặp, và chỗ nối nghe rõ.
BGM_MIN_SECONDS = 60


def probe(path: Path) -> dict:
    """Đọc kích thước và độ dài thật của một file media."""
    out = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=width,height:format=duration",
            "-of", "json",
            str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    doc = json.loads(out.stdout)
    streams = doc.get("streams", [{}])
    video = next((s for s in streams if s.get("width")), {})
    return {
        "width": video.get("width"),
        "height": video.get("height"),
        "seconds": float(doc.get("format", {}).get("duration", 0)),
    }


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main() -> None:
    problems = 0

    # ---- nhạc nền ------------------------------------------------------
    print("NHẠC NỀN")
    bgm = PUBLIC_DIR / "audio" / "bgm.mp3"
    if not bgm.exists():
        print("  [thiếu]  audio/bgm.mp3")
        problems += 1
    else:
        note = PLACEHOLDERS.get(md5(bgm))
        seconds = probe(bgm)["seconds"]
        if note:
            print(f"  [mẫu]    audio/bgm.mp3 — {note} ({seconds:.1f}s)")
            problems += 1
        elif seconds < BGM_MIN_SECONDS:
            print(f"  [ngắn]   audio/bgm.mp3 — {seconds:.1f}s, dưới {BGM_MIN_SECONDS}s thì phải lặp")
            problems += 1
        else:
            print(f"  [ok]     audio/bgm.mp3 — {seconds:.1f}s")

    # ---- clip nền ------------------------------------------------------
    # Chỉ soi những clip mà kịch bản thật sự gọi tên, không soi cả thư mục.
    wanted: dict[str, list[str]] = {}
    for src in sorted(CONTENT_DIR.glob("*.json")):
        if src.name.endswith(".build.json") or src.name.startswith("_"):
            continue
        doc = json.loads(src.read_text(encoding="utf-8"))
        for line in doc.get("lines", []):
            if line.get("clip"):
                wanted.setdefault(line["clip"], []).append(src.stem)

    print("\nCLIP NỀN")
    if not wanted:
        print("  (chưa kịch bản nào khai báo clip)")

    for clip, days in sorted(wanted.items()):
        path = PUBLIC_DIR / clip
        used = ", ".join(sorted(set(days)))
        if not path.exists():
            print(f"  [thiếu]  {clip} — cảnh này đang dùng nền gradient  ({used})")
            problems += 1
            continue

        info = probe(path)
        w, h = info["width"], info["height"]
        note = PLACEHOLDERS.get(md5(path))
        if note:
            print(f"  [mẫu]    {clip} — {note}  ({used})")
            problems += 1
        elif not w or h <= w:
            print(f"  [ngang]  {clip} — {w}×{h}, cần DỌC 1080×1920  ({used})")
            problems += 1
        elif w < 1080:
            print(f"  [nhỏ]    {clip} — {w}×{h}, cần rộng ít nhất 1080  ({used})")
            problems += 1
        else:
            print(f"  [ok]     {clip} — {w}×{h}, {info['seconds']:.1f}s  ({used})")

    print()
    if problems:
        print(f"{problems} chỗ cần xử lý. Xem docs/tai-san-can-tai.md.")
        print("Thiếu clip KHÔNG làm hỏng video — cảnh đó rơi về nền gradient.")
        return

    print("Tài sản đủ và đúng chuẩn.")


if __name__ == "__main__":
    main()
