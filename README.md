# vidgen-kit

Dây chuyền làm video triết lý Nhật – Việt dạng dọc 1080×1920, mỗi ngày một
video. Trang này là **bản đồ**: có những lệnh nào, lệnh nào ra file gì, và nên
gộp bước nào khi nào. Chi tiết từng phần nằm trong `docs/`, quy ước cho người sửa
code nằm trong `CLAUDE.md`.

Máy mới thì cài trước: `make setup` (xem `docs/cai-dat.md`). Quên lệnh thì gõ
`make` — bảng lệnh in ra ngay.

---

## Từ ngữ — mỗi từ đúng một nghĩa

| Từ | Nghĩa |
|---|---|
| **soạn** | Python sinh ra nguyên liệu. Không bao giờ có nghĩa là render |
| **nguyên liệu** | giọng đọc mp3 + `build.json`. Thành phẩm của `make build` |
| **render** | Remotion vẽ ra file hình: MP4, ảnh bìa, ảnh tĩnh |
| **kiểm** | MÁY tự kết luận đạt/hỏng |
| **soát** | MẮT NGƯỜI kết luận: trang soát, ảnh tĩnh, romaji |
| **gói** | viết ra `out/<ngày>/` đủ thứ để đăng. Chỉ `make export` làm việc này |
| **lời đăng** | chữ dán vào bài đăng TikTok/Reels. KHÔNG hiện trong video (trường `caption`, file `caption.txt`) |
| **caption** | chữ hiện TRÊN HÌNH |
| **màn chữ** | một lần chữ đổi trên hình. Câu dài chia mảnh thì một cảnh có nhiều màn chữ |

Bảng đủ nằm ở đầu `Makefile`.

---

## Dây chuyền một ngày

Mỗi bước ghi ra một file mở lên xem được. Hỏng ở đâu thì mở file của bước đó ra
xem, khỏi đọc log.

```
 LỆNH                       SINH RA                                    AI XEM
 ─────────────────────────────────────────────────────────────────────────────────
 make new     DAY=…   ──►  content/<ngày>/script.json                  BẠN: sửa câu,
                              │                                        viết lời đăng
 make reading DAY=…           │  chỉ in romaji ra để soát — không sinh file
                              ▼
 make build   DAY=…   ──►  studio/public/audio/<ngày>/line-XX.mp3      nghe thử
                           content/<ngày>/build.json   ★ hợp đồng      mở JSON
                              │
 make still   DAY=…           │  render 1 frame ra PNG để soát bố cục (vài giây)
 make studio  DAY=…           │  mở Remotion Studio để tua xem
                              ▼
 make video   DAY=…   ──►  out/<ngày>/<ngày>.mp4                       ~5 phút
                           out/<ngày>/<ngày>-thumbnail.png
                              │
 make check   DAY=…   ──►  out/<ngày>-check/index.html                 MÁY: PASS/FAIL
                              │                                        MẮT: trang soát
                              ▼
 make export  DAY=…   ──►  out/<ngày>/caption.txt  description.txt
                                      script.txt   credits.txt
                                      metadata.json  audio/
                              ▼
                            ĐĂNG — mở out/<ngày>/ ra là đủ
```

Từng bước làm gì:

| Lệnh | Làm gì | Tốn |
|---|---|---|
| `make new` | Viết kịch bản mới: nội dung lấy từ ngân hàng (hoặc Claude nếu có khoá), cài đặt kế thừa ngày gần nhất. **Không bao giờ đè** kịch bản đã có | tức thì |
| `make reading` | In romaji + hiragana máy sinh. Máy đọc sai chữ nào thì thêm vào `library/readings.json` | tức thì |
| `make build` | Kiểm kịch bản → đọc TTS từng câu → sinh romaji → chọn clip cho cảnh bỏ trống → đổi giây ra frame → ghi `build.json` | vài giây |
| `make video` | `build`, rồi render MP4 và ảnh bìa | ~5 phút (máy 6 nhân), ~34 phút (máy 2 nhân) |
| `make check` | Đếm frame trên chính MP4, so với `build.json`; trích một ảnh cho mỗi màn chữ | ~10 giây |
| `make export` | Gói lời đăng, lời Nhật–Việt, giọng đọc, ghi công vào `out/<ngày>/`. **Chỉ đọc**, không render lại (trừ ảnh bìa còn thiếu) | vài giây |

---

## Lệnh nào gộp bước nào

```
 new ──► build ──► render ──► check ──► export
         └─ make video ─┘
         └────────────── make release ─────────────┘
```

- `make video` = `build` + render. Nên không bao giờ phải gõ `make build` trước
  `make video`.
- `make release` = `video` + `check` + `export`. Render hỏng thì không kiểm,
  kiểm FAIL thì không gói — không đóng gói một video dở dang.

Chỉ **render** là đắt. Mọi bước khác đều mất vài giây, nên soát kỹ trước khi
render, đừng soát sau.

---

## Các cách đi

### A. Làm từ đầu, đi từng bước

Nên dùng lúc mới quen, hoặc khi muốn nhìn tận mắt từng file.

```bash
make new     DAY=2026-10-01          # rồi mở content/2026-10-01/script.json ra sửa
make reading DAY=2026-10-01          # romaji máy đọc có sai chữ nào không
make build   DAY=2026-10-01          # nghe mp3, xem build.json
make still   DAY=2026-10-01 FRAME=77 # xem thử ảnh bìa trước khi render cả video
make video   DAY=2026-10-01
make check   DAY=2026-10-01
make export  DAY=2026-10-01
```

### B. Gộp — thường ngày chỉ cần ba lệnh

