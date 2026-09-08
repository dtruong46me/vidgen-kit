#!/usr/bin/env python3
"""
BẢN CŨ — giữ lại làm đường quay lui cho BƯỚC 2 (xem CLAUDE.md).
Sẽ bị pipeline/ thay thế; đừng thêm tính năng mới vào đây.

Chuẩn bị nguyên liệu cho 1 video: TTS từng câu -> đo độ dài -> sinh file build JSON.

Cách dùng:
    python3 scripts/legacy_build.py 2026-08-20

Đầu vào : content/<slug>.json          (kịch bản do bạn viết)
Đầu ra  : public/audio/<slug>/line-XX.mp3   (giọng đọc từng câu)
          content/<slug>.build.json         (props để Remotion render)

Yêu cầu: pip install edge-tts   +   ffprobe (đi kèm ffmpeg)
"""

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
PUBLIC_DIR = ROOT / "studio" / "public"


def ffprobe_duration(path: Path) -> float:
    """Đọc độ dài thật (giây) của file audio."""
    out = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def tts(text: str, voice: str, rate: str, pitch: str, out_path: Path) -> None:
    """Gọi edge-tts sinh file mp3 cho 1 câu."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable, "-m", "edge_tts",
            "--voice", voice,
            # dùng dạng --rate=-10% vì giá trị âm sẽ bị argparse hiểu nhầm là tên flag
            f"--rate={rate}",
            f"--pitch={pitch}",
            "--text", text,
            "--write-media", str(out_path),
        ],
        check=True,
        capture_output=True,
    )


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Thiếu tham số. Ví dụ: python3 scripts/build.py 2026-08-20")

    slug = sys.argv[1]
    src = CONTENT_DIR / f"{slug}.json"
    if not src.exists():
        sys.exit(f"Không tìm thấy {src}")

    doc = json.loads(src.read_text(encoding="utf-8"))
    fps = doc.get("fps", 30)
    voice = doc.get("voice", "ja-JP-NanamiNeural")
    rate = doc.get("rate", "+0%")
    pitch = doc.get("pitch", "+0Hz")
    lead_in = doc.get("leadIn", 0.35)
    pause_after = doc.get("pauseAfter", 0.7)

    # cache: câu nào không đổi thì không gọi TTS lại (tiết kiệm thời gian khi làm hàng loạt)
    cache_path = CONTENT_DIR / f".{slug}.cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    new_cache = {}

    out_lines = []
    for i, line in enumerate(doc["lines"], start=1):
        name = f"line-{i:02d}.mp3"
        rel_audio = f"audio/{slug}/{name}"
        abs_audio = PUBLIC_DIR / rel_audio

        fingerprint = hashlib.sha1(
            f"{line['ja']}|{voice}|{rate}|{pitch}".encode("utf-8")
        ).hexdigest()
        new_cache[name] = fingerprint

        if cache.get(name) == fingerprint and abs_audio.exists():
            print(f"  [cache] {name}")
        else:
            print(f"  [tts]   {name}  {line['ja'][:24]}...")
            tts(line["ja"], voice, rate, pitch, abs_audio)

        audio_sec = ffprobe_duration(abs_audio)
        audio_frames = math.ceil(audio_sec * fps)
        scene_frames = math.ceil((lead_in + audio_sec + pause_after) * fps)

        # clip nền: chỉ dùng nếu file thật sự tồn tại trong public/, không thì để null
        clip = line.get("clip")
        clip_start = line.get("clipStartInSeconds", 0)
        clip_frames = None
        if clip and not (PUBLIC_DIR / clip).exists():
            print(f"          (thiếu {clip} -> dùng nền gradient)")
            clip = None
            clip_start = 0
        elif clip:
            clip_seconds = ffprobe_duration(PUBLIC_DIR / clip)
            if clip_start >= clip_seconds:
                print(
                    f"          (clipStartInSeconds={clip_start} vượt quá độ dài "
                    f"clip {clip_seconds:.1f}s -> cắt từ đầu)"
                )
                clip_start = 0
            # Đo phần CÒN LẠI SAU ĐIỂM CẮT, không phải cả clip.
            # Background.tsx cắt clip bằng trimBefore rồi loop theo đúng số này;
            # nếu ghi cả độ dài clip thì vòng lặp sẽ chạy quá phần thật sự có hình.
            clip_frames = math.floor((clip_seconds - clip_start) * fps)

        out_lines.append({
            "ja": line["ja"],
            "romaji": line.get("romaji", ""),
            "vi": line.get("vi", ""),
            "audio": rel_audio,
            "audioDurationInFrames": audio_frames,
            "durationInFrames": scene_frames,
            "audioStartInFrames": round(lead_in * fps),
            "clip": clip,
            "clipDurationInFrames": clip_frames,
            "clipStartInSeconds": clip_start,
        })

    bgm = doc.get("bgm")
    bgm_frames = None
    if bgm and not (PUBLIC_DIR / bgm).exists():
        print(f"  (thiếu nhạc nền {bgm} -> bỏ qua)")
        bgm = None
    elif bgm:
        bgm_frames = math.floor(ffprobe_duration(PUBLIC_DIR / bgm) * fps)

    build = {
        "id": doc["id"],
        "title": doc.get("title", doc["id"]),
        "fps": fps,
        "width": doc.get("width", 1080),
        "height": doc.get("height", 1920),
        "bgm": bgm,
        "bgmDurationInFrames": bgm_frames,
        "bgmVolume": doc.get("bgmVolume", 0.12),
        "lines": out_lines,
    }

    dest = CONTENT_DIR / f"{slug}.build.json"
    dest.write_text(json.dumps(build, ensure_ascii=False, indent=2), encoding="utf-8")
    cache_path.write_text(json.dumps(new_cache, indent=2), encoding="utf-8")

    total = sum(l["durationInFrames"] for l in out_lines)
    seconds = total / fps
    print(f"\nĐã ghi {dest.relative_to(ROOT)}")
    print(f"{len(out_lines)} câu — tổng {total} frame = {seconds:.1f} giây")

    lo, hi = doc.get("targetSeconds", [0, 0])
    if hi and not (lo <= seconds <= hi):
        huong = "dài" if seconds > hi else "ngắn"
        print(
            f"\n[!] Video đang {huong} hơn khoảng mong muốn {lo}-{hi}s.\n"
            f"    Cách chỉnh: sửa \"rate\" (vd. \"+8%\" đọc nhanh hơn), giảm/tăng \"pauseAfter\",\n"
            f"    hoặc thêm/bớt câu trong \"lines\"."
        )


if __name__ == "__main__":
    main()
