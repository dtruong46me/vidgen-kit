# Kiến trúc Hệ thống: Faceless Video Generator MVP

Tài liệu này mô tả chi tiết kiến trúc của ứng dụng Faceless Video Generator (MVP), làm tài liệu tham chiếu (context) cho quá trình Vibe Coding.

## 1. Tổng quan Kiến trúc (Architecture Overview)

Dự án áp dụng mô hình kiến trúc theo hướng **Module hóa (Modular)** và **Dịch vụ (Service-oriented)**. Mỗi dịch vụ chịu trách nhiệm cho một công đoạn cụ thể trong quá trình xử lý video, giúp dễ dàng test độc lập và bảo trì.

Kiến trúc tuân theo luồng **Audio-First**: Thời lượng và nhịp độ của video cuối cùng được quyết định hoàn toàn bởi thời lượng của các đoạn âm thanh giọng đọc (voiceover).

### 1.1. Core Pipeline (Luồng xử lý chính)
1. **Input**: Đọc `example.json` (chứa tiêu đề, theme, và danh sách các câu script).
2. **Voice Generation (VoiceService)**: Tạo file âm thanh TTS cho từng câu script, đo đạc thời lượng (duration) chính xác của từng đoạn.
3. **Asset Selection (AssetService)**: Dựa vào `theme` của script, chọn ngẫu nhiên hoặc theo rule các video clip từ thư mục `assets/clips/` và lấy metadata từ `clips.json`.
4. **Timeline Building (TimelineService)**: Khớp nối từng đoạn voice với một video clip. Tính toán `start_time` và `end_time` dựa trên duration của voice. Cắt (trim) hoặc lặp (loop) clip cho vừa vặn với thời lượng giọng đọc. Chèn transition (crossfade).
5. **Subtitle Generation (SubtitleService)**: Tạo file `.srt` (phụ đề) dựa trên text của script và timing từ Timeline.
6. **Video Composition (ComposerService)**: Sử dụng **MoviePy** để render video cuối cùng (ghép clip, thêm audio, overlay subtitle, bg music, fade in/out).
7. **Thumbnail Generation (ThumbnailService)**: Lấy frame đầu tiên của video, dùng **Pillow** chèn text làm thumbnail.

## 2. Cấu trúc Thư mục (Directory Structure)

```text
faceless_video_mvp/
├── assets/                 # Dữ liệu tĩnh
│   ├── clips/              # Video gốc (phân theo theme)
│   ├── metadata/           # clips.json
│   ├── music/              # Nhạc nền
│   └── fonts/              # Font chữ (hỗ trợ CJK/VN)
├── input/                  # Đầu vào từ người dùng
│   └── scripts/            # Các file .json kịch bản
├── output/                 # Thư mục xuất file
│   ├── videos/             # Video MP4 hoàn chỉnh
│   └── thumbnails/         # Ảnh bìa
├── temp/                   # Dữ liệu tạm (cache)
│   ├── voices/             # File audio sinh từ TTS
│   └── subtitles/          # File .srt
├── src/                    # Source Code
│   ├── __init__.py
│   ├── config.py           # Cấu hình chung (đường dẫn, thông số mặc định)
│   ├── models.py           # Định nghĩa cấu trúc dữ liệu (Dataclasses / Pydantic)
│   ├── utils/              # Các hàm tiện ích (file I/O, format time)
│   ├── services/           # Các service cốt lõi
│   │   ├── voice_service.py
│   │   ├── asset_service.py
│   │   ├── timeline_service.py
│   │   ├── subtitle_service.py
│   │   ├── composer_service.py
│   │   └── thumbnail_service.py
│   └── pipeline/
│       └── faceless_pipeline.py # Orchestrator điều phối các service
└── main.py                 # Entry point (CLI)
```

## 3. Định dạng Dữ liệu (Data Models)

Để Vibe Coding hiệu quả, mọi dữ liệu luân chuyển giữa các service phải tuân theo các model được định nghĩa rõ ràng trong `src/models.py`.

### 3.1. ScriptInput
Dữ liệu đầu vào từ file `example.json`.
- `title` (str)
- `subtitle` (str)
- `ending_text` (str)
- `theme` (str)
- `segments` (list[str]): Danh sách các câu thoại.

### 3.2. TimedSegment
Kết quả sau khi chạy qua `VoiceService`.
- `segment_id` (int)
- `text` (str)
- `audio_path` (str)
- `duration` (float): Thời lượng tính bằng giây.
- `start_time` (float): Thời gian bắt đầu trong video tổng.
- `end_time` (float): Thời gian kết thúc trong video tổng.

### 3.3. TimelineItem
Kết quả sau khi chạy qua `TimelineService`. Bao gồm `TimedSegment` cộng thêm thông tin video clip tương ứng.
- `segment_info` (TimedSegment)
- `clip_path` (str): Đường dẫn đến video clip stock.
- `clip_trim_start` (float): Điểm bắt đầu cắt video clip gốc.
- `clip_trim_end` (float): Điểm kết thúc cắt.
- `transition` (str): Loại hiệu ứng chuyển cảnh (mặc định: 'crossfade').

## 4. Công nghệ & Thư viện (Tech Stack)
- **Ngôn ngữ**: Python 3.10+
- **Video/Audio Processing**: `moviepy` (Core composer), `ffmpeg-python` (Backend), `pydub` (Xử lý âm thanh độc lập).
- **TTS**: `edge-tts` (Sinh giọng đọc mượt mà, hỗ trợ tốt CJK/Việt Nam).
- **Subtitles**: `srt` (Parse và ghi file SRT).
- **Image/Thumbnail**: `Pillow` (PIL).
- **Data Validation**: `dataclasses` (Python built-in) hoặc `pydantic`.
