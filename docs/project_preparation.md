# Hướng dẫn Chuẩn bị Dự án: Faceless Video Generator MVP

Dựa trên tài liệu thiết kế hệ thống, đây là danh sách chi tiết những thứ bạn cần chuẩn bị (môi trường, dữ liệu, tài nguyên) trước khi chúng ta bắt đầu viết code. Việc chuẩn bị kỹ các tài nguyên này giúp quá trình test và phát triển diễn ra suôn sẻ nhất.

## 1. Môi trường Hệ thống

Bạn cần cài đặt sẵn các phần mềm sau trên máy tính của mình:

- **Python**: Phiên bản 3.9 trở lên (khuyến nghị 3.10 hoặc 3.11).
- **FFmpeg**: Đây là công cụ cốt lõi để xử lý video/audio (MoviePy và pydub đều cần FFmpeg làm backend).
  - *Lưu ý cho Windows*: Bạn cần tải FFmpeg, giải nén và thêm đường dẫn thư mục `bin` vào biến môi trường `PATH` của hệ thống.
  - Bạn có thể kiểm tra xem FFmpeg đã nhận chưa bằng cách mở Terminal và gõ: `ffmpeg -version`.
- **ImageMagick (Tùy chọn nhưng rất khuyến nghị)**: MoviePy sử dụng ImageMagick để render text (TextClip). Nếu không có, việc chèn Text/Subtitle có thể gặp lỗi. Cài đặt và đảm bảo tích vào ô "Install legacy utilities (e.g. convert)".

## 2. Tài nguyên Tĩnh (Assets)

Vì đây là dự án tạo video dựa trên các tài nguyên có sẵn (không dùng API Gen Video), bạn cần chuẩn bị sẵn một bộ dữ liệu mẫu (Dummy Data). Hãy tạo các thư mục sau và tải dữ liệu bỏ vào tương ứng:

### 2.1. Stock Videos (Video Clip Ngắn)
Tải khoảng 10-20 video clip ngắn (từ 2 đến 12 giây) miễn phí từ Pexels hoặc Pixabay.
- **Tiêu chí**: Video chất lượng HD/4K, khung hình dọc (9:16) nếu làm Tiktok/Shorts hoặc ngang (16:9) tùy ý định, nội dung aesthetic (trà đạo, hoa sen, nến, phong cảnh tĩnh lặng).
- **Cấu trúc lưu trữ**: Chia thành các thư mục theo chủ đề (`theme`).
  ```text
  assets/clips/
  ├── tea/            # Chứa các video rót trà, ly trà...
  ├── lotus/          # Chứa các video hoa sen...
  └── nature/         # Chứa video phong cảnh...
  ```

### 2.2. Nhạc nền (Background Music)
Tải 1-2 bài nhạc nền không bản quyền (Royalty-free) mang phong cách thư giãn, thiền, hoặc nhạc cụ dân tộc.
- **Định dạng**: `.mp3` hoặc `.wav`.
- **Lưu tại**: `assets/music/calm_bg_01.mp3`

### 2.3. Font chữ (Fonts)
Để render Title và Subtitle không bị lỗi font (đặc biệt với tiếng Việt hoặc tiếng Trung), bạn cần tải các font chữ hỗ trợ tốt Unicode.
- **Khuyến nghị**: Noto Sans SC / Noto Serif SC (cho tiếng Trung) hoặc các font tiếng Việt đẹp (Roboto, Arial Unicode...).
- **Lưu tại**: `assets/fonts/NotoSansSC-Regular.otf` (hoặc `.ttf`).

## 3. Cấu hình Dữ liệu (Metadata & Scripts)

Bạn cần tạo trước 2 file JSON theo đúng định dạng chúng ta đã chốt để code có thể đọc và xử lý.

### 3.1. File Metadata của Clip
Tạo file `assets/metadata/clips.json` để khai báo các video bạn đã tải ở bước 2.1.

**Mẫu `clips.json`**:
```json
{
  "clips": [
    {
      "id": "tea_01",
      "path": "assets/clips/tea/pour_01.mp4",
      "tags": ["tea", "pour"],
      "duration": 5.0,
      "theme": "tea_zen"
    },
    {
      "id": "lotus_01",
      "path": "assets/clips/lotus/lotus_closeup.mp4",
      "tags": ["lotus", "flower"],
      "duration": 6.5,
      "theme": "tea_zen"
    }
  ]
}
```
*(Lưu ý: `duration` bạn có thể xem thời lượng của file MP4 rồi điền vào, không cần chính xác tới từng mili-giây).*

### 3.2. File Kịch bản Mẫu (Input Script)
Tạo file `input/scripts/example.json`. File này chính là đầu vào mà bạn sẽ đưa cho phần mềm chạy.

**Mẫu `example.json`**:
```json
{
  "title": "放下",
  "subtitle": "清茶一杯 · 品味人生",
  "ending_text": "人生如茶，拿得起也要放得下。",
  "theme": "tea_zen",
  "voice": "zh-CN-YunxiNeural",
  "target_duration": 35,
  "segments": [
    "当你看清了一个人而不揭穿，你就懂得了格局的意义。",
    "当你讨厌一个人而不翻脸，你就明白了释然的重要性。",
    "茶不过两个姿态，沉浮；饮茶人不过两个动作，拿起，放下。"
  ]
}
```

## Tổng kết Checklist trước khi Code

- [ ] Đã cài đặt **Python 3.10+**.
- [ ] Đã cài đặt **FFmpeg** (và thêm vào PATH).
- [ ] Đã cài đặt **ImageMagick** (tùy chọn nhưng cần thiết cho text đẹp).
- [ ] Đã tải và sắp xếp **Video clips** vào `assets/clips/`.
- [ ] Đã tải 1-2 file nhạc vào `assets/music/`.
- [ ] Đã tải font chữ vào `assets/fonts/`.
- [ ] Đã tạo file **`assets/metadata/clips.json`**.
- [ ] Đã tạo file kịch bản **`input/scripts/example.json`**.

Ngay khi bạn xác nhận đã chuẩn bị xong (hoặc phần lớn) các tài nguyên này, hãy báo cho tôi biết. Tôi sẽ bắt đầu tạo cấu trúc thư mục dự án và viết mã nguồn (source code) cho các module cốt lõi!
