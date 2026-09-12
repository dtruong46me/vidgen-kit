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

`make release` giờ gọi cả `make export` ở bước cuối, nên sau nó thư mục
`out/2026-09-11/` đã đủ để mở ra và đăng.

Chỉ muốn gói lại (sửa caption xong, không muốn render lại):

```bash
make content DAY=2026-09-11    # dựng lại build.json để caption mới vào
make export  DAY=2026-09-11    # gói lại — không đụng tới MP4 đã có
```

---

## Trường `caption`

Một dòng tiếng Việt trong `content/<ngày>/script.json`, **không hiện trong video**:

```json
{
  "id": "2026-09-11",
  "title": "9月11日 - 手放す",
  "caption": "🌿 Có nhiều thứ không thể nắm giữ, không phải chuyện gì cũng có kết quả",
  ...
}
```

Máy ghép ngày vào đầu, ra đúng dòng để dán:

```
11.09.26 🌿 Có nhiều thứ không thể nắm giữ, không phải chuyện gì cũng có kết quả
```

**Đừng gõ ngày vào `caption`.** Ngày suy từ tên kịch bản, đúng tinh thần P-1 —
gõ tay là sẽ có ngày lệch với tiêu đề trong video. Định dạng `DD.MM.YY` khai ở
`DATE_FORMAT` trong `pipeline/post.py`, đổi một chỗ là đổi cho mọi ngày.

**Emoji nằm trong chính chuỗi**, không phải trường riêng. Mỗi ngày một chủ đề
thì emoji cũng khác; tách ra thành trường riêng chỉ tổ phải nhớ thứ tự ghép, mà
người viết thì muốn nhìn thấy nguyên câu mình sắp đăng.

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
make export DAY=2026-09-11     # gói một ngày
make export-all                # gói MỌI ngày đã có build.json
```

Sinh ra `out/2026-09-11/`:

| File | Dùng để làm gì |
|---|---|
| `caption.txt` | Dòng caption + hashtag. Dán thẳng TikTok/Reels |
| `description.txt` | Caption + toàn bộ lời Nhật–Việt + ghi công. Dán YouTube |
| `script.txt` | Bảng đọc từng câu: Nhật / romaji / hiragana / Việt |
| `metadata.json` | Mọi số đo và mọi trường máy đọc được |
| `credits.txt` | Nguồn, tác giả, giấy phép từng clip và bản nhạc |
| `audio/line-XX.mp3` | Giọng đọc từng câu |
| `<ngày>.mp4`, `<ngày>-thumbnail.png` | Video và ảnh bìa, nếu đã dựng |

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

Thư mục cũ bị **xoá trước khi gói lại**. Bớt một câu rồi gói lại mà còn
`line-09.mp3` nằm lại thì người đăng sẽ tưởng video có chín câu.

### Không có dấu thời gian trong `metadata.json`

Cố tình. Gói hai lần phải ra hai thư mục giống hệt nhau — y như bộ chọn clip
phải tất định. Có dấu thời gian thì `diff` lúc nào cũng khác và mất luôn tác
dụng làm mốc.

### Những chỗ `make export` kêu

- `caption đang mượn câu chốt` — kịch bản chưa khai `caption`.
- `build.json chưa có trường "post"` — build.json dựng bằng bản pipeline trước
  BƯỚC 7. Chạy `make content` lại.
- `chưa có out/<ngày>.mp4` — gói thiếu video, chạy `make video`.
- `<tên clip> thiếu tác giả, giấy phép, nguồn` — `library/shots.json` còn trống
  chỗ đó. Xem `make shots`.

---

## Cả tháng một lượt

```bash
# 1. Soạn kịch bản cho từng ngày (hoặc viết tay vào content/)
for d in 01 02 03 04 05; do make new DAY=2026-10-$d; done

# 2. Mở content/2026-10-*/script.json ra viết caption cho từng ngày
#    (bỏ qua cũng được — máy mượn câu chốt và kêu)

# 3. Dựng nội dung mọi ngày chưa có build.json: TTS + chọn clip + timeline
make content-all

# 4. Soát trước khi tốn CPU render: đọc caption và lời của cả tháng
make export-all
less out/2026-10-01/script.txt

# 5. Render mọi ngày chưa có MP4 (lâu — khoảng 34 phút một video)
make all

# 6. Gói lại để MP4 và ảnh bìa vào trong từng thư mục
make export-all
```

Bước 4 và 6 là cùng một lệnh, chạy hai lần có chủ ý: lần đầu để **soát chữ**
trước khi render, lần sau để **gộp video** vào gói. Bước 4 rẻ (vài giây), bước 5
đắt (hàng giờ) — soát trước thì phát hiện câu sai lúc còn sửa được rẻ.

`make content-all` bỏ qua ngày nào đã có `build.json`. Muốn dựng lại một ngày
thì xoá `content/<ngày>/build.json` rồi chạy lại, hoặc gọi thẳng
`make content DAY=...`.

---

## Xem thêm

- Trường nào là nội dung, trường nào là cài đặt: `docs/kich-ban-va-kiem-tra.md`
- Nguồn và giấy phép clip: `docs/tai-san-can-tai.md`
- Tiêu đề ngày và màn kết: `docs/mo-dau-va-ket.md`
- Caption TRÊN MÀN HÌNH, cỡ chữ và câu dài: `docs/caption-va-cau-dai.md`
