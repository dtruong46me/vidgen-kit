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

Điểm gặp duy nhất: **`content/<slug>/build.json`**.

```
content/<slug>/script.json   bạn (hoặc LLM) viết: câu tiếng Nhật + bản dịch
      │
      │  pipeline/  — TTS từng câu, ffprobe đo độ dài, chọn cảnh, tính frame
      ▼
content/<slug>/build.json    ★ HỢP ĐỒNG — ranh giới Python ↔ React
      │
      │  studio/  — Remotion đọc file này qua --props
      ▼
out/<slug>/   gói đăng: <slug>.mp4, ảnh bìa, caption, lời, audio, metadata
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
- **Cài thư viện Python bằng `make setup`, đừng bao giờ gõ `pip install` trần.**
  Máy dựng có hơn một Python (conda base và python của codespace). `pip` trần trỏ
  vào cái nào là tuỳ `PATH`, nên rất dễ cài xong một chỗ rồi `make` chạy ở chỗ kia
  và báo thiếu thư viện. `make setup` dùng `python3 -m pip`, tức luôn đúng trình
  thông dịch mà Makefile sẽ gọi. Vì lý do đó, mọi thông báo "thiếu thư viện"
  trong `pipeline/` đều phải in kèm `sys.executable`.
- **`make setup` cũng cài Node cho `studio/` bằng `npm ci`.** `studio/node_modules`
  không vào git, thiếu nó thì `npx remotion` chỉ báo "could not determine
  executable". Nó chứa binary theo hệ điều hành, nên cài ở đúng môi trường chạy
  `make` (WSL thì cài trong WSL, đừng `npm install` từ Windows).
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
- **Chữ đọc được nhờ quầng tối ĐI THEO CHỮ, không nhờ phủ tối cả khung.** Bản
  cũ phủ 34–88% toàn khung, đậm nhất ở dải caption: chữ rõ nhưng video xỉn như
  trời sắp tối, kể cả lúc không có chữ nào. Giờ lớp phủ của `Background.tsx`
  rất nhẹ (4–42%, chỉ đậm ở đỉnh cho thanh trạng thái và ở đáy cho chữ của
  TikTok). Caption tự mang quầng tối `CAPTION_SCRIM`, hiện và tắt cùng chữ;
  tiêu đề cũng vậy; và chữ có viền tối 3px sát nét. Clip thật rất sáng (tuyết,
  giấy, hoa anh đào) — muốn chữ rõ hơn thì đậm quầng hoặc viền, ĐỪNG đậm lại
  lớp phủ toàn khung.
- **Hiệu ứng đi chậm.** Chữ hiện trong 26 frame, tắt trong 20, nền mờ chồng 24.
  Ba số này phải đổi cùng nhau, lệch nhau là mất cảm giác thong thả. Tiêu đề ngày
  cố tình chậm hơn nữa (34 frame): nó không phải nhường chỗ cho câu nào.
- **Không có màn mở đầu riêng.** Video vào thẳng cảnh 1 ở frame 0; tiêu đề ngày
  (`titleCard`, vd. `8月20日`, chủ đề nhỏ bên dưới) đè lên cảnh 1 ở 1/4 trên.
  Cảnh 1 lặng `intro.pauseSeconds` (mặc định 1,5 giây) rồi mới đọc, và caption
  câu 1 chờ đúng bấy nhiêu (`captionStartInFrames`). `build.json` vẫn ghi
  `intro: null` để Remotion bản cũ đếm đúng tổng — đừng xoá trường đó.
- **Ảnh bìa chụp lúc caption câu 1 VÀO XONG** (`thumbnailFrame`, do `timeline.py`
  chọn — mặc định 45 + 26 + 6 = 77): trên hình có đủ ngày tháng, chủ đề và câu
  chào `おはようございます`. Bản trước chụp ở frame 45, đúng lúc caption mới bắt
  đầu vào, nên ảnh bìa chỉ có mỗi tiêu đề ngày — mà ảnh bìa là thứ duy nhất
  người lướt thấy trước khi quyết định xem. `CAPTION_IN_FRAMES` (26) trong
  `timeline.py` phải khớp `IN_FRAMES` của `Caption.tsx`; nó chỉ dùng để chọn
  frame ảnh bìa, không tham gia phép cộng nào. Chủ đề vẫn phải vào xong ở frame
  44 (`SUBTITLE_DELAY` 10 + `TITLE_IN` 34 trong `TitleCard.tsx`) để không hiện
  cùng nhịp với caption. `make video` dựng ảnh bìa ngay sau MP4, `make export`
  dựng nốt cho ngày nào còn thiếu; `make release` là video → check → gói, cho
  một ngày hoặc cả khoảng ngày — đó là lệnh trọn gói.
- **Caption bài đăng là chữ ĐỂ ĐĂNG, không phải chữ để vẽ.** Trường `caption`
  trong kịch bản không hiện trong video; nó đi ra `out/<ngày>/caption.txt`. Ngày
  tháng KHÔNG gõ vào đó — `pipeline/post.py` ghép từ tên kịch bản (`2026-09-11`
  ra `11.09.26`), đúng tinh thần P-1. Emoji cũng KHÔNG gõ: `EMOJI = "🌿"` ở
  `post.py`, một cái cho MỌI ngày — nó là dấu nhận diện kênh, không phải minh
  hoạ chủ đề. Bản trước để mỗi kịch bản tự chọn emoji (🍵, 🌅, 🪵…) nên lướt
  trang kênh thì mỗi bài một kiểu. Kịch bản còn để emoji ở đầu `caption` thì
  máy bỏ đi và `make content` kêu một dòng, không in hai emoji liền nhau. Bỏ
  trống `caption` thì máy mượn câu tiếng Việt cuối cùng và kêu một dòng — chạy
  được nhưng nhạt.
- **`caption` là NỘI DUNG, `hashtags` là CÀI ĐẶT.** `caption` nằm trong
  `CONTENT_KEYS` của `new.py` nên không kế thừa (mỗi ngày một câu khác);
  `hashtags` nằm trong `DEFAULT_SETTINGS` nên kế thừa như giọng đọc và nhạc nền
  (kênh nào cũng một bộ thẻ).
- **`make export` chỉ ĐỌC, trừ đúng một thứ: ẢNH BÌA.** Nó gói
  `content/<ngày>/build.json` và MP4 đã có ra `out/<ngày>/`, không gọi TTS,
  không chọn clip, không tính frame —
  phép cộng frame duy nhất nó dùng là mượn `check.py` (P-2). Nhờ vậy sửa
  `export.py` không bao giờ làm lệch một frame nào. Gói lại thì nó xoá rồi viết
  lại ĐÚNG phần nó sinh ra (`GENERATED`: năm file chữ và `audio/`): bớt một câu
  mà còn `line-09.mp3` nằm lại là người đăng tưởng video có chín câu — nhưng
  video và ảnh bìa nằm cùng thư mục thì không đụng tới, xoá theo là mất nửa
  tiếng render. Và nó KHÔNG ghi dấu thời gian vào `metadata.json` — gói hai lần
  phải ra hai thư mục giống hệt nhau, y như bộ chọn clip phải tất định. Ngoại lệ
  ảnh bìa: thiếu `out/<ngày>/<ngày>-thumbnail.png` hoặc file đó cũ hơn
  `build.json` thì nó gọi Remotion chụp lại, vì gói không có ảnh bìa là gói chưa
  đăng được mà ảnh bìa chỉ tốn MỘT frame. Ngoại lệ này không phá câu trên: frame
  chụp là `thumbnailFrame` đã ghi sẵn trong hợp đồng, `export.py` không tự tính.
  Dựng không được thì kêu một dòng rồi gói tiếp, không chặn.
- **Một ngày là một thư mục `out/<ngày>/`, đủ thứ để ĐĂNG.** `render.py` dựng
  MP4 và ảnh bìa thẳng vào đó; `export.py` viết caption, lời, metadata và chép
  giọng đọc vào cạnh. Không chép video qua lại: bản trước dựng ra
  `out/<ngày>.mp4` rồi chép vào gói, mỗi video nằm hai chỗ. Gặp file lẻ kiểu cũ
  thì `make export` DỜI vào. Đồ để SOÁT thì nằm ngoài thư mục ngày:
  `out/<ngày>-check/` và `out/<ngày>-f<N>.png`. Mọi đường dẫn này khai ở
  `paths.py`, cùng chỗ với `content/`.
- **Nhiều ngày một lệnh: `FROM=… [TO=…]` hoặc `MONTH=…`**, cho `make export` và
  `make release`. Makefile chỉ ghép thành một chuỗi (`2026-09-12..2026-09-30`);
  đọc chuỗi đó là việc của `paths.select`, so theo tiền tố của tên ngày ISO nên
  không phải tính tháng có bao nhiêu ngày. `make release` nhiều ngày thì một ngày
  hỏng KHÔNG chặn các ngày sau, cuối lệnh in ra ngày nào hỏng.
- **Sóng giọng đọc (`VoiceWave.tsx`) đọc từ file giọng của từng câu, không phải
  nhạc nền.** Nằm ngay trên tiêu đề, chạy suốt các cảnh, lặng thì phẳng thành
  hàng chấm. Chỉ là lớp vẽ: không có trường nào trong hợp đồng, vì `audio` và
  `audioStartInFrames` đã đủ. `@remotion/media-utils` phải cùng bản với `remotion`.
- **`calculateMetadata` và `timeline.py` phải ra CÙNG một con số.** Cả hai đều
  cộng các cảnh + màn kết (tiêu đề nằm trong cảnh 1, không cộng thêm frame).
  Lệch nhau là video cụt đuôi hoặc thừa một đoạn đen — mà không bên nào báo
  lỗi, phải xem mới biết.
- **Ba kiểu chuyển cảnh khác nhau ở CHỖ ĐẶT cảnh, không chỉ ở hiệu ứng.**
  `crossfade` cho cảnh bắt đầu sớm hơn T frame để chồng lên cảnh trước;
  `dip_to_black` và `cut` để cảnh nằm đúng ô của nó. Vì vậy `DailyVideo.tsx`
  (đặt cảnh) và `Background.tsx` (vẽ opacity) phải đọc cùng nhau.
- **Câu dài thì CẮT, đừng bóp chữ nhỏ lại.** `pipeline/phrase.py` là chỗ duy
  nhất biết cắt một câu thành mấy MẢNH caption. Mảnh KHÔNG phải cảnh: cùng một
  clip, cùng một file mp3 đọc liền hơi, frame chạy tiếp — chỉ chữ là đổi giữa
  chừng, nên cắt mảnh không cộng thêm frame nào. Mảnh sau vào ở đâu thì hỏi
  `WordBoundary` của edge-tts (`tts.py` ghi lại giọng đọc chạm từng chữ ở giây
  thứ mấy), rồi lùi đúng `leadIn` — vẫn P-1, không gõ tay timestamp nào. Bỏ
  trống thì máy cắt, viết `"ja"`/`"vi"` thành DANH SÁCH thì người viết thắng,
  cùng quy ước với `clip`. Hai danh sách phải bằng số phần tử.
- **Cỡ chữ caption CỐ ĐỊNH 56/38, không co theo độ dài câu.** Thang năm bậc cũ
  (62/55/48/42/36) không bao giờ làm tràn khung, nhưng nó làm chuyện tệ hơn: cỡ
  chữ nhảy lên nhảy xuống giữa các cảnh trong khi độ dài câu chẳng nói lên điều
  gì với người xem. Câu dài giờ cao thêm một dòng chứ không nhỏ đi — khối chữ
  neo đáy nên nó nở lên trên. Bốn ngưỡng ở `phrase.py` là HAI cặp khác nhau:
  `JA_MAX`/`VI_MAX` (24 chữ / 60 ký tự) quyết CÓ CẮT KHÔNG, `JA_FIT`/`VI_FIT`
  (30 / 88) quyết CÓ KÊU KHÔNG và phải khớp thang cỡ chữ trong `Caption.tsx`.
  Cặp đầu chặt hơn là cố ý: nhờ khoảng đệm đó, câu không cắt được vẫn hiện ở
  đúng cỡ chữ chuẩn. Cảnh nào chữ nhỏ hơn các cảnh khác là TRIỆU CHỨNG.
- **Dòng hiragana mặc định TẮT.** Caption đã có ba dòng; dòng thứ tư ép cỡ chữ
  nhỏ lại và lấn vào vùng an toàn 380px. Bật bằng `"showHira": true` trong kịch
  bản. Câu nào vốn toàn kana thì dòng đó tự ẩn — in ra là lặp y hệt dòng trên.
- **`remotion.config.ts` ghì concurrency về 1 vì máy dựng thiếu RAM.** Không phải
  giới hạn của code. Máy khoẻ hơn thì nâng lên; để nguyên trên máy 2 nhân / 3 GB
  trống thì compositor bị giết bằng SIGTERM lúc mở clip thứ hai.
- **Studio phải mở bằng dữ liệu thật.** `make studio` truyền `--props` trỏ vào
  build.json của ngày mới nhất. Props mặc định trong `Composition.tsx` chỉ là
  đường lui khi chưa dựng ngày nào.
- **Một ngày là một thư mục `content/<ngày>/`, ba file ba vai trò.**
  `script.json` người viết (commit), `build.json` hợp đồng (máy sinh),
  `.cache.json` cache TTS (máy sinh, xoá được — nó giữ vân tay SHA1 của
  `câu|giọng|tốc độ|cao độ` để biết câu nào không phải đọc lại, kèm mốc từng
  chữ do edge-tts trả về trong chính lượt đọc đó). Bố cục này
  khai ở **`pipeline/paths.py`, chỗ duy nhất biết `content/` bày ra sao** —
  đừng module nào tự ghép chuỗi đường dẫn, cùng lý do với `probe.py` và
  `timeline.py`.
- **Không commit file máy sinh:** `out/`, `content/*/build.json`,
  `content/*/.cache.json`, `studio/public/audio/20*/`. Không có ngoại lệ nào.
  Studio mở bằng props mặc định viết thẳng trong `Composition.tsx`, không đọc file.
- **Nhạc nền CÓ commit, clip nền thì KHÔNG.** Nhạc nhẹ và không tải lại được
  bằng lệnh, nên nó vào git. Clip nền thì ngược lại: thư viện 52 clip dọc
  1080×1920 nặng 1,6 GB, mà `library/shots.json` ghi đủ nguồn và id nên
  `make shots-get` dựng lại được từng cái — sổ vào git, file thì không. Vì vậy
  máy mới clone về sẽ thấy `make shots` kêu "thiếu file" cho tới khi tải lại.
  Ba clip đầu (`tea-room`, `matcha-whisk`, `tea-tray`) đã nằm trong lịch sử từ
  trước nên vẫn được git theo dõi. Giọng đọc cũng không commit, vì
  `make content` dựng lại được trong vài giây.
- **Romaji do máy sinh, đừng gõ tay.** Kịch bản không có trường `romaji` nữa.
  Máy đọc sai chữ nào thì thêm cách đọc vào `library/readings.json` — bảng đó áp
  cho mọi ngày, sửa một lần là xong mãi. Đọc đối chiếu bằng `make reading`.
- **Cutlet trần không đủ, đừng gỡ ba lớp vá trong `reading.py`.** Nó không có
  macron (今日 ra `Kyou`, tức mở lại D-5), không đọc số (`8月20日` ra
  `8 gatsu 20ka`), và đọc sai chữ nhiều nghĩa. Lớp macron bám vào `pron` và
  `kana` của MeCab chứ không đoán theo mặt chữ — nhờ vậy `思う` không thành `omō`.
- **Thư viện hiện có 52 clip, 7 tag chính:** `tea`, `walk`, `rain`, `flower`,
  `window`, `hands`, `garden`, cộng các tag phụ (`calm`, `interior`, `morning`,
  `people`, `ritual`, `nature`, `closeup`…) mà `library/bank.json` đang gọi tên.
  Bảy clip mỗi tag chính là đủ để một ngày tám cảnh không dùng lại clip nào và
  không cảnh nào phải loop — kiểm bằng `pipeline.shots.choose`.
- **Mỗi file trong `studio/public/` phải có một dòng trong `library/shots.json`.**
  Câu hỏi "clip này ở đâu ra" chỉ rẻ đúng một lúc: lúc vừa tải về. Ba clip đầu
  tiên suýt mất dấu, may là lịch sử git còn tên file gốc nên truy ngược được.
  Vì vậy `make shots-get` và `make shots-add` tải và ghi sổ trong CÙNG một lệnh —
  đừng tách ra, tách ra là sẽ có ngày tải xong quên ghi.
- **Cái gì ffprobe đo được thì đừng chép vào sổ.** Độ dài, bề ngang, fps đều đo
  được, mà số chép tay thì chỉ chờ ngày lệch với file thật. Sổ chỉ giữ thứ không
  đo được: nguồn, tác giả, giấy phép, tag.
- **Trường `clip` trong kịch bản có thể bỏ trống.** Bỏ trống thì `shots.py` chọn
  hộ, và nó chọn tốt hơn tay người: bản xếp tay của `2026-08-20` có cảnh chỉ dư
  5 frame trước khi phải loop, bản máy chọn dư ít nhất 48 frame. Câu nào đã ghi
  `clip` thì máy không đụng vào — người viết luôn thắng máy.
- **Đừng ghi `calm` cạnh một tag chủ đề trong kịch bản.** `shots.matches()` ghép
  tag theo kiểu HOẶC, mà `calm` nằm trên 30/52 clip — nên `["rain","window","calm"]`
  khớp gần hết thư viện và bộ chọn rơi về thứ tự trong sổ, tức toàn clip trà.
  Chỉ giữ `calm` khi kịch bản thật sự không có chủ đề hình ảnh nào.
- **Bộ chọn clip phải tất định.** Không random. Cùng kịch bản, cùng thư viện thì
  phải ra cùng kết quả, nếu không thì `make content` chạy hai lần ra hai file
  khác nhau và mốc hồi quy mất nghĩa. Phá hoà bằng thứ tự dòng trong sổ.
- **Chọn clip phải chạy SAU tts.** Muốn biết clip có đủ dài không thì phải biết
  cảnh dài bao nhiêu, mà cảnh dài bao nhiêu là do giọng đọc quyết định (P-1).
- **Mọi lần gọi mạng trong `fetch.py` phải mang `User-Agent` trình duyệt.**
  Cloudflare của Pexels chặn thẳng UA mặc định của urllib (`Python-urllib/3.x`)
  bằng error 1010, trả HTTP 403 — mà `fetch.py` dịch 403 thành "khoá API sai
  hoặc hết hạn", nên đọc log thì tưởng hỏng khoá và đi xin khoá mới. Đó đúng là
  cái đã làm T-1 treo. Hằng `USER_AGENT` khai một chỗ, dùng cho cả tìm lẫn tải.
- **Tải bản dọc vừa đủ 1080px, đừng lấy bản rộng nhất.** Video đích chỉ
  1080×1920, một bản 4K lên khung hình y hệt mà nặng gấp năm. `_best_file` lấy
  bản dọc HẸP NHẤT mà vẫn đủ 1080. Siêu dữ liệu của Pexels có lúc nói dối —
  `6186641` quảng cáo `hd_1080_2048` nhưng phục vụ file 720×1366 — nên đừng tin
  con số API trả về, `make shots` đo lại bằng ffprobe mới là số thật.
- **Khoá API đọc từ `.env` ở gốc repo, không bao giờ vào git.** `pipeline/env.py`
  nạp file đó; biến môi trường thật thắng file. `.env` nằm trong `.gitignore`,
  `.env.example` mới là file được commit, và `make setup` chép cái sau thành cái
  trước nếu chưa có (đã có thì KHÔNG đè). Không có khoá thì mọi lệnh dựng video
  vẫn chạy đủ — khoá chỉ để tìm và tải clip tự động.
- **`make new` không bao giờ đè kịch bản đã có.** File trong `content/` là file
  người viết. Muốn tạo lại thì xoá tay.
- **Kịch bản mới kế thừa CÀI ĐẶT từ ngày gần nhất; chỉ NỘI DUNG lấy từ ngân hàng
  hoặc Claude.** Đừng đưa giọng đọc, nhạc nền hay nhịp nghỉ vào
  `library/bank.json` hay vào prompt — chỉnh ở ngày gần nhất một lần là mọi ngày
  sau theo.
- **LLM mặc định tắt (DEC-06).** `make new` chỉ gọi Claude khi `.env` có
  `ANTHROPIC_API_KEY` hoặc khi gõ `MODEL=`. Không module nào được import
  `pipeline/llm.py` ở đầu file — `new.py` nạp nó muộn, để xoá `llm.py` hay thiếu
  thư viện `anthropic` thì đường ngân hàng vẫn chạy.
- **Mọi kịch bản mở đầu bằng MỘT dòng: `今日は、<ngày>です。おはようございます。`.**
  Nói ngày trước, chào sau, chung một dòng — một file tiếng, một cảnh, không có
  khoảng nghỉ giữa hai vế. Dòng đó nằm ở `OPENING` trong `pipeline/new.py` — chỗ
  duy nhất khai nó. Ngân hàng ghi sẵn ở đầu mỗi mục, prompt Claude chép nguyên
  văn; `make bank` và `make new` cảnh báo chỗ nào lệch.
- **Ngân hàng chọn tất định:** mục chưa dùng đầu tiên theo thứ tự trong file, hết
  thì mục dùng lâu nhất (đọc trường `source` của các kịch bản đã có). Thêm mục
  mới vào CUỐI file.
- **Đoạn kana tự sinh (số, bảng đè) romaji hoá NGOÀI MeCab, phần chữ thường đưa
  MeCab từng khúc riêng.** MeCab không biết ranh giới đoạn: 「くがつとおか」 bị
  cắt thành くが / つと / おか, mẩu vắt qua ranh giới bị sót thành
  `kugatsu tsuto tōka`. `8月20日` chỉ tình cờ cắt khớp — nên đổi gì trong
  `reading.py` thì quét đủ 12 tháng × 31 ngày, đừng chỉ thử một ngày.
- **`make check` trích một ảnh cho mỗi MÀN CHỮ, không phải mỗi cảnh.** Câu dài
  chia mảnh thì lấy giữa cảnh là mảnh đầu không ai nhìn thấy — mà trang này sinh
  ra chính để soi chữ. Nhãn ghi `Cảnh 4 · mảnh 1`.
- **`make check` đếm frame trên chính MP4, không tin `duration × fps`.** Độ dài
  container tính cả luồng tiếng. Đếm gói (`-count_packets`) ra cùng số với giải
  mã từng frame mà gần như không tốn CPU.
- **Không để file mẫu, file test, file trung gian nằm lại trong repo.** Muốn thử
  gì thì thử trong thư mục scratch ngoài repo.

## Cây thư mục

```
pipeline/     Lớp A + B (Python)
  env.py        nạp .env — chỗ duy nhất đọc khoá API
  intro.py      chữ cho tiêu đề ngày và màn kết; ngày suy từ tên kịch bản
  post.py       chữ cho BÀI ĐĂNG: dòng caption + hashtag (không vẽ lên video)
  probe.py      đo độ dài thật bằng ffprobe — chỗ duy nhất gọi ffprobe
  paths.py      chỗ DUY NHẤT biết content/ và out/ bày ra sao; đọc khoảng ngày FROM/TO/MONTH
  phrase.py     chỗ DUY NHẤT biết cắt câu dài thành mấy mảnh caption
  script.py     đọc và kiểm content/<ngày>/script.json trước khi tốn công TTS
  tts.py        edge-tts từng câu + cache theo vân tay nội dung
  reading.py    sinh romaji + hiragana từ câu Nhật (cutlet, có đường lui)
  library.py    sổ đăng ký tài sản — đọc/ghi library/shots.json, soi bằng `make shots`
  fetch.py      tải clip từ Pexels/Pixabay rồi ghi sổ ngay trong một lệnh
  shots.py      chọn clip cho cảnh nào kịch bản bỏ trống trường `clip`
  assets.py     xác minh clip nền và nhạc nền có thật, đo phần còn lại sau điểm cắt
  timeline.py   ★ nơi DUY NHẤT đổi giây ra frame (P-2)
  contract.py   ghi build.json — hình dạng hợp đồng khai báo ở đây (P-3)
  render.py     gọi Remotion — chỗ duy nhất biết quy ước cwd=studio/ và ../
  run.py        cửa vào: python3 -m pipeline.run <ngày> [--render|--still N|--thumbnail]
  new.py        make new — kịch bản mới: nội dung từ ngân hàng/Claude, cài đặt kế thừa
  llm.py        gọi Claude (opus/sonnet/haiku), MẶC ĐỊNH TẮT, chỉ new.py nạp muộn
  check.py      make check — số đo MP4 + trang duyệt từng MÀN CHỮ
  export.py     make export — gói out/<ngày>/: caption, lời, audio, metadata (video + ảnh bìa đã nằm sẵn)
