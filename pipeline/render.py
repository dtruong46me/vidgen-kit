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
import sys
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
            f"Chưa có {props.relative_to(ROOT)} — chạy 'make build DAY={slug}' trước."
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
            f"{props.relative_to(ROOT)} soạn từ bản cũ, chưa có thumbnailFrame — "
            f"chạy 'make build DAY={slug}' rồi thử lại."
        )
    return _still(slug, frame, paths.thumbnail_path(slug))


def studio(slug: str | None = None) -> None:
    """Mở Remotion Studio bằng build.json THẬT của một ngày.

    Bỏ `slug` thì lấy ngày vừa soạn gần đây nhất (`paths.latest_built`). Chưa
    soạn ngày nào thì Studio mở bằng props mặc định viết thẳng trong
    Composition.tsx — một câu, nền gradient, không tiếng. Đó là đường lui để
    Studio có gì mà mở, không phải video thật, nên phải nói ra cho người xem biết.
    """
    slug = slug or paths.latest_built()
    if slug is None:
        print("Chưa có content/*/build.json nào — Studio mở bằng props mặc định.")
        print("Chạy 'make build DAY=2026-08-20' trước để xem video thật.")
        args = ["studio"]
    else:
        props = _props_path(slug)
        print(f"Studio nạp {props.relative_to(ROOT)}")
        args = ["studio", f"--props={_from_studio(props)}"]
    try:
        _run(args)
    except KeyboardInterrupt:
        # Ctrl+C là cách thoát Studio bình thường, không phải lỗi.
        pass


def main(argv: list[str] | None = None) -> int:
    """python3 -m pipeline.render studio [ngày] — cửa vào của `make studio`.

    Video, ảnh bìa và ảnh tĩnh đi qua `pipeline.run`, vì chúng cần soạn trước.
    Studio thì không: nó chỉ mở build.json đã có, nên gọi thẳng vào đây.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] != "studio" or len(args) > 2:
        print("Cách dùng: python3 -m pipeline.render studio [ngày]", file=sys.stderr)
        return 2
    try:
        studio(args[1] if len(args) == 2 else None)
    except RenderError as exc:
        print(f"[lỗi] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
