# vidgen-kit

Dây chuyền sản xuất video triết lý Nhật – Việt dạng dọc 1080×1920, chạy hằng ngày
bằng một lệnh. Đọc file này trước khi sửa bất cứ thứ gì.

## Kiến trúc: ba lớp, một điểm gặp

Ba lớp dưới đây **không được biết gì về nhau**. Chúng chỉ gặp nhau ở đúng một file.

| Lớp | Trả lời câu hỏi | Nằm ở | Đổi mỗi ngày? |
|---|---|---|---|
| A. Nội dung | Hôm nay nói gì? | `pipeline/` | Có |
| B. Tài sản | Lấy hình ảnh ở đâu? | `pipeline/` + `library/` | Không |
| C. Dựng hình | Trông như thế nào? | `studio/` | Không |

Điểm gặp duy nhất: **`content/<slug>.build.json`**.

```
content/<slug>.json          bạn (hoặc LLM) viết: câu tiếng Nhật + bản dịch
      │
      │  pipeline/  — TTS từng câu, ffprobe đo độ dài, chọn cảnh, tính frame
      ▼
content/<slug>.build.json    ★ HỢP ĐỒNG — ranh giới Python ↔ React
      │
      │  studio/  — Remotion đọc file này qua --props
      ▼
out/<slug>.mp4
```

## Bốn nguyên tắc bất di bất dịch

**P-1 — Audio là nguồn sự thật, timeline là hệ quả.**
Không bao giờ gõ tay timestamp. TTS sinh file, `ffprobe` đo độ dài thật, số frame
suy ra từ đó. Sai số bằng 0, và sửa một câu không làm lệch cả video.

**P-2 — Chỉ một module được phép tính frame.**
`pipeline/timeline.py` là nơi duy nhất trong toàn dự án chạm vào `from` và
`durationInFrames`. Không module nào khác được tính frame. Nhờ vậy bug "chữ lệch
tiếng" chỉ có thể nằm trong một file.

**P-3 — Thêm tính năng = thêm một trường vào hợp đồng.**
Không bao giờ sửa Python và React cùng lúc. Trường mới phải có giá trị mặc định,
để Remotion bản cũ vẫn render được build.json bản mới.

**P-4 — Mỗi bước ghi ra file đọc được bằng mắt.**
Debug bằng cách mở file JSON hoặc nghe file MP3, không phải bằng cách đọc log.

## Quy ước

- **Ngôn ngữ:** tài liệu và bình luận viết tiếng Việt; tên biến, tên hàm, tên file
  viết tiếng Anh. Thuật ngữ kỹ thuật giữ nguyên tiếng Anh (frame, props, render).
- **Mọi lệnh đi qua `Makefile`.** Đừng hướng dẫn người dùng gõ `npx remotion` trực
  tiếp — thêm target vào Makefile.
- **Remotion phải chạy với cwd là `studio/`** (nơi có `package.json`). Đường dẫn
  truyền vào nó là tương đối so với `studio/`, nên có tiền tố `../`.
- **`calculateMetadata` suy thời lượng từ props.** Không được hardcode
  `durationInFrames` trong `studio/src/Composition.tsx`.
- **Font phải nạp qua `@remotion/google-fonts`.** Chrome lúc render không có font
  CJK; quên nạp là chữ Nhật ra ô vuông. Font Nhật thường thiếu dấu tiếng Việt —
  phải ghép hai họ font, một cho dòng Nhật, một cho dòng Việt.
- **Vùng an toàn:** TikTok/Reels che khoảng 350 px dưới cùng và dải bên phải.
  Caption đặt ở 2/3 dưới nhưng phải chừa đáy tối thiểu 380 px.
- **Không commit file máy sinh:** `out/`, `content/*.build.json`,
  `content/.*.cache.json`, `studio/public/audio/20*/`. Ngoại lệ duy nhất là
  `content/_sample.build.json` và `studio/public/audio/_sample/` — bản mẫu cố định
  để Studio mở được trên clone mới.

## Cây thư mục

```
pipeline/     Lớp A + B (Python)      — hiện đang dựng, xem BƯỚC 2
studio/       Lớp C (Remotion)        — src/, public/, package.json
content/      kịch bản + build.json
library/      shots.json — metadata và giấy phép mọi clip
out/          MP4 (không commit)
scripts/      legacy_build.py — bản cũ, đường quay lui cho BƯỚC 2
docs/         tài liệu
```

## Trạng thái

Đang ở **BƯỚC 0** của kế hoạch tám bước. `pipeline/` còn rỗng; `make content` hiện
vẫn gọi `scripts/legacy_build.py`. BƯỚC 2 sẽ thay nó bằng các module trong
`pipeline/` — khi đó tiêu chí nghiệm thu là video mới phải có **đúng 1327 frame**
như bản cũ.

Bốn khiếm khuyết đã đo được và sẽ xử lý ở BƯỚC 1: nhạc nền đang là file test tone,
clip nền là video mẫu 960×540 nằm ngang, caption căn giữa màn hình thay vì 2/3
dưới, và khoảng nghỉ giữa câu chỉ 0,55 s là quá gấp.
