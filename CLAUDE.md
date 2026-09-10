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
- **Cài thư viện Python bằng `make setup`, đừng bao giờ gõ `pip install` trần.**
  Máy dựng có hơn một Python (conda base và python của codespace). `pip` trần trỏ
  vào cái nào là tuỳ `PATH`, nên rất dễ cài xong một chỗ rồi `make` chạy ở chỗ kia
  và báo thiếu thư viện. `make setup` dùng `python3 -m pip`, tức luôn đúng trình
  thông dịch mà Makefile sẽ gọi. Vì lý do đó, mọi thông báo "thiếu thư viện"
  trong `pipeline/` đều phải in kèm `sys.executable`.
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
  Ba số này phải đổi cùng nhau, lệch nhau là mất cảm giác thong thả. Màn mở đầu
  cố tình chậm hơn nữa (34 frame): nó không phải nhường chỗ cho câu nào.
- **`calculateMetadata` và `timeline.py` phải ra CÙNG một con số.** Cả hai đều
  cộng màn mở đầu + các cảnh + màn kết. Lệch nhau là video cụt đuôi hoặc thừa
  một đoạn đen — mà không bên nào báo lỗi, phải xem mới biết.
- **Ba kiểu chuyển cảnh khác nhau ở CHỖ ĐẶT cảnh, không chỉ ở hiệu ứng.**
  `crossfade` cho cảnh bắt đầu sớm hơn T frame để chồng lên cảnh trước;
  `dip_to_black` và `cut` để cảnh nằm đúng ô của nó. Vì vậy `DailyVideo.tsx`
  (đặt cảnh) và `Background.tsx` (vẽ opacity) phải đọc cùng nhau.
- **Dòng hiragana mặc định TẮT.** Caption đã có ba dòng; dòng thứ tư ép cỡ chữ
  nhỏ lại và lấn vào vùng an toàn 380px. Bật bằng `"showHira": true` trong kịch
  bản. Câu nào vốn toàn kana thì dòng đó tự ẩn — in ra là lặp y hệt dòng trên.
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
- **Romaji do máy sinh, đừng gõ tay.** Kịch bản không có trường `romaji` nữa.
  Máy đọc sai chữ nào thì thêm cách đọc vào `library/readings.json` — bảng đó áp
  cho mọi ngày, sửa một lần là xong mãi. Đọc đối chiếu bằng `make reading`.
- **Cutlet trần không đủ, đừng gỡ ba lớp vá trong `reading.py`.** Nó không có
  macron (今日 ra `Kyou`, tức mở lại D-5), không đọc số (`8月20日` ra
  `8 gatsu 20ka`), và đọc sai chữ nhiều nghĩa. Lớp macron bám vào `pron` và
  `kana` của MeCab chứ không đoán theo mặt chữ — nhờ vậy `思う` không thành `omō`.
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
- **Bộ chọn clip phải tất định.** Không random. Cùng kịch bản, cùng thư viện thì
  phải ra cùng kết quả, nếu không thì `make content` chạy hai lần ra hai file
  khác nhau và mốc hồi quy mất nghĩa. Phá hoà bằng thứ tự dòng trong sổ.
- **Chọn clip phải chạy SAU tts.** Muốn biết clip có đủ dài không thì phải biết
  cảnh dài bao nhiêu, mà cảnh dài bao nhiêu là do giọng đọc quyết định (P-1).
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
- **Ngân hàng chọn tất định:** mục chưa dùng đầu tiên theo thứ tự trong file, hết
  thì mục dùng lâu nhất (đọc trường `source` của các kịch bản đã có). Thêm mục
  mới vào CUỐI file.
- **Đoạn kana tự sinh (số, bảng đè) romaji hoá NGOÀI MeCab, phần chữ thường đưa
  MeCab từng khúc riêng.** MeCab không biết ranh giới đoạn: 「くがつとおか」 bị
  cắt thành くが / つと / おか, mẩu vắt qua ranh giới bị sót thành
  `kugatsu tsuto tōka`. `8月20日` chỉ tình cờ cắt khớp — nên đổi gì trong
  `reading.py` thì quét đủ 12 tháng × 31 ngày, đừng chỉ thử một ngày.
