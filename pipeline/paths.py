"""
Chỗ DUY NHẤT biết `content/` được bày ra sao.

Một ngày là một thư mục, và trong đó ba file có ba vai trò khác hẳn nhau:

    content/2026-09-11/
      script.json    NGƯỜI viết. Vào git.
      build.json     MÁY sinh. HỢP ĐỒNG với Remotion. Không vào git.
      .cache.json    MÁY sinh. Chỉ là cache của TTS. Không vào git.

Trước BƯỚC 8 ba thứ này nằm phẳng cạnh nhau (`2026-09-11.json`,
`2026-09-11.build.json`, `.2026-09-11.cache.json`), nên `content/` của một tháng
có 90 file và mắt không tách nổi cái nào là của mình viết. Giờ mở một thư mục ra
là thấy đủ một ngày.

Mọi module khác PHẢI hỏi ở đây, không được tự ghép chuỗi. Đó là cùng một lý do
khiến `probe.py` là chỗ duy nhất gọi ffprobe và `timeline.py` là chỗ duy nhất
tính frame: đổi bố cục thư mục thì chỉ có một file phải sửa.

`.cache.json` để riêng được hay không? Được — nó chỉ chứa vân tay SHA1 của
`(câu Nhật | giọng | tốc độ | cao độ)` từng dòng, để `make content` biết câu nào
KHÔNG phải đọc lại. Xoá nó đi thì video dựng ra y hệt, chỉ tốn thêm một lượt gọi
edge-tts. Nó nằm chung thư mục ngày vì nó thuộc về ngày đó, và có dấu chấm đầu
tên để không chen vào giữa hai file người ta thật sự mở ra đọc.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"

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
