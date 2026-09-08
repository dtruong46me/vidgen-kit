# Tài sản cần tải về tay

Hai khiếm khuyết D-1 và D-2 (xem `CLAUDE.md`) không sửa được bằng code, vì chọn
nhạc và chọn cảnh là chuyện thẩm mỹ. Tài liệu này liệt kê đúng những gì cần tải,
tải ở đâu, và lưu vào đâu.

Tải xong, chạy `make assets` để máy tự kiểm tra giúp.

---

## 1. Nhạc nền — 1 file

**Vấn đề hiện tại:** `studio/public/audio/bgm.mp3` đang là file test tone tải từ
samplelib.com. Nó trùng md5 với `assets/audio/sample.mp3`. Dài 19,2 giây nên bị
lặp 2,3 lần dưới một video 48,7 giây — nghe rõ chỗ nối.

**Lưu thành:** `studio/public/audio/bgm.mp3` (ghi đè file cũ)

**Yêu cầu:**

| | |
|---|---|
| Độ dài | ≥ 60 giây, để không phải lặp trong 1 video |
| Định dạng | MP3 |
| Thể loại | lo-fi, ambient, piano, koto — không lời, không trống mạnh |
| Giấy phép | phải cho dùng thương mại và **không bắt ghi công** |

**Nên lấy ở đâu:** [Pixabay Music](https://pixabay.com/music/) — giấy phép
Pixabay Content License, dùng thương mại được, không bắt ghi công, YouTube không
đánh gậy bản quyền. Đây là chỗ ít rắc rối nhất.

- [Tìm "lofi"](https://pixabay.com/music/search/lofi/)
- [Tìm "ambient"](https://pixabay.com/music/search/ambient/)
- [Tìm "japanese"](https://pixabay.com/music/search/japanese/)

Chỗ khác cũng được nhưng phải đọc kỹ giấy phép:

- [Free Music Archive](https://freemusicarchive.org/) — giấy phép trộn lẫn,
  có bài CC-BY bắt ghi công, có bài cấm dùng thương mại. Phải xem từng bài.
- [Incompetech](https://incompetech.com/music/royalty-free/music.html) —
  Kevin MacLeod, tất cả là CC-BY, tức **bắt buộc ghi công** trong mô tả video.

> Âm lượng nhạc nền đang để 0.12 (`bgmVolume` trong `content/<ngày>.json`).
> Nhạc thật thường to hơn test tone, nghe thử rồi chỉnh số đó nếu nhạc át lời.

---

## 2. Clip nền — 2 đến 3 file

**Vấn đề hiện tại:** `scene-01.mp4` và `scene-07.mp4` là cùng một file — video
hoa mẫu CC0 của MDN, **960×540 nằm ngang**, dài 5,055 giây. Khung dọc 1080×1920
phải phóng nó lên khoảng 3,6 lần mới lấp đầy, nên mờ nhoè. Bảy cảnh còn lại không
có clip, đang rơi về nền gradient.

**Lưu thành:** `studio/public/video/scene-01.mp4` … `scene-09.mp4`

Kịch bản `2026-08-20` gọi tên `scene-01` đến `scene-09`. Thiếu file nào thì cảnh
đó tự động dùng nền gradient — **không lỗi, chỉ là nhạt hơn**. Nên bước này chỉ
cần 2–3 clip đẹp là đã đủ thấy khác biệt; không cần đủ 9.

**Yêu cầu:**

| | |
|---|---|
| Hướng | **DỌC** (portrait). Đây là điều quan trọng nhất |
| Kích thước | ≥ 1080×1920 |
| Định dạng | MP4, mã hoá H.264 |
| Độ dài | 8–15 giây (cảnh dài nhất hiện là 9,4 giây) |
| Chuyển động | chậm, ít — mây trôi, nước chảy, lá rung, hơi trà bốc |
| Tránh | mặt người nhìn thẳng, chữ cháy sẵn trong hình, cắt cảnh giật |

**Nên lấy ở đâu:**

- [Pexels Videos](https://www.pexels.com/videos/) — bấm bộ lọc
  **Orientation → Vertical**. Giấy phép Pexels, không bắt ghi công.
  Từ khoá gợi ý: [japanese garden](https://www.pexels.com/search/videos/japanese%20garden/),
  [tea](https://www.pexels.com/search/videos/tea/),
  [bamboo](https://www.pexels.com/search/videos/bamboo/),
  [rain window](https://www.pexels.com/search/videos/rain%20window/),
  [morning light](https://www.pexels.com/search/videos/morning%20light/)
- [Pixabay Videos](https://pixabay.com/videos/) — cũng có bộ lọc dọc.
- [Coverr](https://coverr.co/) và [Mixkit](https://mixkit.co/free-stock-video/) —
  ít clip hơn nhưng chất lượng đồng đều.

> **Ghi lại đường link chỗ bạn tải.** BƯỚC 4 sẽ dựng `library/shots.json` để lưu
> nguồn và giấy phép của từng clip. Chép sẵn link vào một file nháp bây giờ sẽ đỡ
> phải đi tìm lại sau.

---

## 3. Nếu clip tải về nằm ngang

Vẫn dùng được, cắt về dọc bằng ffmpeg — lấy dải giữa khung:

```bash
ffmpeg -i clip-goc.mp4 \
  -vf "crop=ih*9/16:ih,scale=1080:1920" \
  -an -c:v libx264 -crf 20 \
  studio/public/video/scene-02.mp4
```

`-an` bỏ tiếng của clip: video này chỉ dùng giọng đọc và nhạc nền, tiếng gốc của
clip chỉ gây nhiễu.

---

## 4. Kiểm tra lại

```bash
make assets                      # liệt kê file nào còn thiếu hoặc còn là hàng mẫu
make video DAY=2026-08-20        # dựng lại và xem
```
