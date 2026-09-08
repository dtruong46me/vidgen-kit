"""
Gọi Remotion. Đây là chỗ duy nhất trong Python biết Remotion tồn tại.

Module này giữ đúng một quy ước dễ sai: **Remotion phải chạy với cwd là
`studio/`** (nơi có package.json), nên mọi đường dẫn truyền vào nó là tương đối
so với `studio/` và phải có tiền tố `../`. Quy ước đó trước đây nằm rải trong ba
target của Makefile; gom về một hàm thì sai một lần là sai ở một chỗ.

Nó KHÔNG tính frame và KHÔNG đọc kịch bản — nó chỉ nhận một build.json đã có
sẵn rồi bảo Remotion vẽ ra.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

COMPOSITION = "Daily"

ROOT = Path(__file__).resolve().parent.parent
STUDIO_DIR = ROOT / "studio"
CONTENT_DIR = ROOT / "content"
OUT_DIR = ROOT / "out"


class RenderError(RuntimeError):
    """Remotion trả về mã lỗi. Đầu ra của nó đã in thẳng ra màn hình rồi."""


def _from_studio(path: Path) -> str:
    """Đường dẫn nhìn từ bên trong studio/ — đây là chỗ sinh ra tiền tố ../."""
    import os
    return os.path.relpath(path, STUDIO_DIR)


def _props_path(slug: str) -> Path:
    props = CONTENT_DIR / f"{slug}.build.json"
    if not props.exists():
        raise RenderError(
            f"Chưa có {props.relative_to(ROOT)} — chạy 'make content DAY={slug}' trước."
        )
    return props


def _run(args: list[str]) -> None:
    # Không nuốt stdout/stderr: thanh tiến trình của Remotion và thông báo lỗi
    # của nó là thứ đáng xem nhất khi render hỏng.
    proc = subprocess.run(["npx", "remotion", *args], cwd=STUDIO_DIR)
    if proc.returncode != 0:
        raise RenderError(f"Remotion dừng với mã {proc.returncode}. Xem log phía trên.")


def video(slug: str) -> Path:
    """build.json -> out/<slug>.mp4"""
    props = _props_path(slug)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / f"{slug}.mp4"
    _run([
        "render", COMPOSITION, _from_studio(dest),
        f"--props={_from_studio(props)}",
    ])
    return dest


def still(slug: str, frame: int) -> Path:
    """build.json -> out/<slug>-f<frame>.png — cách nhanh nhất bắt lỗi font và bố cục."""
    props = _props_path(slug)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / f"{slug}-f{frame}.png"
    _run([
        "still", COMPOSITION, _from_studio(dest),
        f"--frame={frame}",
        f"--props={_from_studio(props)}",
    ])
    return dest
