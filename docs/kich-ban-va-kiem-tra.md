# Kịch bản mới và kiểm tra video

Hai lệnh của BƯỚC 6: `make new` tạo kịch bản cho một ngày, `make check` kiểm
video đã dựng xong. Không lệnh nào cần khoá API.

---

## Một ngày làm việc

```bash
make new     DAY=2026-09-10    # tạo content/2026-09-10/script.json
                               # mở file ra đọc, sửa câu nào muốn sửa
make reading DAY=2026-09-10    # đọc đối chiếu romaji máy sinh
make release DAY=2026-09-10    # MP4 + ảnh bìa + check; ~34 phút cho 52 giây video (WSL, concurrency 1)
```

`make release` là `make video` (nội dung, MP4, ảnh bìa), `make check` (số đo,
trang duyệt) rồi `make export` (gói thư mục đăng) trong một lệnh. Render hỏng thì
dừng trước check. Muốn làm từng bước thì ba lệnh kia vẫn gọi riêng được.

Caption bài đăng và thư mục `out/<ngày>/` nằm ở tài liệu riêng:
**`docs/dang-bai.md`**.

---

## `make new`

Kịch bản gồm hai phần, lấy từ hai chỗ khác nhau:

| Phần | Gồm | Lấy từ đâu |
|---|---|---|
| **Nội dung** | chủ đề, tag, **caption**, các câu Nhật + Việt | ngân hàng viết sẵn, hoặc Claude |
| **Cài đặt** | giọng đọc, nhạc nền, nhịp nghỉ, khoảng lặng đầu video, màn kết, `targetSeconds`, **hashtags** | **kịch bản của ngày gần nhất** |

Nên muốn đổi nhạc nền hay đọc chậm lại cho mọi ngày sau, chỉ cần sửa ở ngày gần
nhất một lần. Ngân hàng và prompt không chứa cài đặt nào.

### Nội dung lấy từ đâu

| Lệnh | Nội dung |
|---|---|
| `make new DAY=...` | Có `ANTHROPIC_API_KEY` thì Claude Opus viết; không có thì lấy ngân hàng |
| `make new DAY=... MODEL=bank` | Luôn lấy ngân hàng, dù có khoá |
| `make new DAY=... MODEL=opus` | Claude Opus 5 — viết tiếng Nhật tự nhiên nhất |
| `make new DAY=... MODEL=sonnet` | Claude Sonnet 5 — rẻ hơn chừng một nửa |
| `make new DAY=... MODEL=haiku` | Claude Haiku 4.5 — rẻ nhất, hợp để thử đường ống |

Chưa từng điền khoá thì **không bao giờ** có lời gọi mạng nào tốn tiền (DEC-06).

### Những điều lệnh này luôn làm

- **Không đè kịch bản đã có.** Đó là file người viết. Muốn tạo lại thì xoá nó trước.
- **Kiểm ngay bằng `script.py`** — đúng bộ kiểm mà `make content` dùng. Không
  qua thì file bị xoá, không để lại kịch bản hỏng.
- **Bỏ trống trường `clip`.** `shots.py` chọn clip sau khi TTS đo xong độ dài.
- **Ghi trường `source`** (`{"writer": "bank", "id": "ame-no-oto"}`). `script.py`
  bỏ qua trường này; `make new` đọc nó để không lấy lại mục ngân hàng vừa dùng.
- **In ước lượng thời lượng** và cảnh báo nếu câu quá dài, quá ít/nhiều câu,
  hoặc ước lượng rơi ngoài `targetSeconds`.
- **Nhắc nếu chưa có `caption`.** Ngân hàng không giữ caption, nên đường ngân
  hàng luôn nhắc; đường Claude thì model viết luôn một câu. Xem `docs/dang-bai.md`.

### Ước lượng độ dài tin được đến đâu

Giọng Nanami đọc **4,23 chữ/giây** (không tính dấu câu) — đo trên 2026-08-20,
166 chữ ra 39,27 giây audio. Thử trên `2026-09-10` (mục `ame-no-oto`):

| | Thời lượng |
|---|---|
| Ước lượng lúc `make new` | ~52 giây |
| Thật, sau `make content` | 51,6 giây |

Đây vẫn chỉ là ước lượng để bắt kịch bản quá dài/quá ngắn *trước khi* tốn công
TTS. Con số thật luôn là số `make content` in ra (P-1).

---

## Ngân hàng kịch bản — `library/bank.json`

```bash
make bank          # mỗi mục: số câu, số chữ, ước lượng giây, đã dùng ngày nào
```

Máy chọn **mục chưa dùng đầu tiên theo thứ tự trong file**. Dùng hết thì quay lại
mục dùng lâu nhất. Không random — cùng một repo thì luôn ra cùng một mục.

### Thêm một mục

```json
{
  "id": "ten-ngan-khong-dau",
  "theme": "雨の音",
  "tags": ["rain", "window", "calm"],
  "lines": [
    { "ja": "今日は、{date}です。おはようございます。", "vi": "Hôm nay là {date_vi}. Chào buổi sáng." },
    { "ja": "窓の外で、静かに雨が降っています。", "vi": "Ngoài cửa sổ, mưa đang rơi thật khẽ." }
  ]
}
```

- **Thêm vào CUỐI** mảng `scripts`, để không đảo thứ tự các mục cũ.
- **Dòng đầu cố định: nói ngày trước, chào sau, chung một dòng** — đúng như ví dụ
  trên. Dòng đó khai ở `OPENING` trong `pipeline/new.py`; `make bank` đánh dấu
  `[!]` mục nào lệch, `make new` cũng cảnh báo.