```bash
make new     DAY=2026-10-01          # sửa script.json
make reading DAY=2026-10-01
make release DAY=2026-10-01          # = video + check + export
```

### C. Video đã render, chỉ sửa lời đăng — KHÔNG render lại

Lời đăng không hiện trên hình, nên không phải render lại gì cả.

```bash
make build  DAY=2026-10-01           # lời đăng mới vào build.json
make export DAY=2026-10-01           # gói lại, MP4 để nguyên
```

Sửa **câu trong video** thì khác: chữ và giọng đọc đều đổi, nên phải
`make release` lại.

### D. Nhiều ngày — soát chữ cả tháng TRƯỚC khi tốn CPU render

```bash
for d in 01 02 03 04 05; do make new DAY=2026-10-$d; done
                                     # sửa từng script.json, viết lời đăng
make build-all                       # soạn mọi ngày chưa có build.json (vài giây/ngày)
make export  MONTH=2026-10           # gói phần chữ ra, đọc lướt cả tháng
make release MONTH=2026-10           # rồi mới render — cả tháng ~2,5 giờ ở máy 6 nhân
```

Trong một lệnh `release` nhiều ngày, một ngày hỏng **không** chặn các ngày sau.
Cuối lệnh in ra ngày nào hỏng, rồi chạy lại riêng ngày đó bằng `DAY=`.

### E. Chỉ sửa font hay bố cục, chưa muốn render cả video

```bash
make still  DAY=2026-10-01 FRAME=300 # ra out/2026-10-01-f300.png
make studio DAY=2026-10-01           # hoặc tua trong Studio
```

---

## Chọn ngày

Mọi lệnh nhận `DAY=`. Riêng `export` và `release` nhận thêm cả khoảng ngày:

| Viết | Chọn |
|---|---|
| `DAY=2026-09-12` | đúng một ngày |
| `FROM=2026-09-12 TO=2026-09-30` | từ ngày tới ngày, **tính cả hai đầu** |
| `FROM=2026-09-12` | từ ngày đó tới ngày cuối cùng đang có |
| `TO=2026-09-30` | từ ngày đầu tiên tới ngày đó |
| `MONTH=2026-09` | cả tháng |

Muốn làm **mọi** ngày thì dùng lệnh đuôi `-all`, không cần tham số:

| Lệnh | Làm cho |
|---|---|
| `make build-all` | mọi ngày chưa có `build.json` |
| `make video-all` | mọi ngày chưa có MP4 |
| `make export-all` | mọi ngày đã có `build.json` |

---

## Tên lệnh — ba luật

```
 <việc>        một ngày hoặc một khoảng ngày         build, video, check, export, release
 <việc>-all    mọi ngày còn thiếu, không nhận ngày   build-all, video-all, export-all
 <sổ>-list     chỉ IN một cuốn sổ ra                 shots-list, bank-list
```

Tên lệnh là tên thành phẩm khi có thể: `build` ra `build.json`, `video` ra MP4.

Tên cũ vẫn chạy, nhưng in một dòng nhắc:

| Tên cũ | Tên mới |
|---|---|
| `make content` | `make build` |
| `make content-all` | `make build-all` |
| `make all` | `make video-all` |
| `make shots`, `make assets` | `make shots-list` |
| `make bank` | `make bank-list` |

---

## Clip, nhạc nền, ngân hàng kịch bản

| Lệnh | Làm gì |
|---|---|
| `make shots-list` | In sổ clip + nhạc nền (`library/shots.json`), kiểm file thật: có không, khổ hình, fps, thiếu giấy phép |
| `make shots-find Q="tea ceremony"` | Tìm clip trên Pexels/Pixabay (cần khoá API) |
| `make shots-get ID=… NAME=… TAGS=…` | Tải một clip rồi ghi sổ ngay, trong cùng một lệnh |
| `make shots-add FILE=… NAME=… URL=… AUTHOR=… LICENSE=…` | Ghi một file đã tải sẵn vào sổ — không cần khoá |
| `make bank-list` | In ngân hàng kịch bản viết sẵn (`library/bank.json`) |

Chi tiết: `docs/tai-san-can-tai.md`, `docs/kich-ban-va-kiem-tra.md`.

---

## Dọn dẹp — hai mức, vì hai thứ đắt khác hẳn nhau

| Lệnh | Xoá | Làm lại mất |
|---|---|---|
| `make clean` | nguyên liệu: `build.json`, `.cache.json`, mp3. **MP4 còn nguyên** | vài giây mỗi ngày (`make build-all`) |
| `make clean-all` | thêm cả `out/`: **mọi MP4**, ảnh bìa, gói đăng | ~5 phút mỗi ngày (`make video-all`) |

Không lệnh nào đụng tới kịch bản, nhạc nền, clip nền hay sổ clip.

---

## Đọc tiếp

| Tài liệu | Nói về |
|---|---|
| `docs/cai-dat.md` | Cài Python, Node, khoá API |
| `docs/kich-ban-va-kiem-tra.md` | `make new`, ngân hàng kịch bản, `make check` |
| `docs/dang-bai.md` | Lời đăng, `make export`, gói đăng, thời gian render |
| `docs/caption-va-cau-dai.md` | Caption trên hình, cỡ chữ, câu dài chia mảnh |
| `docs/mo-dau-va-ket.md` | Tiêu đề ngày, màn kết, ảnh bìa, chuyển cảnh |
| `docs/tai-san-can-tai.md` | Clip nền, nhạc nền, sổ clip |
| `CLAUDE.md` | Kiến trúc, nguyên tắc, quy ước cho người sửa code |
