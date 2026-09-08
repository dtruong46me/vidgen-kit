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

# md5 của những file mẫu từng nằm trong repo. Trùng md5 nghĩa là hàng mẫu
# lọt lại vào, dù thư mục assets/ đã bị xoá.
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


def scripts_in(content_dir: Path) -> list[dict]:
    """Đọc mọi kịch bản người viết, bỏ qua file build.json do máy sinh."""
    out = []
    for src in sorted(content_dir.glob("*.json")):
        if src.name.endswith(".build.json"):
            continue
        doc = json.loads(src.read_text(encoding="utf-8"))
        doc["_slug"] = src.stem
        out.append(doc)
    return out


def main() -> None:
    problems = 0
    docs = scripts_in(CONTENT_DIR)

    # ---- nhạc nền ------------------------------------------------------
    # Đường dẫn nhạc nền do kịch bản khai báo, không cắm cứng ở đây: mỗi ngày
    # có thể dùng một bản nhạc khác.
    print("NHẠC NỀN")
    wanted_bgm: dict[str, list[str]] = {}
    for doc in docs:
        if doc.get("bgm"):
            wanted_bgm.setdefault(doc["bgm"], []).append(doc["_slug"])

    if not wanted_bgm:
        print("  (chưa kịch bản nào khai báo nhạc nền)")

    for bgm, days in sorted(wanted_bgm.items()):
        path = PUBLIC_DIR / bgm
        used = ", ".join(sorted(set(days)))
        if not path.exists():
            print(f"  [thiếu]  {bgm} — video sẽ không có nhạc  ({used})")
            problems += 1
            continue
        note = PLACEHOLDERS.get(md5(path))
        seconds = probe(path)["seconds"]
        if note:
            print(f"  [mẫu]    {bgm} — {note} ({seconds:.1f}s)  ({used})")
            problems += 1
        elif seconds < BGM_MIN_SECONDS:
            print(f"  [ngắn]   {bgm} — {seconds:.1f}s, dưới {BGM_MIN_SECONDS}s thì phải lặp  ({used})")
            problems += 1
        else:
            print(f"  [ok]     {bgm} — {seconds:.1f}s  ({used})")

    # ---- clip nền ------------------------------------------------------
    # Chỉ soi những clip mà kịch bản thật sự gọi tên, không soi cả thư mục.
    wanted: dict[str, list[str]] = {}
    for doc in docs:
        for line in doc.get("lines", []):
            if line.get("clip"):
                wanted.setdefault(line["clip"], []).append(doc["_slug"])

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
