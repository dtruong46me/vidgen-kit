"""
Chỗ DUY NHẤT biết `content/` và `out/` được bày ra sao.

Một ngày là một thư mục, và trong đó ba file có ba vai trò khác hẳn nhau:

    content/2026-09-11/
      script.json    NGƯỜI viết. Vào git.
      build.json     MÁY sinh. HỢP ĐỒNG với Remotion. Không vào git.
      .cache.json    MÁY sinh. Chỉ là cache của TTS. Không vào git.

Trước BƯỚC 8 ba thứ này nằm phẳng cạnh nhau (`2026-09-11.json`,
`2026-09-11.build.json`, `.2026-09-11.cache.json`), nên `content/` của một tháng
có 90 file và mắt không tách nổi cái nào là của mình viết. Giờ mở một thư mục ra
là thấy đủ một ngày.

`out/` theo đúng tinh thần đó — một ngày một thư mục, trong đó đủ thứ để ĐĂNG:

    out/2026-09-12/
      2026-09-12.mp4            render.py dựng thẳng vào đây
      2026-09-12-thumbnail.png  render.py dựng thẳng vào đây
      caption.txt, …, audio/    export.py viết

Trước đây video và ảnh bìa nằm lẻ ở `out/<ngày>.mp4` rồi được CHÉP vào thư mục
gói: mỗi video nằm hai chỗ, và `out/` của một tháng là 60 file lẻ lẫn giữa 30
thư mục. Hai thứ còn nằm ngoài thư mục ngày là đồ để SOÁT, không phải để đăng:
trang duyệt của `make check` và ảnh tĩnh của `make still`.

Mọi module khác PHẢI hỏi ở đây, không được tự ghép chuỗi. Đó là cùng một lý do
khiến `probe.py` là chỗ duy nhất gọi ffprobe và `timeline.py` là chỗ duy nhất
tính frame: đổi bố cục thư mục thì chỉ có một file phải sửa.

Chọn NHIỀU ngày (`select`) cũng nằm ở đây, vì chọn ngày chính là hỏi "`content/`
đang có những ngày nào" — Makefile hỏi qua `python3 -m pipeline.paths`.

`.cache.json` để riêng được hay không? Được — nó chỉ chứa vân tay SHA1 của
`(câu Nhật | giọng | tốc độ | cao độ)` từng dòng, để `make content` biết câu nào
KHÔNG phải đọc lại. Xoá nó đi thì video dựng ra y hệt, chỉ tốn thêm một lượt gọi
edge-tts. Nó nằm chung thư mục ngày vì nó thuộc về ngày đó, và có dấu chấm đầu
tên để không chen vào giữa hai file người ta thật sự mở ra đọc.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
OUT_DIR = ROOT / "out"

SCRIPT_NAME = "script.json"
BUILD_NAME = "build.json"
CACHE_NAME = ".cache.json"


def day_dir(slug: str, content_dir: Path = CONTENT_DIR) -> Path:
    """content/<slug>/"""
    return content_dir / slug


def script_path(slug: str, content_dir: Path = CONTENT_DIR) -> Path:
    """Kịch bản người viết."""
    return day_dir(slug, content_dir) / SCRIPT_NAME


def build_path(slug: str, content_dir: Path = CONTENT_DIR) -> Path:
    """Hợp đồng với Remotion."""
    return day_dir(slug, content_dir) / BUILD_NAME


def cache_path(slug: str, content_dir: Path = CONTENT_DIR) -> Path:
    """Cache TTS. Xoá được, chỉ mất công đọc lại."""
    return day_dir(slug, content_dir) / CACHE_NAME


def slugs(content_dir: Path = CONTENT_DIR) -> list[str]:
    """Mọi ngày CÓ kịch bản, xếp theo tên tức theo ngày."""
    return sorted(p.parent.name for p in content_dir.glob(f"*/{SCRIPT_NAME}"))


def built_slugs(content_dir: Path = CONTENT_DIR) -> list[str]:
    """Mọi ngày ĐÃ dựng nội dung."""
    return sorted(p.parent.name for p in content_dir.glob(f"*/{BUILD_NAME}"))


def script_paths(content_dir: Path = CONTENT_DIR) -> list[Path]:
    """Đường dẫn mọi kịch bản. Dùng khi cần đọc cả loạt (make new, make shots)."""
    return [script_path(slug, content_dir) for slug in slugs(content_dir)]


def legacy_script(slug: str, content_dir: Path = CONTENT_DIR) -> Path | None:
    """Kịch bản kiểu CŨ nằm phẳng ở `content/<slug>.json`, nếu còn sót.

    Trả về đường dẫn để người gọi in ra một câu hướng dẫn chuyển, chứ KHÔNG tự
    đọc nó. Đọc lẳng lặng thì hai bố cục cùng sống mãi và không ai biết file
    nào đang thật sự được dùng.
    """
    old = content_dir / f"{slug}.json"
    return old if old.exists() else None


def move_hint(slug: str, content_dir: Path = CONTENT_DIR) -> str:
    """Câu hướng dẫn chuyển một ngày từ bố cục cũ sang mới."""
    return (
        f"Thấy {(content_dir / f'{slug}.json').name} theo bố cục CŨ. "
        f"Chuyển nó vào thư mục ngày:\n"
        f"    mkdir -p content/{slug} && "
        f"git mv content/{slug}.json content/{slug}/{SCRIPT_NAME}"
    )


# --------------------------------------------------------------------------
# out/
# --------------------------------------------------------------------------

def out_dir(slug: str, out_root: Path = OUT_DIR) -> Path:
    """out/<slug>/ — gói đăng của một ngày."""
    return out_root / slug


def video_path(slug: str, out_root: Path = OUT_DIR) -> Path:
    """Video để đăng."""
    return out_dir(slug, out_root) / f"{slug}.mp4"


def thumbnail_path(slug: str, out_root: Path = OUT_DIR) -> Path:
    """Ảnh bìa."""
    return out_dir(slug, out_root) / f"{slug}-thumbnail.png"


def still_path(slug: str, frame: int, out_root: Path = OUT_DIR) -> Path:
    """Ảnh tĩnh của `make still` — đồ soát, nên nằm NGOÀI thư mục đăng."""
    return out_root / f"{slug}-f{frame}.png"


def check_dir(slug: str, out_root: Path = OUT_DIR) -> Path:
    """Trang duyệt của `make check` — đồ soát, nên nằm NGOÀI thư mục đăng."""
    return out_root / f"{slug}-check"


def legacy_outputs(slug: str, out_root: Path = OUT_DIR) -> list[tuple[Path, Path]]:
    """(chỗ CŨ, chỗ MỚI) của video và ảnh bìa, từ thời chúng còn nằm lẻ ngoài `out/`."""
    return [
        (out_root / f"{slug}.mp4", video_path(slug, out_root)),
        (out_root / f"{slug}-thumbnail.png", thumbnail_path(slug, out_root)),
    ]


# --------------------------------------------------------------------------
# Chọn nhiều ngày
# --------------------------------------------------------------------------

#: Một đầu mút của khoảng: năm, tháng, hoặc ngày.
_BOUND = re.compile(r"\d{4}(-\d{2}(-\d{2})?)?")
#: Chỉ ngày thật mới được chọn theo khoảng — kịch bản đặt tên khác (vd. `demo`)
#: thì gọi đúng tên nó.
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}")

SPEC_HELP = (
    "Viết kiểu 2026-09-12 (một ngày), 2026-09 (cả tháng), "
    "2026-09-12..2026-09-30 (từ ngày tới ngày), hoặc 2026-09-12.. (tới ngày cuối cùng)."
)


class SpecError(ValueError):
    """Chuỗi chọn ngày viết sai. Thông báo viết cho người đọc."""


def is_range(spec: str) -> bool:
    """`spec` chọn NHIỀU ngày (có `..`, hoặc chỉ ghi tháng/năm) chứ không phải tên một ngày."""
    return ".." in spec or bool(re.fullmatch(r"\d{4}(-\d{2})?", spec))


def select(spec: str, pool: list[str]) -> list[str]:
    """Những ngày trong `pool` khớp `spec`, xếp theo ngày.

        2026-09-12              đúng một ngày
        2026-09                 cả tháng
        2026-09-12..2026-09-30  từ ngày tới ngày, TÍNH CẢ HAI ĐẦU
        2026-09-12..            từ ngày đó tới ngày cuối cùng đang có
        ..2026-09-15            từ ngày đầu tiên tới ngày đó

    So theo TIỀN TỐ, nên đầu mút ghi tháng là cả tháng: `2026-09..2026-10` là
    từ 1/9 tới hết 31/10. Nhờ tên ngày viết ISO, so chuỗi chính là so ngày —
    không phải đổi ra `date` rồi đoán tháng có bao nhiêu ngày.
    """
    lo, sep, hi = spec.partition("..")
    if not sep:
        hi = lo
    if not lo and not hi:
        raise SpecError(f"'{spec}' không có ngày nào. {SPEC_HELP}")
    for bound in (lo, hi):
        if bound and not _BOUND.fullmatch(bound):
            raise SpecError(f"Không hiểu '{bound}' trong '{spec}'. {SPEC_HELP}")
    return [
        slug for slug in sorted(pool)
        if _DAY.fullmatch(slug)
        and (not lo or slug[:len(lo)] >= lo)
        and (not hi or slug[:len(hi)] <= hi)
    ]


def span(days: list[str]) -> str:
    """Tóm tắt một dãy ngày cho log: liệt kê nếu ít, gọn đầu–cuối nếu nhiều."""
    if len(days) <= 6:
        return ", ".join(days)
    return f"{days[0]} … {days[-1]} ({len(days)} ngày)"


def main(argv: list[str] | None = None) -> int:
    """In các ngày khớp, mỗi dòng một ngày — cho vòng lặp trong Makefile.

        python3 -m pipeline.paths 2026-09-12..          ngày CÓ kịch bản
        python3 -m pipeline.paths 2026-09 --built       ngày ĐÃ dựng nội dung
    """
    args = list(sys.argv[1:] if argv is None else argv)
    built = "--built" in args
    specs = [a for a in args if a != "--built"]
    if len(specs) != 1:
        print(f"Cách dùng: python3 -m pipeline.paths <ngày> [--built]\n{SPEC_HELP}",
              file=sys.stderr)
        return 2
    spec = specs[0]
    pool = built_slugs() if built else slugs()
    try:
        chosen = select(spec, pool) if is_range(spec) else [s for s in pool if s == spec]
    except SpecError as exc:
        print(f"[lỗi] {exc}", file=sys.stderr)
        return 2
    if not chosen:
        what = "đã dựng nội dung" if built else "có kịch bản"
        print(f"[lỗi] Không ngày nào khớp '{spec}' mà {what}. "
              f"Đang có: {span(pool) or '(chưa có ngày nào)'}", file=sys.stderr)
        return 1
    # Ghi byte LF trần: Python trên Windows đổi "\n" thành "\r\n", và bash giữ
    # nguyên "\r" dính vào tên ngày cuối cùng — `make release` sẽ đi tìm
    # "2026-09-30\r".
    sys.stdout.buffer.write(("\n".join(chosen) + "\n").encode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