- **`make check` đếm frame trên chính MP4, không tin `duration × fps`.** Độ dài
  container tính cả luồng tiếng. Đếm gói (`-count_packets`) ra cùng số với giải
  mã từng frame mà gần như không tốn CPU.
- **Không để file mẫu, file test, file trung gian nằm lại trong repo.** Muốn thử
  gì thì thử trong thư mục scratch ngoài repo.

## Cây thư mục

```
pipeline/     Lớp A + B (Python)
  env.py        nạp .env — chỗ duy nhất đọc khoá API
  intro.py      chữ cho màn mở đầu và màn kết; ngày kiểu Nhật suy từ tên kịch bản
  probe.py      đo độ dài thật bằng ffprobe — chỗ duy nhất gọi ffprobe
  script.py     đọc và kiểm content/<ngày>.json trước khi tốn công TTS
  tts.py        edge-tts từng câu + cache theo vân tay nội dung
  reading.py    sinh romaji + hiragana từ câu Nhật (cutlet, có đường lui)
  library.py    sổ đăng ký tài sản — đọc/ghi library/shots.json, soi bằng `make shots`
  fetch.py      tải clip từ Pexels/Pixabay rồi ghi sổ ngay trong một lệnh
  shots.py      chọn clip cho cảnh nào kịch bản bỏ trống trường `clip`
  assets.py     xác minh clip nền và nhạc nền có thật, đo phần còn lại sau điểm cắt
  timeline.py   ★ nơi DUY NHẤT đổi giây ra frame (P-2)
  contract.py   ghi build.json — hình dạng hợp đồng khai báo ở đây (P-3)
  render.py     gọi Remotion — chỗ duy nhất biết quy ước cwd=studio/ và ../
  run.py        cửa vào: python3 -m pipeline.run <ngày> [--render|--still N]
  new.py        make new — kịch bản mới: nội dung từ ngân hàng/Claude, cài đặt kế thừa
  llm.py        gọi Claude (opus/sonnet/haiku), MẶC ĐỊNH TẮT, chỉ new.py nạp muộn
  check.py      make check — số đo MP4 + trang duyệt từng cảnh
studio/       Lớp C (Remotion)
  src/          Composition, DailyVideo, Background, Caption, Intro, Outro, fonts
  public/       audio/bgm-*.mp3, video/*.mp4  (commit)
                audio/<ngày>/line-XX.mp3      (máy sinh, không commit)
content/      <ngày>.json  (người viết, commit — KHÔNG còn trường romaji;
                            trường `clip` giờ CÓ THỂ bỏ trống, máy tự chọn)
              <ngày>.build.json + .<ngày>.cache.json  (máy sinh, không commit)
library/      readings.json — chữ máy đọc sai thì đè cách đọc ở đây
              shots.json — nguồn, tác giả, giấy phép và tag của mọi clip/nhạc
              bank.json — ngân hàng kịch bản viết sẵn cho `make new` khi không có khoá
out/          MP4 và PNG (không commit); <ngày>-check/ là trang duyệt của make check
.env          khoá API (KHÔNG commit) — sinh từ .env.example bằng `make setup`
docs/         cai-dat.md, tai-san-can-tai.md, mo-dau-va-ket.md, kich-ban-va-kiem-tra.md
```

## Việc đang treo, chờ người làm

Không cái nào chặn dây chuyền — `make video` chạy đủ mà không cần cái nào.

