"""
Lớp B — tải clip mới về và ghi ngay vào sổ.

Tải và đăng ký là MỘT việc, không phải hai. Tách ra thì sẽ có ngày tải xong
quên ghi sổ, và sáu tháng sau không ai biết clip đó ở đâu ra — đúng cái bẫy mà
ba clip đầu tiên của dự án đã suýt rơi vào.

    make shots-find SOURCE=pexels Q="tea ceremony"
    make shots-get  SOURCE=pexels ID=8507912 NAME=matcha-whisk TAGS=tea,matcha
    make shots-add  FILE=~/quay/san-vuon.mp4 NAME=zen-garden \\
                    URL=... AUTHOR="..." LICENSE="CC0" TAGS=garden,calm

Khoá API đọc từ file `.env` ở gốc repo (xem `pipeline/env.py`), hoặc từ biến
môi trường thật — biến môi trường thắng file. `.env` nằm trong `.gitignore`
nên KHÔNG bao giờ lên git; `.env.example` mới là file được commit.

    make setup                    chép .env.example -> .env
    # rồi điền PEXELS_API_KEY / PIXABAY_API_KEY vào .env

Không có khoá thì `make shots-add` vẫn dùng được: tự tải bằng trình duyệt rồi
chỉ vào file. Chỉ có tìm kiếm và tải tự động là cần khoá.

Dùng urllib của thư viện chuẩn chứ không thêm `requests` — dây chuyền này gọi
mạng đúng hai chỗ (edge-tts và đây), không đáng thêm một phụ thuộc.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import env, library
from .probe import ProbeError, media_info

ROOT = Path(__file__).resolve().parent.parent
VIDEO_DIR = ROOT / "studio" / "public" / "video"

TIMEOUT = 30
MIN_WIDTH = 1080


class FetchError(RuntimeError):
    """Không tải được. Thông báo viết cho người đọc, không phải traceback."""


@dataclass(frozen=True)
class Candidate:
    """Một clip tìm được, chưa tải về."""

    provider: str
    source_id: str
    page_url: str
    author: str
    seconds: float
    width: int
    height: int
    fps: float | None
    download_url: str

    @property
    def is_vertical(self) -> bool:
        return self.height > self.width

    def line(self) -> str:
        fps = f"{self.fps:g}fps" if self.fps else "?fps"
        mark = " " if self.is_vertical and self.width >= MIN_WIDTH else "!"
        return (f"  {mark} {self.source_id:<12} {self.width}×{self.height} {fps:>7} "
                f"{self.seconds:5.1f}s  {self.author or '(không rõ)':<22} {self.page_url}")


# ---------------------------------------------------------------------------
# Hai nhà cung cấp. Mỗi nhà một cách gọi API, nhưng cùng trả về Candidate.
# ---------------------------------------------------------------------------

PROVIDERS = {
    "pexels": {
        "env": "PEXELS_API_KEY",
        "signup": "https://www.pexels.com/api/",
        "license": "Pexels License",
        "licenseUrl": "https://www.pexels.com/license/",
        "attributionRequired": False,
    },
    "pixabay": {
        "env": "PIXABAY_API_KEY",
        "signup": "https://pixabay.com/api/docs/",
        "license": "Pixabay Content License",
        "licenseUrl": "https://pixabay.com/service/license-summary/",
        "attributionRequired": False,
    },
}


def _key(provider: str) -> str:
    if provider not in PROVIDERS:
        raise FetchError(
            f"Chưa hỗ trợ nhà cung cấp \"{provider}\". "
            f"Đang có: {', '.join(PROVIDERS)}."
        )
    spec = PROVIDERS[provider]
    env.load()
    key = os.environ.get(spec["env"], "").strip()
    if not key:
        raise FetchError(
            f"Chưa có khoá API của {provider}.\n"
            f"    Đăng ký miễn phí ở {spec['signup']}\n"
            f"    {env.missing_hint(spec['env'])}\n"
            f"    (Hoặc bỏ qua API hẳn: tải bằng trình duyệt rồi `make shots-add`.)"
        )
    return key


def _get_json(url: str, headers: dict[str, str]) -> dict:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        hint = " — khoá API sai hoặc hết hạn" if exc.code in (401, 403) else ""
        raise FetchError(f"Máy chủ trả về HTTP {exc.code}{hint}: {url}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"Không nối được tới máy chủ: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise FetchError(f"Máy chủ trả về thứ không phải JSON: {url}") from exc


def _pexels(query: str | None, source_id: str | None, per_page: int) -> list[Candidate]:
    headers = {"Authorization": _key("pexels")}
    if source_id:
        doc = {"videos": [_get_json(
            f"https://api.pexels.com/videos/videos/{source_id}", headers
        )]}
    else:
        params = urllib.parse.urlencode({
            "query": query, "orientation": "portrait",
            "size": "medium", "per_page": per_page,
        })
        doc = _get_json(f"https://api.pexels.com/videos/search?{params}", headers)

    out = []
    for video in doc.get("videos", []):
        # Lấy bản dọc to nhất; không có bản dọc nào thì lấy bản to nhất để
        # người dùng còn thấy mà tự quyết định có crop hay không.
        files = video.get("video_files", []) or []
        vertical = [f for f in files if (f.get("height") or 0) > (f.get("width") or 0)]
        best = max(vertical or files, key=lambda f: f.get("width") or 0, default=None)
        if not best:
            continue
        out.append(Candidate(
            provider="pexels",
            source_id=str(video.get("id", "")),
            page_url=video.get("url", ""),
            author=(video.get("user") or {}).get("name", ""),
            seconds=float(video.get("duration") or 0),
            width=best.get("width") or 0,
            height=best.get("height") or 0,
            fps=best.get("fps"),
            download_url=best.get("link", ""),
        ))
    return out


def _pixabay(query: str | None, source_id: str | None, per_page: int) -> list[Candidate]:
    # Pixabay KHÔNG có tham số lọc hướng — khác Pexels. Phải xin nhiều rồi tự
    # lọc dọc phía mình, nếu không thì mười hai kết quả đầu toàn clip ngang.
    params = {"key": _key("pixabay"), "per_page": min(max(per_page * 6, 3), 200)}
    if source_id:
        params["id"] = source_id
    else:
        params["q"] = query
    doc = _get_json(
        f"https://pixabay.com/api/videos/?{urllib.parse.urlencode(params)}", {}
    )

    out = []
    for hit in doc.get("hits", []):
        sizes = (hit.get("videos") or {}).values()
        vertical = [v for v in sizes if (v.get("height") or 0) > (v.get("width") or 0)]
        best = max(vertical or sizes, key=lambda v: v.get("width") or 0, default=None)
        if not best:
            continue
        out.append(Candidate(
            provider="pixabay",
            source_id=str(hit.get("id", "")),
            page_url=hit.get("pageURL", ""),
            author=hit.get("user", ""),
            seconds=float(hit.get("duration") or 0),
            width=best.get("width") or 0,
            height=best.get("height") or 0,
            fps=None,  # Pixabay không trả fps; ffprobe đo sau khi tải.
            download_url=best.get("url", ""),
        ))
    return out


def _finder(provider: str):
    """Tra hàm gọi API. Kiểm tên provider ở ĐÂY chứ không để dict ném KeyError:
    gõ nhầm tên là chuyện thường, và người gõ nhầm cần một câu tiếng Việt chứ
    không cần một traceback."""
    try:
        return {"pexels": _pexels, "pixabay": _pixabay}[provider]
    except KeyError as exc:
        raise FetchError(
            f"Chưa hỗ trợ nhà cung cấp \"{provider}\". "
            f"Đang có: {', '.join(PROVIDERS)}."
        ) from exc


def search(provider: str, query: str, per_page: int = 12) -> list[Candidate]:
    return _finder(provider)(query, None, per_page)


def lookup(provider: str, source_id: str) -> Candidate:
    found = _finder(provider)(None, source_id, 3)
    if not found:
        raise FetchError(f"{provider} không có clip nào mang id {source_id}.")
    return found[0]


# ---------------------------------------------------------------------------
# Tải về và ghi sổ
# ---------------------------------------------------------------------------

def _slug_ok(name: str) -> str:
    if not name or not all(c.isalnum() or c in "-_" for c in name):
        raise FetchError(
            f"Tên \"{name}\" không hợp lệ. Chỉ dùng chữ không dấu, số, - và _.\n"
            f"    Đặt tên theo NỘI DUNG cảnh quay chứ đừng theo số thứ tự — "
            f"một clip thường dùng cho nhiều cảnh."
        )
    return name


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Tải ra file tạm rồi mới đổi tên: đứt mạng giữa chừng thì không để lại
    # một file mp4 cụt trong studio/public/ cho ffprobe vấp phải.
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp, tmp.open("wb") as fh:
            shutil.copyfileobj(resp, fh)
    except (urllib.error.URLError, OSError) as exc:
        tmp.unlink(missing_ok=True)
        raise FetchError(f"Tải hỏng: {exc}") from exc
    tmp.replace(dest)


def _register(entry: dict, name: str, dest: Path, verb: str) -> None:
    library.add(entry, "shots")
    info = media_info(dest)
    print(f"\n{verb} {dest.relative_to(ROOT)}")
    print(f"        {info.width}×{info.height}, {info.fps:g}fps, {info.seconds:.1f}s")
    print(f"Đã ghi sổ dòng \"{name}\" trong library/shots.json.")
    if not info.is_vertical:
        print("\n[!] Clip này NẰM NGANG. Xem docs/tai-san-can-tai.md để cắt về dọc.")
    if info.fps and abs(info.fps - library.TARGET_FPS) > 0.01:
        print(f"\n[!] Clip {info.fps:g}fps, video đích {library.TARGET_FPS}fps — "
              f"cảnh lia chậm sẽ hơi giật.")
    print("\nKiểm lại: make shots")


def get(provider: str, source_id: str, name: str, tags: tuple[str, ...]) -> Path:
    """Tải một clip theo id rồi ghi thẳng vào sổ."""
    name = _slug_ok(name)
    dest = VIDEO_DIR / f"{name}.mp4"
    if dest.exists():
        raise FetchError(f"Đã có {dest.relative_to(ROOT)}. Đặt NAME khác.")

    found = lookup(provider, source_id)
    if not found.download_url:
        raise FetchError(f"{provider} không cho link tải trực tiếp clip {source_id}.")

    print(f"Tải {found.width}×{found.height}, {found.seconds:.1f}s "
          f"của {found.author or '(không rõ)'}…")
    _download(found.download_url, dest)

    spec = PROVIDERS[provider]
    _register({
        "id": name,
        "file": f"video/{name}.mp4",
        "tags": list(tags),
        "note": "",
        "source": provider,
        "sourceId": found.source_id,
        "url": found.page_url,
        "author": found.author,
        "license": spec["license"],
        "licenseUrl": spec["licenseUrl"],
        "attributionRequired": spec["attributionRequired"],
    }, name, dest, "Đã tải  ")
    return dest


def add(
    src: Path, name: str, tags: tuple[str, ...],
    url: str, author: str, license_name: str, note: str = "",
) -> Path:
    """Nhận một file đã có sẵn trên máy vào thư viện.

    Bắt buộc khai url, tác giả và giấy phép. Không phải để hành: file không rõ
    nguồn mà lọt vào video đăng lên YouTube thì gỡ xuống tốn hơn nhiều.
    """
    name = _slug_ok(name)
    if not src.exists():
        raise FetchError(f"Không có file {src}.")
    missing = [
        label for label, value in
        (("URL", url), ("AUTHOR", author), ("LICENSE", license_name))
        if not value.strip()
    ]
    if missing:
        raise FetchError(
            f"Thiếu {', '.join(missing)}. Ba thứ này bắt buộc: sáu tháng nữa "
            f"không ai nhớ clip ở đâu ra, mà YouTube thì có nhớ."
        )

    dest = VIDEO_DIR / f"{name}.mp4"
    if dest.exists():
        raise FetchError(f"Đã có {dest.relative_to(ROOT)}. Đặt NAME khác.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)

    _register({
        "id": name,
        "file": f"video/{name}.mp4",
        "tags": list(tags),
        "note": note,
        "source": "manual",
        "sourceId": "",
        "url": url,
        "author": author,
        "license": license_name,
        "licenseUrl": "",
        "attributionRequired": None,
    }, name, dest, "Đã nhận ")
    return dest


# ---------------------------------------------------------------------------

USAGE = """Cách dùng:
    python3 -m pipeline.fetch find <pexels|pixabay> "<từ khoá>"
    python3 -m pipeline.fetch get  <pexels|pixabay> <id> <tên> [tag,tag]
    python3 -m pipeline.fetch add  <đường/dẫn/file.mp4> <tên> <url> <tác giả> <giấy phép> [tag,tag]

