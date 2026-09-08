"""
Lớp B — sổ đăng ký tài sản: clip nào ở đâu ra, ai làm, giấy phép nào.

Vì sao cần một cuốn sổ riêng thay vì cứ để file nằm trong studio/public/:
YouTube và TikTok đều quét bản quyền tự động, và câu hỏi "clip này lấy ở đâu"
chỉ có một thời điểm để trả lời rẻ — lúc vừa tải về. Sáu tháng sau thì không
ai nhớ nữa. Ba clip đang có suýt rơi vào đúng cái bẫy đó; may là lịch sử git
còn giữ tên file gốc nên truy ngược được.

Module này chỉ ĐỌC và GHI sổ. Nó không chọn clip cho cảnh nào (việc của
`shots.py`), không tải file về (việc của `fetch.py`), và tuyệt nhiên không
biết frame là gì (P-2).

Quy tắc: cái gì ffprobe đo được thì KHÔNG ghi vào sổ. Độ dài, bề ngang, fps —
đo tại chỗ. Sổ chỉ giữ những thứ không đo được: nguồn, tác giả, giấy phép, tag.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from .probe import MediaInfo, ProbeError, media_info

ROOT = Path(__file__).resolve().parent.parent
SHOTS_PATH = ROOT / "library" / "shots.json"

#: Hai ngăn của cuốn sổ. Chung một hình dạng, nên chung một lớp Entry.
SECTIONS = ("shots", "music")


class LibraryError(ValueError):
    """Sổ hỏng hoặc thiếu trường. Thông báo viết cho người đọc."""


@dataclass(frozen=True)
class Entry:
    """Một tài sản đã đăng ký. Chưa đo gì cả — số đo lấy bằng `measure()`."""

    id: str
    file: str
    kind: str  # "shots" | "music"
    tags: tuple[str, ...] = ()
    note: str = ""
    source: str = "manual"
    source_id: str = ""
    url: str = ""
    author: str = ""
    license: str = ""
    license_url: str = ""
    attribution_required: bool | None = None

    def matches(self, wanted: tuple[str, ...]) -> bool:
        """Có ít nhất một tag trùng. Không có tag mong muốn thì clip nào cũng hợp."""
        return not wanted or bool(set(wanted) & set(self.tags))


@dataclass
class Library:
    shots: list[Entry] = field(default_factory=list)
    music: list[Entry] = field(default_factory=list)

    def all(self) -> list[Entry]:
        return [*self.shots, *self.music]

    def by_file(self, rel_path: str) -> Entry | None:
        return next((e for e in self.all() if e.file == rel_path), None)

    def by_id(self, entry_id: str) -> Entry | None:
        return next((e for e in self.all() if e.id == entry_id), None)


def _entry(raw: object, kind: str, where: str) -> Entry:
    if not isinstance(raw, dict):
        raise LibraryError(f"{where} không phải object.")
    for key in ("id", "file"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            raise LibraryError(f"{where} thiếu \"{key}\".")

    tags = raw.get("tags", [])
    if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
        raise LibraryError(f"{where} có \"tags\" không phải danh sách chuỗi.")

    return Entry(
        id=raw["id"],
        file=raw["file"],
        kind=kind,
        tags=tuple(tags),
        note=raw.get("note", ""),
        source=raw.get("source", "manual"),
        source_id=str(raw.get("sourceId", "")),
        url=raw.get("url", ""),
        author=raw.get("author", ""),
        license=raw.get("license", ""),
        license_url=raw.get("licenseUrl", ""),
        attribution_required=raw.get("attributionRequired"),
    )


def load(path: Path = SHOTS_PATH) -> Library:
    """Đọc library/shots.json. Sổ chưa có thì trả về sổ rỗng, không phải lỗi."""
    if not path.exists():
        return Library()

    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LibraryError(f"{path} không phải JSON hợp lệ: {exc}") from exc
    if not isinstance(doc, dict):
        raise LibraryError(f"{path} phải là một object.")

    lib = Library()
    for section in SECTIONS:
        rows = doc.get(section, [])
        if not isinstance(rows, list):
            raise LibraryError(f"{path.name} có \"{section}\" phải là danh sách.")
        entries = [
            _entry(raw, section, f"{path.name} {section}[{i}]")
            for i, raw in enumerate(rows)
        ]
        setattr(lib, section, entries)

    _check_unique(lib, path.name)
    return lib


def _check_unique(lib: Library, where: str) -> None:
    """Trùng id hay trùng file đều là lỗi — bộ chọn sẽ chọn nhầm một cách âm thầm."""
    for label, key in (("id", lambda e: e.id), ("file", lambda e: e.file)):
        seen: dict[str, str] = {}
        for entry in lib.all():
            value = key(entry)
            if value in seen:
                raise LibraryError(
                    f"{where} có hai dòng cùng {label} \"{value}\" "
                    f"({seen[value]} và {entry.id})."
                )
            seen[value] = entry.id


def add(entry: dict, section: str, path: Path = SHOTS_PATH) -> None:
    """Ghi thêm một dòng vào sổ, giữ nguyên phần _doc và thứ tự các dòng cũ."""
    if section not in SECTIONS:
        raise LibraryError(f"Ngăn \"{section}\" không có. Chỉ có: {', '.join(SECTIONS)}.")

    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    doc.setdefault(section, [])

    existing = {row.get("id") for row in doc[section]}
    if entry["id"] in existing:
        raise LibraryError(
            f"Sổ đã có dòng id \"{entry['id']}\". Đặt tên khác, "
            f"hoặc xoá dòng cũ trong library/shots.json."
        )

    doc[section].append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Soi sổ — `make shots`
# ---------------------------------------------------------------------------

#: fps của video đích. Clip khác số này thì Remotion phải nhân đôi hoặc bỏ frame.
TARGET_FPS = 30
MIN_WIDTH = 1080

#: Nhạc ngắn hơn video thì phải lặp, và chỗ nối nghe rõ.
BGM_MIN_SECONDS = 60

#: md5 của những file mẫu từng nằm trong repo. Trùng md5 nghĩa là hàng mẫu lọt
#: lại vào, dù thư mục assets/ đã bị xoá từ BƯỚC 1.
PLACEHOLDERS = {
    "b402473130c79fdc8ec88f5f244fc796": "test tone của samplelib.com",
}


def measure(entry: Entry, public_dir: Path) -> MediaInfo | None:
    """Đo file thật. Không có file thì trả None chứ không ném lỗi."""
    try:
        return media_info(public_dir / entry.file)
    except ProbeError:
        return None


def audit(entry: Entry, info: MediaInfo | None, path: Path | None = None) -> list[str]:
    """Liệt kê những chỗ chưa ổn của một dòng sổ. Rỗng nghĩa là ổn."""
    issues = []
    if info is None:
        return [f"thiếu file {entry.file}"]

    if path is not None:
        sample = PLACEHOLDERS.get(hashlib.md5(path.read_bytes()).hexdigest())
        if sample:
            issues.append(f"vẫn là hàng mẫu — {sample}")

    if entry.kind == "music" and info.seconds < BGM_MIN_SECONDS:
        issues.append(
            f"chỉ {info.seconds:.0f}s, dưới {BGM_MIN_SECONDS}s thì phải lặp giữa video"
        )

    if entry.kind == "shots":
        if not info.is_vertical:
            issues.append(f"nằm ngang {info.width}×{info.height}, cần dọc")
        elif info.width and info.width < MIN_WIDTH:
            issues.append(f"chỉ rộng {info.width}px, cần ít nhất {MIN_WIDTH}")
        if info.fps and abs(info.fps - TARGET_FPS) > 0.01:
            issues.append(f"{info.fps:g}fps ≠ {TARGET_FPS}fps của video đích")

    if not entry.url:
        issues.append("chưa ghi nguồn (url)")
    if not entry.author:
        issues.append("chưa ghi tác giả")
    if not entry.license:
        issues.append("chưa ghi giấy phép")
    return issues


def _used_by(public_dir: Path) -> dict[str, list[str]]:
    """Mỗi file tài sản đang được những kịch bản nào gọi tên."""
    content_dir = public_dir.parent.parent / "content"
    used: dict[str, list[str]] = {}
    for src in sorted(content_dir.glob("*.json")):
        if src.name.endswith(".build.json") or src.name.startswith("."):
            continue
        try:
            doc = json.loads(src.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for ref in [doc.get("bgm"), *(l.get("clip") for l in doc.get("lines", []))]:
            if ref:
                used.setdefault(ref, []).append(src.stem)
    return used


def report(path: Path = SHOTS_PATH, public_dir: Path | None = None) -> int:
    """In cả cuốn sổ kèm số đo thật. Trả về số chỗ cần xử lý."""
    public_dir = public_dir or ROOT / "studio" / "public"
    lib = load(path)
    used = _used_by(public_dir)
    problems = 0

    for section, label in (("shots", "CLIP NỀN"), ("music", "NHẠC NỀN")):
        entries = getattr(lib, section)
        print(f"\n{label}  ({len(entries)} dòng)")
        if not entries:
            print("  (sổ chưa có dòng nào)")
            continue

        for entry in entries:
            info = measure(entry, public_dir)
            issues = audit(entry, info, (public_dir / entry.file) if info else None)
            problems += len(issues)

            size = ""
            if info:
                size = f"{info.seconds:.1f}s"
                if info.width:
                    size = f"{info.width}×{info.height}, {info.fps:g}fps, {size}"
            mark = "ok " if not issues else "!! "
            print(f"  [{mark}] {entry.id:<14} {size}")
            print(f"          {entry.file}   tags: {', '.join(entry.tags) or '(chưa gắn)'}")
            if entry.url or entry.author:
                who = entry.author or "tác giả chưa rõ"
                print(f"          {entry.source}: {who} — {entry.url or 'chưa có link'}")
            days = used.get(entry.file)
            print(f"          dùng cho: {', '.join(sorted(set(days))) if days else '(chưa ngày nào)'}")
            for issue in issues:
                print(f"          [!] {issue}")

    # Chiều ngược lại: file kịch bản gọi tên mà sổ không có dòng nào.
    orphans = sorted(ref for ref in used if lib.by_file(ref) is None)
    if orphans:
        print(f"\nCHƯA ĐĂNG KÝ  ({len(orphans)} file)")
        print("  Kịch bản đang dùng những file này mà sổ không có dòng nào —")
        print("  tức là không biết chúng ở đâu ra và có được phép dùng không.")
        for ref in orphans:
            print(f"  [!!] {ref}   ({', '.join(sorted(set(used[ref])))})")
        problems += len(orphans)

    print()
    if problems:
        print(f"{problems} chỗ cần xử lý. Sổ vẫn dùng được — đây là báo cáo, không phải cổng chặn.")
    else:
        print("Sổ đủ: mọi tài sản đều có file thật, có nguồn, có tác giả, có giấy phép.")
    return problems


def main(argv: list[str] | None = None) -> int:
    try:
        report()
    except (LibraryError, ProbeError) as exc:
        print(f"\n[lỗi] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