| | Việc | Vì sao treo | Làm xong thì được gì |
|---|---|---|---|
| T-1 | Lấy `PEXELS_API_KEY` | Trang đăng nhập Pexels đang lỗi *"An unexpected error occurred"* — lỗi phía họ, không phải cấu hình. Cloudflare cũng chặn cả `curl` lẫn WebFetch từ máy này | Điền nốt tên tác giả ba clip trong `library/shots.json`, và `make shots-find SOURCE=pexels` chạy được |
| T-2 | Lấy `PIXABAY_API_KEY` | Chưa làm. Dễ hơn Pexels nhiều: đăng nhập xong khoá hiện thẳng trên `pixabay.com/api/docs/` | `make shots-find SOURCE=pixabay` chạy được. Code đã đối chiếu với tài liệu API của họ, khớp |
| T-3 | Tìm clip 30fps thay ba clip 25fps (D-8) | Cần người xem và chọn, máy không quyết hộ | Hết giật ở cảnh lia chậm |
| T-4 | Gắn tag cho thư viện khi nó lớn lên (s4e) | Chỉ có 3 clip nên chưa cấp bách | Bộ chọn ghép cảnh đúng chủ đề hơn |
| T-5 | Quyết có cắm `ANTHROPIC_API_KEY` (s6f) | Tốn tiền theo lượt gọi; không cắm cũng không chặn gì | `make new` do Claude viết, tránh lặp ý 7 ngày gần nhất. Đường gọi thật CHƯA được kiểm — lần đầu hãy đọc kỹ kịch bản trước khi dựng |
| T-6 | Nới ngân hàng kịch bản | Mới có 7 mục, tức 7 ngày không cần khoá. Tag `rain`, `window`, `walk`, `flower`, `garden` trong ngân hàng chưa khớp clip nào | Chạy dài ngày không cần khoá; clip đúng chủ đề hơn |
| T-7 | Vài chỗ romaji tách chữ chưa chuẩn | Không sai cách đọc, chỉ sai chỗ dấu cách (`sumaseruto`, `shizumuka mo`, `ni do to`, `Da kara koso`, `Itsu mo`) — cần người đọc chốt cách viết | Sửa từng chữ bằng `library/readings.json`: dấu cách trong cách đọc là chỗ tách |

Không có khoá nào thì đường `make shots-add` vẫn làm được mọi thứ đường API làm —
xem `docs/cai-dat.md`. Khoá chỉ tiết kiệm công tìm clip.

## Trạng thái

**BƯỚC 0 tới 6 đã xong trọn vẹn.** `make content` gọi `python3 -m
pipeline.run`; `scripts/legacy_build.py` và `scripts/check_assets.py` đã bị xoá
(thư mục `scripts/` không còn).

Nghiệm thu BƯỚC 2 đạt: `2026-08-20` ra **đúng 1462 frame** (48,7 giây) và file
`build.json` **giống hệt từng byte** bản do legacy sinh ra.

Nghiệm thu BƯỚC 3 đạt: bỏ hết trường `romaji` khỏi kịch bản, romaji máy sinh
khác bản gõ tay **đúng 1 chỗ trên 9 câu** — `sukina` thành `suki na`, mà bản gõ
tay vốn tự mâu thuẫn ở chỗ này (câu 9 viết `Suteki na` có dấu cách). Số frame
không đổi, vì romaji không dính gì tới thời lượng.

> **Mốc hồi quy giờ có hai con số.** `1462` là phần THOẠI — không đổi từ BƯỚC 1
> và không được đổi. `1687` là tổng của `2026-08-20` sau khi bật màn mở đầu
> (135) và màn kết (90). Kịch bản không khai `intro`/`outro` thì tổng vẫn đúng
> 1462, nên mốc cũ còn nguyên giá trị. Đổi bất cứ thứ gì trong
> `pipeline/` xong, chạy `make content DAY=2026-08-20` và nhìn con số đó. Nó đổi
> mà bạn không cố ý đổi nhịp đọc, tức là bạn vừa làm hỏng timeline.

> Con số này từng là 1327 trước BƯỚC 1, đổi vì `leadIn`/`pauseAfter` giãn ra
> (0,2/0,35 -> 0,35/0,7 giây), cộng đúng 15 frame cho mỗi câu trong 9 câu.

Nghiệm thu BƯỚC 4 đạt trên ba mặt:

1. **Nguồn và giấy phép truy ngược được hết.** `library/shots.json` ghi đủ năm
   tài sản. Ba clip là Pexels 8508048 / 8507912 / 8507953 — lấy từ tên file gốc
   trong commit `09e08ce`, đối chiếu md5 qua lần đổi tên `R100` ở `c61b177`.
   Hai bản nhạc là của Snoozy Beats. **Tên tác giả ba clip vẫn để trống**, vì
   Pexels chặn cả `curl` lẫn WebFetch bằng Cloudflare; điền nốt được khi có
   `PEXELS_API_KEY`, và `make shots` kêu cho tới lúc đó.
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
| D-8 | Cả ba clip đều 25fps trong timeline 30fps — cảnh lia chậm hơi giật | **Còn mở.** `make shots` cảnh báo. Sửa bằng cách tìm clip 30fps, không sửa được bằng code |

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
