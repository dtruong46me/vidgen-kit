# Cài đặt

Ba việc, theo thứ tự. Việc thứ ba có thể bỏ qua.

---

## 1. Cài phụ thuộc

```bash
make setup
```

Nó cài phụ thuộc Python **và** phụ thuộc Node của `studio/`, và in ra đường dẫn
thật của cả hai trước khi cài:

```
Python:  /opt/conda/bin/python3
Node:    /home/ban/.nvm/versions/node/v22.14.0/bin/node
npm:     /home/ban/.nvm/versions/node/v22.14.0/bin/npm
```

Đọc ba dòng đó. Cả hai bên đều có cùng một cái bẫy: **lệnh chạy được không có
nghĩa là nó thuộc môi trường bạn tưởng.**

Phía Python, máy này có hai bản — conda base (dòng lệnh có `(base)` hoặc
`(vidgenkit)` ở đầu) và python của hệ thống. `pip install` trần trỏ vào cái nào
là tuỳ `PATH`, nên rất dễ cài xong một chỗ rồi `make` chạy ở chỗ kia và báo
thiếu thư viện. Đó chính là lỗi đã xảy ra một lần rồi. `make setup` dùng
`python3 -m pip`, tức luôn đúng trình thông dịch mà Makefile sẽ gọi.

**Đừng bao giờ gõ `pip install` trần trong dự án này.**

Nếu vẫn thấy báo thiếu thư viện, thông báo lỗi sẽ in kèm đường dẫn Python đang
chạy — so nó với dòng `Python:` ở trên, lệch nhau là biết ngay vấn đề.

---

### Node trong WSL: đừng mượn bản Windows

Phía Node, bẫy nặng hơn. WSL nối `PATH` của Windows vào cuối `PATH` của nó, nên
nếu máy Windows đã cài Node thì trong WSL bạn thấy thế này:

```
npm  -> /mnt/c/Program Files/nodejs/npm     ← bản Windows
node -> không có
```

`npm` gọi được nên trông như đã cài xong, nhưng đây là Node của Windows nhìn
xuyên qua ranh giới. Cài bằng nó thì Remotion tải **Chrome Headless Shell và
esbuild bản win32** về `studio/node_modules`, rồi lỗi mới nổ ra lúc render —
xa chỗ sai thật. `make setup` chặn hẳn trường hợp này chứ không cài tiếp.

Cách sửa là cài Node **bản Linux** vào trong WSL:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install --lts
```

Kiểm lại — `which node` phải ra đường dẫn trong `~/.nvm`, không phải `/mnt/...`:

```bash
which node npm && node -v
```

Remotion 4.0.5 cần **Node 18 trở lên**; `make setup` cũng kiểm con số đó.

---

### ffmpeg

`ffprobe` đo độ dài mọi file media, và theo P-1 thì độ dài đó quyết định toàn bộ
timeline — thiếu nó là không dựng được gì. Nó phải nằm **cùng phía** với `make`:
cài bên Windows mà chạy `make` trong WSL thì WSL không thấy.

```bash
sudo apt update && sudo apt install -y ffmpeg   # trong WSL / Ubuntu
```

Không muốn dùng `sudo` thì cài thẳng vào conda env đang bật:

```bash
conda install -c conda-forge ffmpeg
```

Đừng trỏ `PATH` của WSL sang `ffprobe.exe` bên Windows. Nó chạy được, nhưng mỗi
câu thoại gọi một lần qua ranh giới WSL↔Windows kèm dịch đường dẫn `/mnt/...`,
chậm thấy rõ.

Codespace đã có sẵn cả ffmpeg lẫn Node, không phải làm bước này.

---

## 2. File `.env`

`make setup` tự chép `.env.example` thành `.env` nếu chưa có. Đã có `.env` rồi
thì nó **không đè** — khoá bạn điền không bị mất.

`.env` nằm trong `.gitignore` nên không bao giờ lên git. `.env.example` mới là
file được commit, và nó chỉ chứa tên biến rỗng.

Biến môi trường thật luôn thắng file, nên chạy một lần với khoá khác vẫn được:

```bash
PEXELS_API_KEY=... make shots-find Q="bamboo"
```

---

## 3. Khoá API — có thể bỏ qua

**Không có khoá nào thì mọi lệnh dựng video vẫn chạy đủ.** `make content`,
`make video`, `make still`, `make reading`, `make shots` đều không gọi mạng
ngoài edge-tts. Khoá chỉ để **tìm và tải clip tự động**.

| Biến | Lấy ở đâu | Mất bao lâu | Dùng cho |
|---|---|---|---|
| `PEXELS_API_KEY` | https://www.pexels.com/api/ | ~2 phút, không cần thẻ | `make shots-find` / `shots-get` với `SOURCE=pexels` |
| `PIXABAY_API_KEY` | https://pixabay.com/api/docs/ | ~2 phút, cần tài khoản | `SOURCE=pixabay` |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/ | tốn tiền theo lượt gọi | BƯỚC 6, chưa dùng tới |

Điền vào `.env`:

```
PEXELS_API_KEY=abc123...
```

Kiểm tra ngay:

```bash
make shots-find SOURCE=pexels Q="tea ceremony"
```

Chưa điền thì lệnh đó nói thẳng thiếu gì và điền vào đâu, không phải traceback.

### Không muốn lấy khoá thì làm sao

Tải bằng trình duyệt như bình thường, rồi nhập vào thư viện bằng một lệnh:

```bash
make shots-add FILE=~/Downloads/8507912.mp4 NAME=matcha-whisk \
               URL=https://www.pexels.com/video/8507912/ \
               AUTHOR="Tên tác giả" LICENSE="Pexels License" \
               TAGS=tea,matcha,closeup
```

Đường này làm được mọi thứ đường API làm, chỉ là bạn tự tìm clip. Xem
[tai-san-can-tai.md](tai-san-can-tai.md) để biết tìm ở đâu và chọn thế nào.

---

## Kiểm tra cả bộ

```bash
make reading DAY=2026-08-20      # romaji + hiragana, không cần khoá
make shots                       # sổ tài sản
make content DAY=2026-08-20      # phải ra đúng 1462 frame
make video   DAY=2026-08-20      # ~10 phút trên máy 2 nhân
```

Con số **1462 frame** là mốc hồi quy. Nó đổi mà bạn không cố ý đổi nhịp đọc thì
có thứ gì đó vừa hỏng.