Thường thì gọi qua Makefile: make shots-find / shots-get / shots-add."""


def _tags(raw: str | None) -> tuple[str, ...]:
    return tuple(t.strip() for t in (raw or "").split(",") if t.strip())


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print(USAGE)
        return 2

    try:
        command, rest = args[0], args[1:]
        if command == "find" and len(rest) >= 2:
            found = search(rest[0], " ".join(rest[1:]))
            if not found:
                print("Không tìm thấy clip nào. Thử từ khoá khác.")
                return 0
            # Clip dùng được lên trước, rộng nhất lên trên. Bắt người đọc tự
            # dò trong danh sách lẫn lộn là cách chắc chắn để họ chọn nhầm.
            found.sort(key=lambda c: (not (c.is_vertical and c.width >= MIN_WIDTH), -c.width))
            good = sum(1 for c in found if c.is_vertical and c.width >= MIN_WIDTH)
            print(f"{len(found)} kết quả, {good} đạt chuẩn dọc ≥{MIN_WIDTH}px "
                  f"(dấu ! là không đạt):\n")
            for c in found[:20]:
                print(c.line())
            if good == 0:
                print("\nKhông clip nào dọc. Thử từ khoá khác, hoặc tải clip ngang "
                      "rồi cắt về dọc — xem docs/tai-san-can-tai.md.")
            print(f"\nTải một clip: make shots-get SOURCE={rest[0]} "
                  f"ID=<id> NAME=<tên> TAGS=tea,calm")
            return 0

        if command == "get" and len(rest) >= 3:
            get(rest[0], rest[1], rest[2], _tags(rest[3] if len(rest) > 3 else None))
            return 0

        if command == "add" and len(rest) >= 5:
            add(
                Path(rest[0]).expanduser(), rest[1],
                _tags(rest[5] if len(rest) > 5 else None),
                url=rest[2], author=rest[3], license_name=rest[4],
            )
            return 0

        print(USAGE)
        return 2
    except (FetchError, library.LibraryError, ProbeError) as exc:
        print(f"\n[lỗi] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
