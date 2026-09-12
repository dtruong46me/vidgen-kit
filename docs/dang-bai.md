# Caption và gói đăng bài

Video dựng xong vẫn chưa đăng được. Còn thiếu dòng caption, còn thiếu bản chữ để
soát lại, còn thiếu chỗ ghi công tác giả clip. Hai thứ trong tài liệu này lấp
chỗ đó: trường `caption` trong kịch bản, và lệnh `make export` gói mọi thứ lại.

---

## Một ngày làm việc, bản đầy đủ

```bash
make new     DAY=2026-09-11    # tạo content/2026-09-11/script.json
                               # mở ra viết caption, sửa câu nào muốn sửa
make reading DAY=2026-09-11    # đọc đối chiếu romaji máy sinh
make release DAY=2026-09-11    # MP4 + ảnh bìa + check + GÓI ĐĂNG, một lệnh
```

Sau `make release`, thư mục `out/2026-09-11/` đã đủ để mở ra và đăng.

Chỉ muốn gói lại (sửa caption xong, không muốn render lại):

```bash
make content DAY=2026-09-11    # dựng lại build.json để caption mới vào
make export  DAY=2026-09-11    # gói lại — không đụng tới MP4 đã có
```

---

## Trường `caption`

Một dòng tiếng Việt trong `content/<ngày>/script.json`, **không hiện trong
video**. Chỉ viết câu chữ — không ngày, không emoji:

```json
{
  "id": "2026-09-11",
  "title": "9月11日 - 手放す",
  "caption": "Có nhiều thứ không thể nắm giữ, không phải chuyện gì cũng có kết quả",
  ...
}
```

Máy ghép ngày và emoji vào đầu, ra đúng dòng để dán:

```
11.09.26 🌿 Có nhiều thứ không thể nắm giữ, không phải chuyện gì cũng có kết quả
```

**Đừng gõ ngày vào `caption`.** Ngày suy từ tên kịch bản, đúng tinh thần P-1 —
gõ tay là sẽ có ngày lệch với tiêu đề trong video. Định dạng `DD.MM.YY` khai ở
`DATE_FORMAT` trong `pipeline/post.py`, đổi một chỗ là đổi cho mọi ngày.

**Emoji là 🌿 cho MỌI ngày**, khai ở `EMOJI` trong cùng file đó. Trước đây mỗi
kịch bản tự chọn một emoji hợp chủ đề (🍵, 🌅, 🪵…), nên lướt trang kênh thì mỗi
bài một kiểu. Giờ nó là dấu nhận diện của kênh, cùng loại với định dạng ngày.
Kịch bản nào còn để emoji ở đầu `caption` thì máy bỏ nó đi và `make content`
nhắc một dòng `[!]` — không bao giờ in hai emoji liền nhau.

Bỏ trống `caption` cũng chạy: máy mượn tạm câu tiếng Việt cuối cùng của kịch bản
(lời chúc chốt video) và nhắc một dòng `[!]` ở cả `make content` lẫn
`make export`. Tạm được, nhưng nhạt — ngày nào cũng "Chúc bạn một ngày tốt lành".

### `hashtags` là CÀI ĐẶT, không phải nội dung

```json
"hashtags": ["tiengnhat", "hoctiengnhat", "nhatngu", "chualanh", "songchamlai"]
```

Kênh nào cũng một bộ thẻ, nên nó nằm cùng chỗ với giọng đọc và nhạc nền: sửa ở
ngày gần nhất một lần là mọi ngày `make new` sau đó tự kế thừa. `caption` thì
ngược lại — nó ở trong `CONTENT_KEYS` của `pipeline/new.py`, tức không kế thừa,
vì mỗi ngày một câu khác.

Viết thẻ không cần dấu `#`; `make export` tự thêm.

---

## `make export`

```bash
make export DAY=2026-09-11                   # một ngày
make export FROM=2026-09-12 TO=2026-09-30    # từ ngày tới ngày, tính cả hai đầu
make export FROM=2026-09-12                  # từ ngày đó tới ngày cuối cùng đã dựng
make export MONTH=2026-09                    # cả tháng
make export-all                              # MỌI ngày đã có build.json
```

`make release` nhận đúng những biến đó. Cách đọc khoảng ngày nằm ở một chỗ,
`select` trong `pipeline/paths.py`.

Mỗi ngày một thư mục, đủ thứ để đăng — `out/2026-09-11/`:

| File | Dùng để làm gì |
|---|---|
| `<ngày>.mp4` | Video để đăng. Remotion dựng thẳng vào đây |
| `<ngày>-thumbnail.png` | Ảnh bìa. Remotion dựng thẳng vào đây — thiếu thì `make export` dựng luôn |
| `caption.txt` | Dòng caption + hashtag. Dán thẳng TikTok/Reels |
| `description.txt` | Caption + toàn bộ lời Nhật–Việt + ghi công. Dán YouTube |
| `script.txt` | Bảng đọc từng câu: Nhật / romaji / hiragana / Việt |
| `metadata.json` | Mọi số đo và mọi trường máy đọc được |
| `credits.txt` | Nguồn, tác giả, giấy phép từng clip và bản nhạc |
| `audio/line-XX.mp3` | Giọng đọc từng câu |