studio/       Lớp C (Remotion)
  src/          Composition, DailyVideo, Background, Caption, TitleCard, VoiceWave, Outro, fonts
  public/       audio/bgm-*.mp3, video/*.mp4  (commit)
                audio/<ngày>/line-XX.mp3      (máy sinh, không commit)
content/      <ngày>/       MỘT NGÀY LÀ MỘT THƯ MỤC
                script.json   người viết, commit. KHÔNG còn trường romaji;
                              `clip` CÓ THỂ bỏ trống (máy tự chọn); có thêm
                              `caption` (nội dung) và `hashtags` (cài đặt);
                              `ja`/`vi` CÓ THỂ là danh sách mảnh caption
                build.json    ★ hợp đồng, máy sinh, không commit
                .cache.json   cache TTS, máy sinh, không commit, xoá được
library/      readings.json — chữ máy đọc sai thì đè cách đọc ở đây
              shots.json — nguồn, tác giả, giấy phép và tag của mọi clip/nhạc
              bank.json — ngân hàng kịch bản viết sẵn cho `make new` khi không có khoá
out/          máy sinh, không commit. <ngày>/ là MỘT ngày đủ để đăng: <ngày>.mp4,
              <ngày>-thumbnail.png, caption.txt, description.txt, script.txt,
              credits.txt, metadata.json, audio/. Nằm ngoài là đồ soát:
              <ngày>-check/ (make check) và <ngày>-f<N>.png (make still)
.env          khoá API (KHÔNG commit) — sinh từ .env.example bằng `make setup`
docs/         cai-dat.md, tai-san-can-tai.md, mo-dau-va-ket.md,
              kich-ban-va-kiem-tra.md, dang-bai.md, caption-va-cau-dai.md
```

## Việc đang treo, chờ người làm

Không cái nào chặn dây chuyền — `make video` chạy đủ mà không cần cái nào.

| | Việc | Vì sao treo | Làm xong thì được gì |
|---|---|---|---|
| T-2 | Lấy `PIXABAY_API_KEY` | Chưa làm. Dễ hơn Pexels nhiều: đăng nhập xong khoá hiện thẳng trên `pixabay.com/api/docs/` | `make shots-find SOURCE=pixabay` chạy được. Code đã đối chiếu với tài liệu API của họ, khớp |
| T-3 | Bỏ hẳn ba clip 25fps `tea-room`, `matcha-whisk`, `tea-tray` (D-8) | Cần người xem và chọn cái thay. 49 clip mới đều 30fps rồi, nên chỉ còn ba cái cũ vướng — mà `2026-08-20.json` ghim tên cả ba, đổi là mốc hồi quy đổi theo | Hết giật ở cảnh lia chậm |
| T-5 | Quyết có cắm `ANTHROPIC_API_KEY` (s6f) | Tốn tiền theo lượt gọi; không cắm cũng không chặn gì | `make new` do Claude viết, tránh lặp ý 7 ngày gần nhất. Đường gọi thật CHƯA được kiểm — lần đầu hãy đọc kỹ kịch bản trước khi dựng |
| T-8 | Bỏ `calm` khỏi 4 mục ngân hàng đang gắn nó cạnh tag chủ đề (D-11) | Ngân hàng là file người viết, và đây là quyết định nội dung chứ không phải lỗi code | `make new` đường ngân hàng chọn clip đúng chủ đề thay vì rơi về clip trà |
| T-6 | Nới ngân hàng kịch bản | Mới có 7 mục, tức 7 ngày không cần khoá. Phần tag đã xong: cả 12 tag ngân hàng dùng giờ đều có clip mang | Chạy dài ngày không cần khoá |
| T-7 | Vài chỗ romaji tách chữ chưa chuẩn | Không sai cách đọc, chỉ sai chỗ dấu cách (`sumaseruto`, `shizumuka mo`, `ni do to`, `Da kara koso`, `Itsu mo`) — cần người đọc chốt cách viết | Sửa từng chữ bằng `library/readings.json`: dấu cách trong cách đọc là chỗ tách |

Không có khoá nào thì đường `make shots-add` vẫn làm được mọi thứ đường API làm —
xem `docs/cai-dat.md`. Khoá chỉ tiết kiệm công tìm clip.

## Trạng thái

**BƯỚC 0 tới 9 đã xong trọn vẹn.** `make content` gọi `python3 -m
pipeline.run`; `scripts/legacy_build.py` và `scripts/check_assets.py` đã bị xoá
(thư mục `scripts/` không còn).

Nghiệm thu BƯỚC 2 đạt: `2026-08-20` ra **đúng 1462 frame** (48,7 giây) và file
`build.json` **giống hệt từng byte** bản do legacy sinh ra.

Nghiệm thu BƯỚC 3 đạt: bỏ hết trường `romaji` khỏi kịch bản, romaji máy sinh
khác bản gõ tay **đúng 1 chỗ trên 9 câu** — `sukina` thành `suki na`, mà bản gõ
tay vốn tự mâu thuẫn ở chỗ này (câu 9 viết `Suteki na` có dấu cách). Số frame
không đổi, vì romaji không dính gì tới thời lượng.

> **Mốc hồi quy giờ có hai con số.** `1472` là phần THOẠI của `2026-08-20`, đã
> gồm 45 frame lặng đầu cảnh 1 cho tiêu đề ngày. `1562` là tổng sau khi cộng
> màn kết (90) — không còn màn mở đầu riêng. Đổi bất cứ thứ gì trong
> `pipeline/` xong, chạy `make content DAY=2026-08-20` và nhìn con số đó. Nó đổi
> mà bạn không cố ý đổi nhịp đọc hay nội dung kịch bản, tức là bạn vừa làm
> hỏng timeline.

> Con số này đã đổi ba lần, cả ba đều có chủ ý. Từ 1327 thành 1462 ở BƯỚC 1,
> vì `leadIn`/`pauseAfter` giãn ra (0,2/0,35 -> 0,35/0,7 giây), cộng đúng 15
> frame cho mỗi câu trong 9 câu; 1462 (tổng 1687) là mốc suốt BƯỚC 1–6. Rồi
> thành 1427 (tổng 1652) khi gộp `今日は、8月20日です。` và `おはようございます。`
> thành một dòng mở đầu: 9 câu còn 8, bớt một khoảng nghỉ, và TTS đọc liền hai vế.
> Rồi thành 1472 (tổng 1562) khi bỏ màn mở đầu nền gradient 135 frame: tiêu đề
> ngày đè lên cảnh 1, và cảnh 1 lặng thêm đúng 45 frame (1,5 giây) trước câu 1.
> Các con số 1462/1687 trong phần nghiệm thu bên dưới là số đo của thời đó.

> **BƯỚC 9 đổi đường gọi TTS mà KHÔNG đổi con số.** `tts.py` giờ gọi thư viện
> `edge_tts` trực tiếp thay vì chạy `python3 -m edge_tts`, để lấy được mốc từng
> chữ. Đã đối chiếu cả 8 câu của 2026-08-20: độ dài mp3 giống hệt tới từng mili
> giây (5.256 / 3.720 / 4.512 / 8.352 / 6.000 / 4.440 / 3.600 / 3.144). Byte thì
> khác — mp3 chèn đệm ở hai đầu khác nhau — nhưng P-1 chỉ quan tâm độ dài.

Nghiệm thu BƯỚC 4 đạt trên ba mặt:

1. **Nguồn và giấy phép truy ngược được hết.** `library/shots.json` ghi đủ năm
   tài sản. Ba clip là Pexels 8508048 / 8507912 / 8507953 — lấy từ tên file gốc
   trong commit `09e08ce`, đối chiếu md5 qua lần đổi tên `R100` ở `c61b177`.
   Hai bản nhạc là của Snoozy Beats. Tên tác giả ba clip là **Ivan S**, điền
   được sau khi đường API Pexels thông (xem phần thư viện bên dưới). Hai bản
   nhạc thì vẫn thiếu url và giấy phép, `make shots` còn kêu chỗ đó.
2. **Máy chọn clip tốt hơn tay người.** Bỏ hết trường `clip` khỏi
   `2026-08-20.json` rồi để `shots.py` tự chọn: vẫn đúng 1462 frame, không cảnh
   nào loop, và biên mỏng nhất là **48 frame (1,6 giây)** — so với **5 frame
   (0,17 giây)** của bản xếp tay. Chạy hai lần ra kết quả giống hệt.
3. **Không hồi quy.** Kịch bản còn nguyên trường `clip` thì bộ chọn không chạy,
   và `build.json` giống hệt từng byte bản trước BƯỚC 4.

Ba khiếm khuyết đo được ở BƯỚC 4 — hai đã đóng, một còn mở:

| | Khiếm khuyết | Trạng thái |
|---|---|---|
| D-6 | Ba clip nền không có nguồn, không có giấy phép | Đóng — `library/shots.json` |
| D-7 | `scripts/check_assets.py` gọi ffprobe riêng, trái quy ước "probe.py là chỗ duy nhất" | Đóng — gộp vào `pipeline/library.py`, `make assets` thành bí danh của `make shots` |
| D-8 | Cả ba clip đều 25fps trong timeline 30fps — cảnh lia chậm hơi giật | **Thu hẹp.** 49 clip thêm vào sau này đều đúng 30fps, nên hàng mới không dính. Ba clip gốc vẫn 25fps và `make shots` vẫn kêu — xem T-3 |

Nghiệm thu BƯỚC 5 đạt:

1. **Hai lượt tách bạch, đúng P-3.** Lượt Python thêm năm trường vào hợp đồng
   (`intro`, `outro`, `transition`, `transitionInFrames`, `showHira`), cả năm
   mặc định "không đổi gì cả" — `transitionInFrames` mặc định 24, đúng bằng
   hằng số `CROSSFADE` mà `DailyVideo.tsx` vẫn dùng. Bản Remotion CŨ đọc
   build.json MỚI render ra đúng video cũ, đã kiểm bằng `make still`. Lượt React
   làm sau, không đụng lại Python.
2. **Số frame khớp hai bên.** `timeline.py` và `calculateMetadata` cùng ra
   1687 = 135 + 1462 + 90. Bản render thật dài 56,3 giây, vẫn trong khoảng
   `targetSeconds` 45–60.
3. **Ba kiểu chuyển cảnh chạy được.** `crossfade` giữ nguyên hành vi cũ;
   `dip_to_black` cho frame ranh giới đen hoàn toàn (kiểm ở frame 279);
   `cut` không dành frame nào cho hiệu ứng.

Quyết định của BƯỚC 5 về dòng hiragana (s5e): **để tắt.** Bật lên xem thử thì
thấy hai vấn đề — caption thành bốn dòng lấn vào vùng an toàn, và câu nào vốn
toàn kana thì dòng hiragana lặp y hệt dòng tiếng Nhật. Vấn đề thứ hai đã sửa
(câu như vậy tự ẩn dòng đó), vấn đề thứ nhất thì không sửa được bằng code. Công
tắc `showHira` vẫn còn để đổi ý mà không phải viết lại gì.

Nghiệm thu BƯỚC 6 đạt:

1. **Kịch bản mới không cần khoá.** `make new DAY=2026-09-10` lấy mục
   `ame-no-oto` từ ngân hàng, qua `script.py`, và `make content` dựng được ngay:
   1549 frame = 51,6 giây, trong khi ước lượng trước TTS là ~52 giây (tốc độ
   đọc 4,23 chữ/giây, đo trên 2026-08-20).
2. **`make check DAY=2026-08-20` PASS cả sáu mục**, 1687 frame đếm trên chính
   MP4 — đếm gói ra đúng bằng đếm giải mã từng frame.
3. **Đường Claude chạy tới máy chủ.** Thiếu khoá, khoá sai (401) và tên model
   sai đều ra một dòng hướng dẫn, không để lại file. Chưa gọi thật lần nào vì
   chưa có khoá.

Nghiệm thu BƯỚC 8 đạt:

1. **`content/` gọn lại, không mất một byte nào.** 93 file phẳng thành 31 thư
   mục ngày, mỗi thư mục ba file ba vai trò. `git mv` giữ lịch sử hai file đã
   commit; `build.json` và `.cache.json` vào `.gitignore` đúng chỗ mới (62 file
   bị bỏ qua, không file máy sinh nào lọt vào `git status`).
2. **Mốc hồi quy không đổi:** `2026-08-20` vẫn **1472 + 90 = 1562 frame** sau
   khi dời file. `make export-all` vẫn ra đủ 31 gói.
3. **Đường dẫn gom về một chỗ.** `pipeline/paths.py` là module duy nhất biết bố
   cục; bảy module khác (`script`, `run`, `check`, `render`, `export`, `new`,
   `library`) và bốn target Makefile đều hỏi nó thay vì tự ghép chuỗi.
4. **Bố cục cũ không im lặng hỏng.** Còn sót `content/<ngày>.json` phẳng thì
   `make content` dừng lại và in đúng câu lệnh `git mv` cần gõ, chứ không báo
   "không tìm thấy kịch bản".

Nghiệm thu BƯỚC 7 đạt:

1. **Thêm trường không làm lệch frame.** `caption` vào kịch bản, `post` vào hợp
   đồng, `make export` ra đời — `2026-08-20` vẫn **1472 frame thoại + 90 frame
   kết = 1562**, đúng mốc hồi quy. Remotion không đọc `post`, nên bản cũ render
   build.json mới vẫn ra y hệt (P-3).
2. **Caption ghép đúng, ngày không gõ tay.** `2026-09-11` ra
   `11.09.26 🌿 Có nhiều thứ không thể nắm giữ…` — ngày suy từ tên kịch bản.
   Bỏ trống `caption` thì mượn câu chốt và kêu; kiểm trên `2026-08-20` trước khi
   nó có caption riêng.
3. **Cả tháng 9 dựng được, không một cảnh báo nào.** 30 ngày, 8–10 câu mỗi ngày,
   **46,6–52,8 giây** (trung bình 49,8), cả 30 đều trong khoảng `targetSeconds`
   45–60. Mỗi cảnh một clip riêng, **không ngày nào phải loop** — thư viện 52
   clip đủ rộng cho một ngày 10 cảnh không dùng lại clip nào.
4. **`make export-all` gói 31 ngày một lượt.** Cảnh báo còn lại đúng ba loại và
   cả ba đều thật: 30 ngày chưa render MP4, 31 lần nhắc `lonely-self` thiếu giấy
   phép, và 1 lần bắt được `build.json` cũ chưa có trường `post` (2026-09-10,
   dựng trước BƯỚC 7) — dựng lại là hết.

Nghiệm thu BƯỚC 9 đạt:

1. **Cắt mảnh không tốn một frame nào.** `2026-08-20` vẫn **1472 frame thoại +
   90 frame kết = 1562**, đúng mốc hồi quy, dù ba trong tám câu của nó giờ hiện
   làm hai màn chữ. Cả 31 ngày dựng lại đều ra đúng số cũ (46,6–52,8 giây).
   Kiểm bằng máy trên cả 31 build.json: các mảnh nối khít nhau, cộng lại đúng
   bằng `durationInFrames` của cảnh, ghép chữ lại ra đúng nguyên câu, và mốc
   đổi chữ luôn nằm trong quãng đang có tiếng.
2. **Cỡ chữ đứng yên ở mọi cảnh.** 286 câu ra **292 màn chữ**, màn dài nhất là
   24 chữ Nhật (ngưỡng co chữ 30) và 73 ký tự Việt (ngưỡng 88) — tức **không
   màn nào phải co chữ**, cỡ 56/38 ở khắp 31 ngày.
3. **Mốc đổi chữ là số đo, không phải ước lượng.** Câu 4 của 2026-08-20: giọng
   đọc chạm 「小さな」 ở giây 4,562, mốc tính ra frame 137 — đúng bằng
   `audioStart 10 + round(4,562 × 30) − leadIn 10`.
4. **Máy cắt được gần hết, và chỗ không cắt được thì nói ra.** 6 câu được cắt
   tự động trên 286; một câu (`2026-09-01` câu 5) bản dịch không có dấu ngắt nào
   nên `make content` kêu đúng câu đó, và nó được chia tay bằng dạng danh sách —
   ca đầu tiên dùng đường "người viết thắng máy".
5. **Remotion đọc hợp đồng mới không sai kiểu.** `tsc --noEmit` sạch. Trường
   `segments` là tuỳ chọn, bản cũ bỏ qua thì vẫn hiện nguyên `ja`/`vi` (P-3).

Ảnh bìa dời từ frame 45 sang **frame 77** (caption câu 1 vào xong) để bắt được
cả ngày tháng lẫn `おはようございます`, và `make export` giờ tự dựng ảnh bìa cho
ngày nào còn thiếu hoặc đang mang bản cũ. Cả 31 ngày dựng lại: tổng frame **y
nguyên** từng ngày (`2026-08-20` vẫn 1562) — `thumbnailFrame` không tham gia
phép cộng nào.

**Video sáng hơn, gói đăng một thư mục, emoji 🌿 cố định.** Lớp phủ toàn khung
nhẹ đi (34–88% → 4–42%); chữ đọc được nhờ quầng tối đi theo chữ và viền tối
sát nét — so trước/sau trên sáu clip sáng nhất (tuyết, mưa, hoa anh đào, rèm
trắng) trước khi sửa code. Video và ảnh bìa dựng thẳng vào `out/<ngày>/`;
`make export` và `make release` nhận `FROM`/`TO`/`MONTH`; caption mọi ngày dùng
🌿 (bỏ emoji ở đầu caption của cả 31 kịch bản). Dựng lại nội dung 20 ngày: tổng
frame và `thumbnailFrame` y nguyên từng ngày, `2026-08-20` vẫn **1562**. Render
thật trên máy Windows (bản Remotion riêng ngoài repo, vì `studio/node_modules`
chỉ có nhị phân Linux): `2026-09-12` qua `make check` PASS cả sáu mục (1564
frame đếm trên MP4), trang duyệt 11 màn chữ không tofu, không chữ nào lấn vùng
che; ảnh bìa frame 77 có đủ ngày, chủ đề và câu chào. Thời gian đo thật:
**~296 giây một video** (5,9 giây render cho mỗi giây video, Ryzen 5 5500U,
concurrency 6) — bảng từng ngày ở `docs/dang-bai.md`. Đợt dựng này **tạm dừng
theo yêu cầu sau 10 ngày (12–21/9)**; 22–30/9 chưa có video mới, và cả 19 ngày
chưa `make export` lại (caption trong `out/<ngày>/` còn là bản cũ có emoji cũ).

Một chỗ còn chưa kiểm của BƯỚC 9: bố cục câu CẮT MẢNH trên khung hình thật (khối
chữ có nở quá lên vùng tiêu đề không) — `make still DAY=2026-08-20 FRAME=614` và
`FRAME=756`.

Một khiếm khuyết BƯỚC 7 lộ ra khi dựng tháng 9, đã sửa ở phía kịch bản:

| | Khiếm khuyết | Trạng thái |
|---|---|---|
| D-11 | Kịch bản gắn `["rain","window","calm"]` mà bộ chọn ra **toàn clip trà**: `matches()` ghép tag theo kiểu HOẶC, mà `calm` nằm trên 30/52 clip nên khớp gần hết thư viện rồi rơi về thứ tự sổ | Đã sửa 12 kịch bản tháng 9 (bỏ `calm` khi đã có tag chủ đề), `2026-09-11` giờ ra 9 clip mưa/cửa sổ. **`library/bank.json` còn 4 mục dính y hệt** — chưa sửa, xem T-8 |

Hai lỗi của BƯỚC 3 lộ ra khi soi romaji ngân hàng — cả hai đã sửa, và
`build.json` của 2026-08-20 vẫn giống hệt từng byte:

| | Khiếm khuyết | Đã sửa bằng |
|---|---|---|
| D-9 | Ngày 5, 6, 8, 9, 10, 12, 30, 31 đọc sai hoặc dính chữ — `9月10日` ra `kugatsu tsuto tōka` | Romaji hoá đoạn số ngoài MeCab, phần còn lại đưa MeCab từng khúc. Quét 372/372 tổ hợp tháng-ngày ra đúng |
| D-10 | Mất macron ở chữ hoa đầu câu — `大きく` ra `Ookiku` | So nguyên âm bằng chữ thường |

Kèm theo, `library/readings.json` thêm 一歩 (`ippo`), 一杯 (`ippai`), 一期一会
(`ichigo ichie`) — ba chữ ngân hàng dùng mà máy đọc sai.

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
