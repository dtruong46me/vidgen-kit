# Vibe Coding Guidelines

Tài liệu này quy định các nguyên tắc, quy chuẩn viết code và phong cách (style) áp dụng cho dự án **Faceless Video Generator MVP**. Bất kỳ AI/LLM nào tham gia vào quá trình Vibe Coding cho dự án này đều PHẢI tuân thủ các quy tắc dưới đây.

## 1. Nguyên tắc cốt lõi (Core Principles)
- **Đơn giản & Rõ ràng (Simplicity)**: Viết code dễ đọc, ưu tiên sự rõ ràng hơn là tối ưu hóa sớm rườm rà. MVP cần chạy được và dễ debug.
- **Tách biệt Trách nhiệm (Separation of Concerns)**: Các module trong `src/services/` tuyệt đối không gọi chéo lẫn nhau một cách chằng chịt. Dữ liệu đi vào và ra (Input/Output) qua Pipeline (`faceless_pipeline.py`).
- **Phòng thủ & Logging (Defensive & Logging)**: Xử lý ngoại lệ (try/except) cho các thao tác rủi ro như đọc/ghi file, gọi API TTS. Sử dụng thư viện `logging` của Python thay vì `print()` trơn (trừ ở CLI entry point).

## 2. Quy chuẩn Ngôn ngữ và Môi trường
- **Python Version**: 3.10+. Bắt buộc sử dụng Type Hinting cho MỌI hàm và class (VD: `def process(text: str) -> float:`).
- **Dependencies**: Chỉ sử dụng các thư viện đã được phê duyệt trong thiết kế (moviepy, pydub, edge-tts, srt, Pillow). Không tự ý cài đặt thêm thư viện trừ khi thực sự cần thiết và phải comment giải thích.

## 3. Kiến trúc và Cấu trúc Code
- **Models Đầu Tiên**: Luôn sử dụng Data Models (Dataclass) định nghĩa trong `src/models.py` để truyền dữ liệu. Hạn chế tối đa việc truyền `dict` thô qua lại giữa các service để đảm bảo Type Safety.
- **Paths & Cấu hình**: KHÔNG hardcode đường dẫn (path) trong các service. Mọi đường dẫn (assets, output, temp) phải được lấy từ `src/config.py` bằng thư viện `pathlib` (sử dụng đối tượng `Path`).

## 4. Xử lý Video & Audio (MoviePy & pydub)
- **MoviePy Gotchas**:
  - Khi làm việc với MoviePy, luôn đóng các clip sau khi sử dụng để tránh leak memory (`clip.close()`). Đặc biệt quan trọng khi lặp qua nhiều clip.
  - Sử dụng `CompositeVideoClip` một cách cẩn thận, thiết lập `fps` rõ ràng khi write file cuối cùng.
- **Audio Syncing**: Timeline là "Chân lý" (Single Source of Truth). Bất cứ việc trim video clip nào cũng phải dựa trên biến số `duration` lấy từ audio thực tế (VoiceService sinh ra).

## 5. Hướng dẫn Prompt (Prompting cho Vibe Coding)
Khi yêu cầu AI viết một module mới (ví dụ: `composer_service.py`), hãy sử dụng format sau:

> "Dựa trên [docs/architecture.md], hãy viết mã cho `src/services/composer_service.py`. Input của service là danh sách các `TimelineItem` (từ models.py) và đường dẫn file audio tổng. Yêu cầu tuân thủ Type Hinting, sử dụng MoviePy để nối clip có crossfade 0.5s, và lấy config đường dẫn từ `src/config.py`."

## 6. Xử lý File & Thư mục Tạm
- Pipeline phải có bước dọn dẹp (cleanup) hoặc tái sử dụng file tạm trong thư mục `temp/`.
- Nếu file voice sinh ra bởi TTS bị lỗi, phải có cơ chế retry hoặc skip an toàn báo lỗi rõ ràng.

## 7. Format & Linting Code
- Thụt lề: 4 spaces.
- Tên biến, tên hàm: `snake_case`.
- Tên Class: `PascalCase`.
- Constant (trong config): `UPPER_SNAKE_CASE`.
- Cung cấp **Docstrings** ngắn gọn giải thích chức năng cho các phương thức quan trọng trong Service.
