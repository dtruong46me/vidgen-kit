"""
Lớp A — nhờ Claude viết nội dung một ngày. MẶC ĐỊNH TẮT (DEC-06).

`make new` chỉ đi đường này khi có `ANTHROPIC_API_KEY` trong `.env`, hoặc khi
bạn gọi thẳng `make new MODEL=opus|sonnet|haiku`. Không có khoá thì dây chuyền
lấy từ `library/bank.json` và không chạm tới mạng.

Module này tách hẳn khỏi phần còn lại: không module nào import nó ở đầu file,
`new.py` chỉ nạp nó lúc cần. Xoá file này đi thì mọi lệnh khác vẫn chạy.

Nó chỉ làm đúng một việc: đưa một bản mô tả (ngày nào, bao nhiêu chữ, câu nào
đã dùng gần đây) và nhận về chủ đề + tag + các câu. Nó KHÔNG ghi file, KHÔNG
biết cài đặt giọng đọc hay nhạc nền — những thứ đó `new.py` lo.

Đầu ra dùng structured outputs (`output_config.format`), nên JSON trả về luôn
đúng schema — không phải bóc JSON ra khỏi một đoạn văn. Còn nội dung có hay
không, đủ dài không, thì `new.py` vẫn kiểm lại như với ngân hàng.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import date

from . import env

#: Ba model, gọi bằng tên ngắn. Opus viết tiếng Nhật tự nhiên nhất; Sonnet rẻ
#: hơn chừng một nửa; Haiku rẻ nhất, hợp để thử đường ống chứ không hợp để đăng.
MODELS = {
    "opus": "claude-opus-5",
    "sonnet": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5",
}
DEFAULT_MODEL = "opus"

#: Kịch bản chỉ vài trăm token, 16000 là trần rộng rãi cho cả phần suy nghĩ
#: mà vẫn đủ nhỏ để gọi không cần streaming.
MAX_TOKENS = 16000

#: Chỉ Opus 5 nhận tham số này. Khi bộ lọc an toàn từ chối, máy chủ tự chạy lại
#: yêu cầu trên model dự phòng thay vì trả về lời từ chối.
_FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMError(RuntimeError):
    """Gọi Claude không thành. Thông báo nói rõ sửa ở đâu, không phải traceback."""


@dataclass(frozen=True)
class Brief:
    """Mọi thứ model cần biết để viết một ngày. Không có gì khác lọt vào prompt."""

    day: date
    #: Khoảng tổng số chữ Nhật, không tính dấu câu. `new.py` suy ra từ
    #: targetSeconds và tốc độ đọc đo được, để video rơi đúng khoảng 45–60 giây.
    chars: tuple[int, int]
    lines: tuple[int, int]
    #: Tag mà thư viện clip đang có. Model chỉ được chọn trong số này.
    tags: tuple[str, ...]
    #: Câu đã dùng ở các ngày gần nhất — vừa làm mẫu giọng văn, vừa để tránh lặp ý.
    recent: tuple[str, ...]
    max_line_chars: int = 40
    #: Các câu mở đầu cố định (ja, vi), ngày đã điền sẵn. Model chép nguyên văn.
    opening: tuple[tuple[str, str], ...] = ()


SYSTEM = """\
Bạn viết lời cho một kênh video dọc ngắn, đăng mỗi ngày một video 45–60 giây.

Video: một giọng nữ đọc tiếng Nhật chậm rãi trên nền cảnh quay tĩnh lặng (trà
đạo, mưa, cửa sổ, vườn, đường đi bộ). Mỗi câu hiện phụ đề ba dòng: tiếng Nhật,
romaji và tiếng Việt. Người xem là người Việt đang học tiếng Nhật.

Giọng văn:
- Nhẹ nhàng, tĩnh lặng, triết lý đời thường. Như một người bạn nói chuyện buổi
  sáng, không phải một diễn giả.
- Không giáo điều, không khẩu hiệu, không "hãy cố gắng lên". Gợi, đừng giảng.
- Một hình ảnh cụ thể (một tách trà, tiếng mưa, một bông hoa) rồi mới đến suy
  ngẫm. Suy ngẫm rút ra từ hình ảnh đó, không dán từ ngoài vào.
- Mở đầu CỐ ĐỊNH: một dòng nói ngày trước, rồi mới chào. Nó được ghi nguyên văn
  trong yêu cầu — chép đúng từng chữ, không tách đôi, không thêm lời chào khác.
- Sau mở đầu, nhịp thường gặp: quan sát nhỏ → suy ngẫm → lời chúc. Không bắt buộc.

Tiếng Nhật:
- Đơn giản, tự nhiên, khoảng trình độ N4–N3. Thể です/ます là chính.
- Mỗi câu một ý. Dấu 、 chia nhịp đọc — giọng đọc ngắt đúng chỗ đó.
- Ngày tháng viết bằng chữ số Ả Rập, ví dụ 9月10日.
- Không dùng ngoặc 「」, không emoji, không romaji.

Tiếng Việt:
- Dịch cho người Việt đọc thấy tự nhiên, giữ sắc thái mềm của câu Nhật.
  Không dịch từng chữ. Các tiểu từ ね、よ thường ra "nhỉ", "nhé".