- `theme` là chủ đề hiện nhỏ dưới ngày tháng ở đầu video, nét bút lông: 2–8 chữ.
- `{date}` ra `9月10日`, `{date_vi}` ra `ngày 10 tháng 9`.
- Giữ trong khoảng **120–180 chữ, 8–10 câu, mỗi câu dưới 40 chữ**. `make bank`
  đánh dấu `[!]` mục nào ước lượng ra ngoài khoảng.
- **Không có** `romaji`, `clip` — máy sinh cả hai.
- `tags` nên dùng tag mà thư viện clip đang có (`make shots`). Tag không khớp
  clip nào thì bộ chọn lấy clip bất kỳ — không lỗi, chỉ kém đúng chủ đề.

Sau khi thêm, tạo thử rồi đọc romaji:

```bash
make new DAY=2026-12-01 MODEL=bank
make reading DAY=2026-12-01
```

Chữ nào máy đọc sai thì thêm cách đọc vào `library/readings.json`, đừng sửa ngân
hàng. Muốn romaji tách chữ thì đặt dấu cách trong cách đọc (`"一期一会": "いちご いちえ"`).

---

## Bật Claude

1. Điền `ANTHROPIC_API_KEY=...` vào `.env` (lấy ở https://console.anthropic.com/).
2. `make new DAY=...` — từ giờ nó gọi Claude Opus 5.

Những gì được gửi đi, và không gì khác:

- ngày (kèm thứ trong tuần),
- dòng mở đầu cố định (`OPENING`, ngày đã điền sẵn) — model chép nguyên văn,
- khoảng số chữ suy ra từ `targetSeconds` của ngày gần nhất (hiện là 127–173 chữ),
- số câu 8–10, tối đa 40 chữ mỗi câu,
- danh sách tag thư viện clip đang có,
- mọi câu tiếng Nhật của **7 ngày gần nhất** — vừa làm mẫu giọng văn, vừa để
  tránh lặp ý.

Prompt nằm ở `SYSTEM` trong `pipeline/llm.py`, viết bằng tiếng Việt để sửa được.
Đầu ra dùng structured outputs nên luôn đúng hình dạng JSON. Riêng Opus 5 bật
`fallbacks: "default"`: nếu bộ lọc an toàn từ chối, máy chủ tự chạy lại trên
model dự phòng thay vì trả về lời từ chối. Sau mỗi lần gọi, lệnh in số token vào/ra.

**Đã kiểm:** thiếu khoá, khoá sai (máy chủ trả 401) và tên model sai đều ra một
dòng hướng dẫn, không traceback, không để lại file. **Chưa kiểm:** một lần gọi
thật có khoá — nên chưa có số đo chi phí hay chất lượng. Lần gọi đầu tiên hãy
đọc kỹ kịch bản trước khi `make content`.

---

## `make check`

```bash
make check DAY=2026-08-20
```

```
  PASS  Khổ hình     1080×1920
  PASS  fps          30
  PASS  Luồng tiếng  có
  PASS  Số frame     1562 = 1472 thoại + 90 kết
  PASS  Thời lượng   ~52s, khoảng mong muốn 45–60s
  PASS  Độ mới       MP4 dựng sau build.json
```

| Mục | Kiểm gì | FAIL nghĩa là |
|---|---|---|
| Khổ hình | bề ngang × bề dọc thật của MP4 | render sai composition |
| fps | fps thật | Remotion và timeline hiểu khác nhau |
| Luồng tiếng | MP4 có luồng audio | video câm — ảnh tĩnh không bao giờ lộ ra |
| **Số frame** | đếm trên chính MP4, so với tổng build.json hứa | video cụt đuôi hoặc thừa đoạn đen |
| Thời lượng | nằm trong `targetSeconds` của kịch bản | quá dài/ngắn cho nền tảng |
| Độ mới | MP4 dựng sau build.json | **WARN**, không FAIL: có thể đang xem bản dựng cũ |

`Độ mới` báo WARN cả khi `make content` dựng lại ra build.json giống hệt — nó
chỉ so giờ sửa file. Thấy WARN thì `make video` lại cho chắc.

Lệnh trả mã lỗi 1 nếu có mục FAIL, nên xâu được — `make release DAY=...` chính là
`make video` rồi `make check` xâu sẵn.

### Trang duyệt

Ghi ra `out/<ngày>-check/`:

- **`sheet.jpg`** — mở thẳng trong VS Code. Mỗi ô một khung: giữa
  từng cảnh (cảnh 1 có cả tiêu đề ngày), màn kết. Viền đỏ là vùng giao diện TikTok/Reels che (đáy 380px,
  dải phải 110px).
- **`index.html`** — cùng các khung đó, kèm bảng số đo và **chữ lẽ ra phải hiện**
  ngay dưới mỗi ảnh.

Hai lỗi máy không bắt được mà mắt thấy trong một giây:

- **Tofu** — chữ trong ảnh ra ô vuông trong khi chữ bên dưới hiện bình thường:
  font thiếu glyph.
- **Phụ đề bị che** — chữ lấn vào viền đỏ.

Cả lệnh mất khoảng 10 giây.

Câu dài được cắt thành nhiều **màn chữ** trong cùng một cảnh, và trang duyệt
trích một ảnh cho mỗi màn (`Cảnh 4 · mảnh 1`). Xem `docs/caption-va-cau-dai.md`.
