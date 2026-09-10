# Cài đặt

Ba việc, theo thứ tự. Việc thứ ba có thể bỏ qua.

---

## 1. Cài phụ thuộc

```bash
make setup
```

Nó in ra **đúng Python nào đang được cài vào** trước khi cài:

```
Cài vào: /opt/conda/bin/python3
```

Đọc dòng đó. Máy này có hai Python — conda base (dòng lệnh có `(base)` ở đầu)
và python của codespace. `pip install` trần trỏ vào cái nào là tuỳ `PATH`, nên
rất dễ cài xong một chỗ rồi `make` chạy ở chỗ kia và báo thiếu thư viện. Đó
chính là lỗi đã xảy ra một lần rồi. `make setup` dùng `python3 -m pip`, tức
luôn đúng trình thông dịch mà Makefile sẽ gọi.

**Đừng bao giờ gõ `pip install` trần trong dự án này.**

Nếu vẫn thấy báo thiếu thư viện, thông báo lỗi sẽ in kèm đường dẫn Python đang
chạy — so nó với dòng `Cài vào:` ở trên, lệch nhau là biết ngay vấn đề.

Ngoài Python còn cần **ffmpeg** (`ffprobe` đo độ dài mọi file media) và
**Node 18 trở lên** (Remotion). `make setup` tự chạy `npm ci` trong `studio/` —
thiếu bước này thì `make studio` báo `npm error could not determine executable
to run`.

### Node trên WSL: phải là bản Linux

`node_modules` chứa binary riêng cho từng hệ điều hành (esbuild, compositor của
Remotion). Repo nằm trên ổ Windows mà `make` chạy trong WSL thì Node cũng phải
là bản Linux cài trong WSL. WSL mặc định chép `PATH` của Windows vào, nên nếu
WSL chưa có Node thì `npm` sẽ trỏ sang `/mnt/c/.../npm` — cài bằng nó là ra
binary win32 và render chết. `make setup` in dòng `npm:` và từ chối chạy khi
đường dẫn bắt đầu bằng `/mnt/`.

Cài Node bản Linux bằng một trong hai cách, trong terminal WSL. Đang dùng env
conda cho Python thì cách đầu gọn hơn — Node nằm luôn trong env đó:

```bash
# Cách 1: vào env conda của dự án
conda install -n vidgenkit -c conda-forge nodejs
conda activate vidgenkit

# Cách 2: nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
exec $SHELL          # nạp lại shell để có lệnh nvm
nvm install --lts
```

Rồi kiểm và cài:

```bash
command -v npm       # phải ra /home/..., không phải /mnt/c/...
make setup
```

Theo cách 1 thì Node chỉ có khi env đang bật — quên `conda activate` là `npm`
lại rơi về bản Windows, và `make setup` sẽ chặn lại.

Lỡ `npm install` từ Windows rồi thì xoá `studio/node_modules` và chạy lại
`make setup` trong WSL.

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
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/ | tốn tiền theo lượt gọi | `make new` nhờ Claude viết kịch bản. **Điền vào là bật** — xem [kich-ban-va-kiem-tra.md](kich-ban-va-kiem-tra.md) |

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
make content DAY=2026-08-20      # 1427 frame thoại, tổng 1652
make video   DAY=2026-08-20      # ~10 phút trên máy 2 nhân
make check   DAY=2026-08-20      # phải PASS, đếm frame trên chính MP4
make bank                        # ngân hàng kịch bản, không cần khoá
```

Con số **1427 frame thoại** là mốc hồi quy. Nó đổi mà bạn không cố ý đổi nhịp
đọc thì có thứ gì đó vừa hỏng.