Chủ đề (theme): 2–8 chữ tiếng Nhật, là tiêu đề viết bút lông ở màn mở đầu.
"""


def _schema(tags: tuple[str, ...]) -> dict:
    tag_items: dict = {"type": "string"}
    if tags:
        tag_items["enum"] = list(tags)
    return {
        "type": "object",
        "properties": {
            "theme": {"type": "string"},
            "tags": {"type": "array", "items": tag_items},
            "lines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ja": {"type": "string"},
                        "vi": {"type": "string"},
                    },
                    "required": ["ja", "vi"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["theme", "tags", "lines"],
        "additionalProperties": False,
    }


def _prompt(brief: Brief) -> str:
    d = brief.day
    weekday = "月火水木金土日"[d.weekday()]
    parts = [
        f"Viết nội dung cho ngày {d.month}月{d.day}日（{weekday}曜日）, năm {d.year}.",
        "",
        f"- Số câu: từ {brief.lines[0]} đến {brief.lines[1]}.",
        f"- Tổng số chữ tiếng Nhật, KHÔNG tính dấu câu: từ {brief.chars[0]} "
        f"đến {brief.chars[1]}. Đây là ràng buộc về thời lượng video, hãy đếm.",
        f"- Mỗi câu tiếng Nhật không quá {brief.max_line_chars} chữ, "
        f"nếu không phụ đề sẽ tràn màn hình.",
    ]
    if brief.tags:
        parts.append(
            "- tags: chọn 1–3 tag khớp nhất với hình ảnh của bài, từ danh sách: "
            + ", ".join(brief.tags) + "."
        )
    if brief.opening:
        parts += [
            "",
            "Mở đầu CỐ ĐỊNH dưới đây phải đứng đầu bài — chép nguyên văn cả ja lẫn "
            "vi, đúng thứ tự, rồi mới viết tiếp. Nó tính vào số câu và số chữ ở trên:",
            "",
            *(f"  {i}. ja: {ja}\n     vi: {vi}"
              for i, (ja, vi) in enumerate(brief.opening, start=1)),
        ]
    if brief.recent:
        parts += [
            "",
            "Các câu dưới đây đã dùng ở những ngày gần nhất. Giữ CÙNG giọng văn, "
            "nhưng đừng lặp lại ý, hình ảnh hay lời chúc cuối giống hệt "
            "(các câu mở đầu cố định thì cứ lặp):",
            "",
            *(f"  {line}" for line in brief.recent),
        ]
    return "\n".join(parts)


def _missing_library() -> LLMError:
    return LLMError(
        "Chưa cài thư viện anthropic cho Python đang chạy:\n"
        f"    {sys.executable}\n"
        "Chạy `make setup` rồi thử lại. Không muốn dùng LLM thì bỏ MODEL=, "
        "`make new` sẽ lấy từ ngân hàng kịch bản."
    )


def generate(model: str, brief: Brief, log=print) -> dict:
    """Gọi Claude, trả về {"theme", "tags", "lines": [{"ja", "vi"}]}.

    `model` là tên ngắn trong MODELS. Mọi lỗi mạng/khoá/giới hạn đều đổi thành
    LLMError có hướng dẫn, để `make new` in một dòng thay vì một traceback.
    """
    if model not in MODELS:
        raise LLMError(
            f"Không có model tên \"{model}\". Chọn một trong: "
            f"{', '.join(MODELS)} (hoặc MODEL=bank để lấy từ ngân hàng)."
        )
    model_id = MODELS[model]

    try:
        import anthropic
    except ImportError as exc:
        raise _missing_library() from exc

    env.load()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise LLMError(
            f"Thiếu ANTHROPIC_API_KEY. {env.missing_hint('ANTHROPIC_API_KEY')}"
        )

    request = {
        "model": model_id,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": _prompt(brief)}],
        "output_config": {
            "format": {"type": "json_schema", "schema": _schema(brief.tags)},
        },
    }
    if model_id == "claude-opus-5":
        # Truyền qua extra_* để không phụ thuộc bản SDK đã khai kiểu cho tham
        # số beta này hay chưa.
        request["extra_headers"] = {"anthropic-beta": _FALLBACK_BETA}
        request["extra_body"] = {"fallbacks": "default"}

    log(f"  Gọi {model_id}...")
    client = anthropic.Anthropic()
    try:
        response = client.messages.create(**request)
    except anthropic.AuthenticationError as exc:
        raise LLMError(
            "Khoá ANTHROPIC_API_KEY bị từ chối (sai hoặc đã thu hồi). "
            "Kiểm tra lại dòng đó trong .env."
        ) from exc
    except anthropic.PermissionDeniedError as exc:
        raise LLMError(f"Khoá không có quyền gọi {model_id}: {exc.message}") from exc
    except anthropic.NotFoundError as exc:
        raise LLMError(
            f"Tài khoản chưa dùng được model {model_id}. Thử MODEL=sonnet."
        ) from exc
    except anthropic.RateLimitError as exc:
        raise LLMError(
            "Đang bị giới hạn tốc độ hoặc hết hạn mức. Đợi một lát, hoặc dùng "
            "MODEL=bank để lấy từ ngân hàng."
        ) from exc
    except anthropic.BadRequestError as exc:
        raise LLMError(f"Yêu cầu bị từ chối: {exc.message}") from exc
    except anthropic.APIStatusError as exc:
        raise LLMError(
            f"Máy chủ Anthropic trả lỗi {exc.status_code}. Thử lại sau."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise LLMError("Không kết nối được tới api.anthropic.com. Kiểm tra mạng.") from exc

    if response.stop_reason == "refusal":
        raise LLMError("Model từ chối viết nội dung này. Chạy lại, hoặc dùng MODEL=bank.")
    if response.stop_reason == "max_tokens":
        raise LLMError(f"Model viết chưa xong đã chạm trần {MAX_TOKENS} token.")

    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"Model trả về thứ không phải JSON:\n{text[:400]}") from exc

    usage = response.usage
    served = f" (máy chủ chuyển sang {response.model})" if response.model != model_id else ""
    log(f"  {usage.input_tokens} token vào, {usage.output_tokens} token ra{served}")
    return data