Ngoài thư mục ngày chỉ còn đồ để SOÁT, không phải để đăng: trang duyệt
`out/<ngày>-check/` của `make check` và ảnh tĩnh `out/<ngày>-f<frame>.png` của
`make still`.

`script.txt` trông thế này:

```
9月11日 - 手放す
2026-09-11 · 9 câu · 51.2 giây

────────────────────────────────────────────────────────────────

 1. 今日は、9月11日です。おはようございます。
    Kyō wa, kugatsu jūichinichi desu. Ohayō gozaimasu.
    きょうは、くがつじゅういちにちです。おはようございます。
    Hôm nay là ngày 11 tháng 9. Chào buổi sáng.
```

### Lệnh này không dựng gì cả

`make export` chỉ **đọc** `content/<ngày>/build.json` và đo lại MP4 nếu có. Nó
không gọi TTS, không chọn clip, không tính một frame nào — phép cộng frame duy
nhất nó dùng là mượn của `check.py` (P-2). Vì vậy chạy lại bao nhiêu lần cũng
được, và sửa `export.py` không bao giờ làm lệch video.

**Đúng một ngoại lệ: ảnh bìa.** Thiếu `out/<ngày>/<ngày>-thumbnail.png`, hoặc
file đó cũ hơn `build.json`, thì `make export` gọi Remotion chụp lại. Gói không
có ảnh bìa là gói chưa đăng được, mà ảnh bìa chỉ tốn MỘT frame chứ không phải cả
video. Ngoại lệ này không phá nguyên tắc trên: frame chụp là `thumbnailFrame` đã
ghi sẵn trong hợp đồng, `export.py` không tự tính. Ngày nào đã có ảnh bìa mới thì
không dựng lại, nên lần gói thứ hai vẫn nhanh và vẫn ra thư mục giống hệt. Dựng
không được (chưa cài Remotion) thì nó kêu một dòng rồi gói tiếp, không chặn.

**Gói lại chỉ xoá phần nó viết ra.** `caption.txt`, `description.txt`,
`script.txt`, `credits.txt`, `metadata.json` và `audio/` bị xoá rồi viết lại —
bớt một câu mà còn `line-09.mp3` nằm lại thì người đăng sẽ tưởng video có chín
câu. Video và ảnh bìa nằm cùng thư mục thì KHÔNG bị đụng tới: xoá theo là mất
nửa tiếng render.

**Bố cục cũ tự dời vào.** Video dựng trước khi đổi bố cục nằm lẻ ở
`out/<ngày>.mp4` (ảnh bìa ở `out/<ngày>-thumbnail.png`). `make export` DỜI
chúng vào thư mục ngày — dời chứ không chép, để mỗi video chỉ nằm một chỗ.

### Không có dấu thời gian trong `metadata.json`

Cố tình. Gói hai lần phải ra hai thư mục giống hệt nhau — y như bộ chọn clip
phải tất định. Có dấu thời gian thì `diff` lúc nào cũng khác và mất luôn tác
dụng làm mốc.

### Những chỗ `make export` kêu

- `caption đang mượn câu chốt` — kịch bản chưa khai `caption`.
- `build.json chưa có trường "post"` — build.json dựng bằng bản pipeline trước
  BƯỚC 7. Chạy `make content` lại.
- `chưa có out/<ngày>/<ngày>.mp4` — gói thiếu video, chạy `make video`.
- `chưa dựng được ảnh bìa: …` — Remotion chưa chạy được ở máy này. Gói vẫn đủ
  phần chữ; chạy `make thumbnail DAY=...` ở máy dựng được là có.
- `<ngày>-thumbnail.png là bản chụp từ lần dựng trước` — có ảnh bìa, nhưng nó cũ
  hơn `build.json`, tức chụp ở frame của bản kịch bản trước. Gói vẫn mang nó
  theo, nhưng đừng đăng trước khi chụp lại.
- `còn bản cũ out/<ngày>.mp4 nằm lẻ ngoài` — thư mục ngày đã có video của nó,
  nên bản lẻ không được dời vào. Xem lại rồi xoá bản lẻ.
- `<tên clip> thiếu tác giả, giấy phép, nguồn` — `library/shots.json` còn trống
  chỗ đó. Xem `make shots`.

---

## Cả tháng (hay cả tuần) một lượt

```bash
# 1. Soạn kịch bản cho từng ngày (hoặc viết tay vào content/)
for d in 01 02 03 04 05; do make new DAY=2026-10-$d; done

# 2. Mở content/2026-10-*/script.json ra viết caption cho từng ngày
#    (bỏ qua cũng được — máy mượn câu chốt và kêu)

# 3. Dựng nội dung mọi ngày chưa có build.json: TTS + chọn clip + timeline
make content-all

# 4. Soát trước khi tốn CPU render: đọc caption và lời của cả tháng
make export MONTH=2026-10
less out/2026-10-01/script.txt

# 5. Render + check + gói từng ngày (lâu — xem "Thời gian dựng" bên dưới)
make release MONTH=2026-10
```

