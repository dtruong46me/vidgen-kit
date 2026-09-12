"""
Đọc khoá API từ file `.env` ở gốc repo.

Vì sao có module này thay vì bắt người dùng `export` mỗi lần mở terminal:
`export` chỉ sống trong đúng cái shell đó. Đóng terminal là mất, mở tab mới là
mất, chạy qua cron là mất. File `.env` thì nằm yên một chỗ.

Vì sao không dùng `python-dotenv`: cả dây chuyền chỉ cần đọc vài dòng
`TÊN=giá trị`, không cần nội suy biến, không cần multiline. Thêm một phụ thuộc
để làm việc mười dòng là không đáng — và mỗi phụ thuộc thêm vào là một cơ hội
nữa để `make setup` cài trượt sang Python khác.

Quy tắc: biến môi trường THẬT luôn thắng file `.env`. Nhờ vậy chạy một lệnh với
`PEXELS_API_KEY=... make shots-find` vẫn đè được, và CI cắm khoá qua secret của
hệ thống thì không bị file trong repo ghi đè.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
EXAMPLE_PATH = ROOT / ".env.example"

_loaded = False


def load(path: Path = ENV_PATH, force: bool = False) -> dict[str, str]:
    """Nạp .env vào os.environ. Gọi bao nhiêu lần cũng chỉ đọc đĩa một lần."""
    global _loaded
    if _loaded and not force:
        return {}
    _loaded = True

    if not path.exists():
        return {}

    found = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip("'\"")
        if not name:
            continue
        found[name] = value
        # Biến môi trường thật thắng file. Đặt rỗng cũng coi như chưa đặt, để
        # dòng `PEXELS_API_KEY=` chưa điền không che mất khoá export từ shell.
        if value and not os.environ.get(name):
            os.environ[name] = value
    return found


def missing_hint(var: str) -> str:
    """Câu hướng dẫn khi thiếu một khoá — nói rõ sửa Ở ĐÂU, không nói chung chung."""
    if ENV_PATH.exists():
        return f"Điền {var}=... vào {ENV_PATH.name} ở gốc repo rồi chạy lại."
    if EXAMPLE_PATH.exists():
        return (f"Chưa có file .env. Chạy `make setup` (nó chép .env.example "
                f"thành .env), rồi điền {var}=... vào đó.")
    return f"Đặt biến môi trường {var}."
