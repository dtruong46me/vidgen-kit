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
  truyền vào nó là tương đối so với `studio/`, nên có tiền tố `../`. Quy ước này
  chỉ được viết ở `pipeline/render.py`; Makefile không tự dựng đường dẫn nữa.
- **`calculateMetadata` suy thời lượng từ props.** Không được hardcode
  `durationInFrames` trong `studio/src/Composition.tsx`.
- **Font phải nạp qua `@remotion/google-fonts`.** Chrome lúc render không có font
  CJK; quên nạp là chữ Nhật ra ô vuông. Font Nhật thường thiếu dấu tiếng Việt —
  phải ghép hai họ font, một cho dòng Nhật, một cho dòng Việt.
- **Vùng an toàn:** TikTok/Reels che khoảng 350 px dưới cùng và dải bên phải.
  Caption đặt ở 2/3 dưới nhưng phải chừa đáy tối thiểu 380 px.
- **Lớp phủ tối phải đậm nhất ở dải có caption**, không phủ đều. Clip thật rất
  sáng; phủ đều là chữ chìm. Xem `Background.tsx`.
- **Hiệu ứng đi chậm.** Chữ hiện trong 26 frame, tắt trong 20, nền mờ chồng 24.
  Ba số này phải đổi cùng nhau, lệch nhau là mất cảm giác thong thả.
- **`remotion.config.ts` ghì concurrency về 1 vì máy dựng thiếu RAM.** Không phải
  giới hạn của code. Máy khoẻ hơn thì nâng lên; để nguyên trên máy 2 nhân / 3 GB
  trống thì compositor bị giết bằng SIGTERM lúc mở clip thứ hai.
- **Studio phải mở bằng dữ liệu thật.** `make studio` truyền `--props` trỏ vào
  build.json của ngày mới nhất. Props mặc định trong `Composition.tsx` chỉ là
  đường lui khi chưa dựng ngày nào.
- **Không commit file máy sinh:** `out/`, `content/*.build.json`,
  `content/.*.cache.json`, `studio/public/audio/20*/`. Không có ngoại lệ nào.
  Studio mở bằng props mặc định viết thẳng trong `Composition.tsx`, không đọc file.
- **Nhạc nền và clip nền thì CÓ commit.** Chúng là tài sản thật, tải một lần dùng
  mãi, và thiếu chúng là video mất hình mất tiếng. Chỉ giọng đọc mới là đồ máy
  sinh, vì `make content` dựng lại được trong vài giây.
- **Không để file mẫu, file test, file trung gian nằm lại trong repo.** Muốn thử
  gì thì thử trong thư mục scratch ngoài repo.

## Cây thư mục

```
pipeline/     Lớp A + B (Python)
  probe.py      đo độ dài thật bằng ffprobe — chỗ duy nhất gọi ffprobe
  script.py     đọc và kiểm content/<ngày>.json trước khi tốn công TTS
  tts.py        edge-tts từng câu + cache theo vân tay nội dung
  assets.py     xác minh clip nền và nhạc nền có thật, đo phần còn lại sau điểm cắt
  timeline.py   ★ nơi DUY NHẤT đổi giây ra frame (P-2)
  contract.py   ghi build.json — hình dạng hợp đồng khai báo ở đây (P-3)
  render.py     gọi Remotion — chỗ duy nhất biết quy ước cwd=studio/ và ../
  run.py        cửa vào: python3 -m pipeline.run <ngày> [--render|--still N]
studio/       Lớp C (Remotion)
  src/          Composition, DailyVideo, Background, Caption, fonts
  public/       audio/bgm-*.mp3, video/*.mp4  (commit)
                audio/<ngày>/line-XX.mp3      (máy sinh, không commit)
content/      <ngày>.json  (người viết, commit)
              <ngày>.build.json + .<ngày>.cache.json  (máy sinh, không commit)
library/      shots.json — metadata và giấy phép mọi clip. Còn rỗng, xem BƯỚC 4
out/          MP4 và PNG (không commit)
scripts/      check_assets.py  — soi nhạc nền và clip nền
docs/         tài liệu
```

## Trạng thái

**BƯỚC 0, 1 và 2 đã xong trọn vẹn.** `make content` gọi `python3 -m
pipeline.run`; `scripts/legacy_build.py` đã bị xoá. Nghiệm thu BƯỚC 2 đạt:
`2026-08-20` ra **đúng 1462 frame** (48,7 giây) và file `build.json` **giống hệt
từng byte** bản do legacy sinh ra.

> Con số 1462 vẫn là mốc hồi quy cho mọi bước sau. Đổi bất cứ thứ gì trong
> `pipeline/` xong, chạy `make content DAY=2026-08-20` và nhìn con số đó. Nó đổi
> mà bạn không cố ý đổi nhịp đọc, tức là bạn vừa làm hỏng timeline.

> Con số này từng là 1327 trước BƯỚC 1, đổi vì `leadIn`/`pauseAfter` giãn ra
> (0,2/0,35 -> 0,35/0,7 giây), cộng đúng 15 frame cho mỗi câu trong 9 câu.

Năm khiếm khuyết đo được ở BƯỚC 1 — đã đóng hết:

| | Khiếm khuyết | Đã sửa bằng |
|---|---|---|
| D-1 | Nhạc nền là file test tone 19,2 s | `bgm-lonely-self.mp3`, 150 s, không phải lặp |
| D-2 | Clip nền là video hoa mẫu 960×540 nằm ngang, chỉ có 2/9 cảnh | 3 clip trà đạo dọc 1080×1920, phủ đủ 9/9 cảnh |
| D-3 | Caption căn giữa màn hình thay vì 2/3 dưới | Neo đáy, chừa 400 px |
| D-4 | Nghỉ giữa câu chỉ 0,55 s, quá gấp | 1,05 s |
| D-5 | Romaji hiện ra `Kyo¯mo` thay vì `Kyō mo` | Tách hai họ font |

Ba lỗi phát hiện thêm trong lúc làm BƯỚC 1, cũng đã sửa:

- Câu 16 ký tự bị xuống dòng thành 15 + 1, bỏ trơ một chữ. Sửa bằng `text-wrap:
  balance` và tính lại thang cỡ chữ theo bề ngang 860 px.
- `clipDurationInFrames` ghi độ dài CẢ clip trong khi `Background.tsx` cắt clip
  bằng `trimBefore`, nên vòng lặp chạy quá phần thật sự có hình. Giờ đo phần còn
  lại sau điểm cắt.
- Lớp phủ tối nhạt nhất ở giữa khung, đúng chỗ caption bắt đầu. Giờ dồn xuống dưới.

Ba clip (12,8 + 12,9 + 22,9 giây) phải phủ chín cảnh dài tổng 48,6 giây, nên mỗi
clip dùng lại 2–3 lần ở các điểm cắt khác nhau (`clipStartInSeconds`). Cách xếp
hiện tại không cảnh nào phải loop — `make assets` kiểm tra lại được.