Tuần thì thay `MONTH` bằng `FROM=2026-10-05 TO=2026-10-11`.

`make release` với nhiều ngày chạy lần lượt: render → check → gói, xong ngày này
mới sang ngày sau. Trong một ngày, render hỏng thì không check, check FAIL thì
không gói. Nhưng một ngày hỏng KHÔNG chặn các ngày sau — render cả tháng mất
hàng giờ, dừng giữa đêm vì một ngày thì sáng ra chẳng còn gì. Cuối lệnh in ra
ngày nào hỏng để chạy lại riêng bằng `make release DAY=...`.

Bước 4 rẻ (vài giây), bước 5 đắt (hàng giờ) — soát trước thì phát hiện câu sai
lúc còn sửa được rẻ.

`make content-all` bỏ qua ngày nào đã có `build.json`. Muốn dựng lại một ngày
thì xoá `content/<ngày>/build.json` rồi chạy lại, hoặc gọi thẳng
`make content DAY=...`.

---

## Thời gian dựng — số đo thật

Render là bước đắt duy nhất của cả dây chuyền. Số dưới đây đo khi dựng lại
tháng 9 sau lượt đổi lớp phủ sáng hơn (đêm 2026-09-12 sang 13), mỗi ngày gồm
MP4 **và** ảnh bìa.

**Máy:** Windows 11, AMD Ryzen 5 5500U (6 nhân 12 luồng), 19 GB RAM. Remotion
4.0.513 bản Windows, `--concurrency=6`, bundle dựng sẵn một lần (59 giây).

| Ngày | Video | Render | Giây render / giây video | MP4 |
|---|---:|---:|---:|---:|
| 2026-09-12 | 52,1 s | 304 s | 5,8 | 63,5 MB |
| 2026-09-13 | 49,0 s | 326 s | 6,7 | 104,8 MB |
| 2026-09-14 | 48,1 s | 283 s | 5,9 | 65,0 MB |
| 2026-09-15 | 47,8 s | 287 s | 6,0 | 117,3 MB |
| 2026-09-16 | 51,2 s | 292 s | 5,7 | 54,4 MB |
| 2026-09-17 | 48,9 s | 273 s | 5,6 | 71,3 MB |
| 2026-09-18 | 48,2 s | 286 s | 5,9 | 103,8 MB |
| 2026-09-19 | 49,3 s | 296 s | 6,0 | 89,6 MB |
| 2026-09-20 | 52,1 s | 293 s | 5,6 | 74,7 MB |
| 2026-09-21 | 52,6 s | 321 s | 6,1 | 111,6 MB |
| **10 ngày** | **499,3 s** | **2961 s = 49,4 phút** | **5,9** | |

- Trung bình **~5 phút một video** (273–326 giây). Nhẩm nhanh: **khoảng 6 giây
  render cho mỗi giây video**.
- Suy ra: một tuần ≈ **35 phút**, cả tháng 30 ngày ≈ **2,5 giờ**.
- Máy dựng yếu chậm hơn hẳn: máy 2 nhân / 3 GB trống (WSL, `setConcurrency(1)`
  trong `remotion.config.ts`) mất khoảng **34 phút một video** — số đo ở BƯỚC 6.
  Con số 1 đó là giới hạn của máy yếu chứ không phải của code; máy khoẻ thì
  truyền `--concurrency` cao hơn.
- MP4 nặng 54–117 MB cho cùng ~50 giây: tuỳ clip nền (mưa, lá lay nhiều thì
  nặng), không phải lỗi.

### Đợt dựng 12–30/9 — đang tạm dừng

- **Xong 10 ngày, 12–21/9:** MP4 và ảnh bìa mới (lớp phủ sáng) nằm trong
  `out/<ngày>/`. `2026-09-12` đã qua `make check` PASS cả sáu mục.
- **Dừng giữa ngày 22/9 theo yêu cầu** (00:39 ngày 13/9). Remotion ghi ra file
  tạm rồi mới đổi tên, nên không có MP4 dở dang nào nằm lại.
- **Còn 9 ngày, 22–30/9:** chưa có video mới — ước ~45 phút ở máy trên.
- **Chưa gói lại cả 19 ngày.** `caption.txt`, `script.txt`, `metadata.json`…
  trong `out/<ngày>/` vẫn là bản gói lúc 16:23 ngày 12/9, caption còn emoji cũ.

Làm tiếp:

```bash
make export  FROM=2026-09-12 TO=2026-09-21   # gói lại 10 ngày đã có video — vài giây
make release FROM=2026-09-22                 # render + check + gói 22–30/9
```

---

## Xem thêm

- Trường nào là nội dung, trường nào là cài đặt: `docs/kich-ban-va-kiem-tra.md`
- Nguồn và giấy phép clip: `docs/tai-san-can-tai.md`
- Tiêu đề ngày và màn kết: `docs/mo-dau-va-ket.md`
- Caption TRÊN MÀN HÌNH, cỡ chữ và câu dài: `docs/caption-va-cau-dai.md`
