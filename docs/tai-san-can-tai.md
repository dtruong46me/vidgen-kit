# Nhạc nền và clip nền

Chọn nhạc và chọn cảnh là chuyện thẩm mỹ, code không quyết hộ được. Tài liệu này
ghi lại đang có gì, và khi cần thêm thì tải ở đâu, lưu thế nào.

Chạy `make assets` bất cứ lúc nào để máy soi lại.

---

## Đang có gì

**Nhạc nền** — `studio/public/audio/`

| File | Dài | Đang dùng cho |
|---|---|---|
| `bgm-lonely-self.mp3` | 150 s | `2026-08-20` |
| `bgm-lofi-piano.mp3` | 223 s | (chưa dùng) |

Cả hai đều dài hơn video 48,7 giây nên không phải lặp lần nào. Đổi bản nhạc bằng
cách sửa trường `bgm` trong `content/<ngày>.json` — một dòng, không đụng code.

**Clip nền** — `studio/public/video/`, cả ba đều 1080×1920, H.264

| File | Dài | Nội dung |
|---|---|---|
| `tea-room.mp4` | 22,9 s | Toàn cảnh phòng trà, tranh cuộn, chiếu tatami |
| `matcha-whisk.mp4` | 12,8 s | Cận cảnh tay đánh matcha, nhìn từ trên xuống |
| `tea-tray.mp4` | 12,9 s | Hai người chuyền khay trà, nền đỏ ấm |

Ba clip cộng lại 48,6 giây, mà chín cảnh cũng đúng 48,6 giây — không thể xếp kín
mà không dùng lại. Nên mỗi clip được cắt ở 2–3 điểm khác nhau qua trường
`clipStartInSeconds`. Cách xếp hiện tại không cảnh nào phải loop.

> **Chưa ghi nguồn và giấy phép.** Ba clip trông như tải từ Pexels (tên file gốc
> có dạng `8507912-hd_1080_1920_25fps.mp4`). BƯỚC 4 sẽ dựng `library/shots.json`
> để lưu link gốc và giấy phép từng clip. Nếu bạn còn nhớ link, chép ra một chỗ
> ngay bây giờ sẽ đỡ phải đi tìm lại.

---

## Khi cần thêm

### Nhạc nền

Lưu vào `studio/public/audio/bgm-<tên-gợi-nhớ>.mp3`, rồi trỏ trường `bgm` của
kịch bản vào đó.

| | |
|---|---|
| Độ dài | ≥ 60 giây, để không phải lặp trong 1 video |
| Thể loại | lo-fi, ambient, piano, koto — không lời, không trống mạnh |
| Giấy phép | phải cho dùng thương mại và **không bắt ghi công** |

[Pixabay Music](https://pixabay.com/music/) là chỗ ít rắc rối nhất: dùng thương
mại được, không bắt ghi công, YouTube không đánh gậy.
[lofi](https://pixabay.com/music/search/lofi/) ·
[ambient](https://pixabay.com/music/search/ambient/) ·
[japanese](https://pixabay.com/music/search/japanese/)

Chỗ khác phải đọc kỹ giấy phép: [Free Music Archive](https://freemusicarchive.org/)
trộn lẫn nhiều loại; [Incompetech](https://incompetech.com/music/royalty-free/music.html)
toàn bộ là CC-BY, tức **bắt buộc ghi công** trong mô tả video.

> Âm lượng để ở `bgmVolume` trong kịch bản, hiện là 0.12. Nghe thử bản render;
> nhạc át lời thì hạ xuống 0.08, nhạc chìm quá thì nâng lên 0.16.

### Clip nền

Lưu vào `studio/public/video/<tên-theo-nội-dung>.mp4`. Đặt tên theo cảnh quay
chứ đừng theo số thứ tự — cùng một clip thường dùng cho nhiều cảnh.

| | |
|---|---|
| Hướng | **DỌC**. Đây là điều quan trọng nhất |
| Kích thước | ≥ 1080×1920 |
| Định dạng | MP4, mã hoá H.264 |
| Độ dài | càng dài càng đỡ phải dùng lại; 20 giây là thoải mái |
| Chuyển động | chậm, ít — mây trôi, nước chảy, lá rung, hơi trà bốc |
| Tránh | mặt người nhìn thẳng, chữ cháy sẵn trong hình, cắt cảnh giật |

[Pexels Videos](https://www.pexels.com/videos/) — lọc **Orientation → Vertical**.
[japanese garden](https://www.pexels.com/search/videos/japanese%20garden/) ·
[tea](https://www.pexels.com/search/videos/tea/) ·
[bamboo](https://www.pexels.com/search/videos/bamboo/) ·
[rain window](https://www.pexels.com/search/videos/rain%20window/)

Còn có [Pixabay Videos](https://pixabay.com/videos/), [Coverr](https://coverr.co/)
và [Mixkit](https://mixkit.co/free-stock-video/).

### Nếu clip tải về nằm ngang

Cắt về dọc bằng ffmpeg, lấy dải giữa khung:

```bash
ffmpeg -i clip-goc.mp4 \
  -vf "crop=ih*9/16:ih,scale=1080:1920" \
  -an -c:v libx264 -crf 20 \
  studio/public/video/ten-moi.mp4
```

`-an` bỏ tiếng của clip: video này chỉ dùng giọng đọc và nhạc nền, tiếng gốc chỉ
gây nhiễu.

---

## Gán clip vào cảnh

Trong `content/<ngày>.json`, mỗi câu có hai trường:

```json
{
  "ja": "毎日の生活は、…",
  "clip": "video/matcha-whisk.mp4",
  "clipStartInSeconds": 0
}
```

Cắt từ giây thứ mấy là do bạn chọn. `make content` sẽ tự đo phần còn lại sau
điểm cắt; nếu không đủ dài cho cảnh thì Remotion cho clip chạy lặp. Muốn biết
cảnh nào đang phải lặp thì xem `clipDurationInFrames` trong file build.json —
nhỏ hơn `durationInFrames` là đang lặp.

Bỏ trống `clip` (hoặc trỏ vào file không tồn tại) thì cảnh đó dùng nền gradient
tông trầm. Không lỗi, chỉ nhạt hơn.
