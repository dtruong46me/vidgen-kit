"""
Gọi Remotion. Đây là chỗ duy nhất trong Python biết Remotion tồn tại.

Module này giữ đúng một quy ước dễ sai: **Remotion phải chạy với cwd là
`studio/`** (nơi có package.json), nên mọi đường dẫn truyền vào nó là tương đối
so với `studio/` và phải có tiền tố `../`. Quy ước đó trước đây nằm rải trong ba
target của Makefile; gom về một hàm thì sai một lần là sai ở một chỗ.

Nó KHÔNG tính frame và KHÔNG đọc kịch bản — nó chỉ nhận một build.json đã có
sẵn rồi bảo Remotion vẽ ra.

Nó cũng không tự đặt tên file ra: nằm ở đâu là chuyện của `paths.py`. Video và
ảnh bìa đi thẳng vào thư mục ngày `out/<ngày>/`, cạnh caption và giọng đọc mà
`export.py` gói — một ngày một thư mục, không chép qua chép lại.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from . import paths

COMPOSITION = "Daily"

ROOT = Path(__file__).resolve().parent.parent
STUDIO_DIR = ROOT / "studio"
CONTENT_DIR = ROOT / "content"
OUT_DIR = paths.OUT_DIR


class RenderError(RuntimeError):
    """Remotion trả về mã lỗi. Đầu ra của nó đã in thẳng ra màn hình rồi."""


def _from_studio(path: Path) -> str:
    """Đường dẫn nhìn từ bên trong studio/ — đây là chỗ sinh ra tiền tố ../."""
    return os.path.relpath(path, STUDIO_DIR)


def _props_path(slug: str) -> Path:
    props = paths.build_path(slug)
    if not props.exists():
        raise RenderError(
            f"Chưa có {props.relative_to(ROOT)} — chạy 'make content DAY={slug}' trước."
        )
    return props


def _npx() -> str:
    """Đường dẫn tới npx, hỏi y như shell hỏi.

    Trên Windows npx là `npx.cmd`, mà subprocess không tự thêm đuôi như shell:
    gọi trần "npx" ra WinError 2 "không tìm thấy file" dù Node đã cài đủ.
    """
    found = shutil.which("npx")
    if not found:
        raise RenderError("Không thấy npx trên PATH — cài Node 18 trở lên (xem docs/cai-dat.md).")
    return found


def _run(args: list[str]) -> None:
    # Thiếu node_modules thì npx chỉ báo "could not determine executable to run",
    # không nói thiếu gì — chặn trước bằng một câu dễ hiểu.
    # `lexists`, không phải `Path.exists()`: `.bin/remotion` có thể là symlink
    # mà Windows không đi theo được (node_modules cài từ WSL). Lúc đó
    # `Path.exists()` NÉM OSError [WinError 1920] chứ không trả về False, và cả
    # lệnh chết ở đúng dòng kiểm tra — nghịch lý, vì dòng này sinh ra để thay
    # một thông báo khó hiểu bằng một câu dễ hiểu. `lexists` chỉ hỏi "có cái tên
    # đó không", không đi theo liên kết, nên nó trả lời được.
    if not os.path.lexists(STUDIO_DIR / "node_modules" / ".bin" / "remotion"):
        raise RenderError("Chưa cài Remotion (studio/node_modules trống) — chạy 'make setup' trước.")
    # Không nuốt stdout/stderr: thanh tiến trình của Remotion và thông báo lỗi
    # của nó là thứ đáng xem nhất khi render hỏng.
    try:
        proc = subprocess.run([_npx(), "remotion", *args], cwd=STUDIO_DIR)
    except OSError as exc:
        raise RenderError(f"Không gọi được npx: {exc}") from exc
    if proc.returncode != 0:
        raise RenderError(f"Remotion dừng với mã {proc.returncode}. Xem log phía trên.")


def video(slug: str) -> Path:
    """build.json -> out/<slug>/<slug>.mp4"""
    props = _props_path(slug)
    dest = paths.video_path(slug)
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "render", COMPOSITION, _from_studio(dest),
        f"--props={_from_studio(props)}",
    ])
    return dest


def _still(slug: str, frame: int, dest: Path) -> Path:
    props = _props_path(slug)
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "still", COMPOSITION, _from_studio(dest),
        f"--frame={frame}",
        f"--props={_from_studio(props)}",
    ])
    return dest


def still(slug: str, frame: int) -> Path:
    """build.json -> out/<slug>-f<frame>.png — cách nhanh nhất bắt lỗi font và bố cục."""
    return _still(slug, frame, paths.still_path(slug, frame))


def thumbnail(slug: str) -> Path:
    """build.json -> out/<slug>/<slug>-thumbnail.png — ảnh bìa: ngày tháng và câu chào cùng trên hình.

    Frame lấy từ `thumbnailFrame` trong build.json, do timeline.py chọn. Module
    này chỉ đọc số đó, không tự đoán frame nào đẹp (P-2).
    """
    props = _props_path(slug)
    frame = json.loads(props.read_text(encoding="utf-8")).get("thumbnailFrame")
    if frame is None:
        raise RenderError(
            f"{props.relative_to(ROOT)} dựng từ bản cũ, chưa có thumbnailFrame — "
            f"chạy 'make content DAY={slug}' rồi thử lại."
        )
    return _still(slug, frame, paths.thumbnail_path(slug))
