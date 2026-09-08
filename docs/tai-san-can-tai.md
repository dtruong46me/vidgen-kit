# Nhạc nền và clip nền

Chọn nhạc và chọn cảnh là chuyện thẩm mỹ, code không quyết hộ được. Tài liệu này
ghi lại khi cần thêm thì tải ở đâu, lưu thế nào.

**Đang có gì thì hỏi máy, đừng hỏi tài liệu.** `make shots` in ra cả sổ kèm số
đo thật, ai đang dùng, và chỗ nào còn thiếu thông tin. Bảng chép tay trong tài
liệu chỉ chờ ngày lệch với thư mục thật, nên nó đã bị bỏ đi.

---

## Sổ tài sản

Mỗi file trong `studio/public/` phải có đúng một dòng trong `library/shots.json`.
Sổ giữ những thứ **không đo được**: nguồn, tác giả, giấy phép, tag. Những thứ
đo được — độ dài, bề ngang, fps — thì ffprobe đo lúc chạy `make shots`, không
chép vào sổ, vì số chép tay chỉ chờ ngày lệch với file thật.

```
$ make shots

CLIP NỀN  (3 dòng)
  [!! ] tea-room       1080×1920, 25fps, 22.9s
          video/tea-room.mp4   tags: tea, interior, tatami, scroll, wide, calm, morning
          pexels: tác giả chưa rõ — https://www.pexels.com/video/8508048/
          dùng cho: 2026-08-20
          [!] 25fps ≠ 30fps của video đích
          [!] chưa ghi tác giả
```

Đây là **báo cáo, không phải cổng chặn** — thiếu thông tin thì video vẫn dựng
được, chỉ là bạn đang tích nợ. Cổng chặn thật sự là `make check` ở BƯỚC 6.

`tags` là thứ duy nhất nên sửa tay trong sổ. Chúng quyết định bộ chọn clip lấy
cảnh nào cho câu nào, nên cứ gắn rộng tay: `tea`, `hands`, `closeup`, `calm`,
`morning`. Câu nào trong kịch bản khai `"tags": ["matcha"]` thì chỉ những clip
mang tag đó mới được chọn.

---

## Thêm clip mới

### Có khoá API

Điền `PEXELS_API_KEY` vào `.env` trước — xem [cai-dat.md](cai-dat.md).

```bash
make shots-find SOURCE=pexels Q="tea ceremony"
make shots-get  SOURCE=pexels ID=8507912 NAME=matcha-whisk TAGS=tea,matcha,closeup
```

`shots-find` đã lọc sẵn hướng dọc và đánh dấu `!` vào clip không đạt chuẩn.
`shots-get` tải file, đặt vào `studio/public/video/<NAME>.mp4`, ghi sổ kèm tác
giả và giấy phép lấy thẳng từ API, rồi đo lại bằng ffprobe và cảnh báo nếu clip
nằm ngang hoặc sai fps. Một lệnh, không có bước nào để quên.

### Không có khoá API

Tải bằng trình duyệt như bình thường, rồi:

```bash
make shots-add FILE=~/Downloads/8507912.mp4 NAME=matcha-whisk \
               URL=https://www.pexels.com/video/8507912/ \
               AUTHOR="Tên tác giả" LICENSE="Pexels License" \
               TAGS=tea,matcha,closeup
```

`URL`, `AUTHOR` và `LICENSE` là **bắt buộc**. Không phải để hành: sáu tháng nữa
không ai nhớ clip ở đâu ra, mà YouTube thì có nhớ.

### Nhạc nền

Chưa có lệnh tự động — lưu tay vào `studio/public/audio/bgm-<tên>.mp3`, thêm một
dòng vào ngăn `music` của `library/shots.json`, rồi trỏ trường `bgm` của kịch
bản vào đó.

---

## Tìm ở đâu, chọn thế nào

### Nhạc nền

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

Đặt `NAME` theo nội dung cảnh quay chứ đừng theo số thứ tự — cùng một clip
thường dùng cho nhiều cảnh, nên `scene-01` là cái tên sai ngay từ hôm sau.

| | |
|---|---|
| Hướng | **DỌC**. Đây là điều quan trọng nhất |
| Kích thước | ≥ 1080×1920 |
| Định dạng | MP4, mã hoá H.264 |
| Khung hình | **30fps**. Ba clip đang có đều 25fps, nên cảnh lia chậm hơi giật — `make shots` cảnh báo chỗ này |
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
gây nhiễu. Cắt xong thì `make shots-add` file đã cắt, và ghi vào ô `URL` link
của clip GỐC — đó mới là thứ giấy phép bám vào.

Ép luôn về 30fps thì thêm `-r 30` vào cùng lệnh trên.

---

## Gán clip vào cảnh

**Cách thường dùng: đừng gán gì cả.** Bỏ trống trường `clip` thì `shots.py` tự
chọn, và nó chọn tốt hơn tay người vì nó biết chính xác mỗi cảnh dài bao nhiêu
giây — con số đó chỉ có sau khi TTS chạy xong, tức là sau lúc bạn viết kịch bản.

```json
{
  "tags": ["tea", "calm"],
  "lines": [
    { "ja": "毎日の生活は、…", "vi": "…" },
    { "ja": "美味しいご飯を…", "vi": "…", "tags": ["matcha"] }
  ]
}
```

`tags` ở cấp kịch bản là gợi ý mặc định cho mọi câu; `tags` ở cấp câu đè lên nó.
Không clip nào mang tag đang tìm thì bộ chọn rơi về cả thư viện và nói ra.

Bộ chọn chạy theo bốn quy tắc, ưu tiên từ trên xuống: đủ dài (kèm biên an toàn
0,25 giây) → đúng tag → không trùng clip của cảnh ngay trước → ưu tiên đoạn hình
chưa dùng → clip nào dùng ít nhất thì đến lượt. Không có random: cùng kịch bản
và cùng thư viện thì luôn ra cùng kết quả.

**Muốn tự chọn thì cứ ghi ra, máy không đụng vào:**

```json
{ "ja": "…", "clip": "video/matcha-whisk.mp4", "clipStartInSeconds": 5.5 }
```

Cảnh nào clip không đủ dài thì Remotion cho chạy lặp, và `make content` nói ra
ngay trên màn hình. Bỏ trống `clip` khi sổ chưa có clip nào dùng được thì cảnh
đó dùng nền gradient tông trầm — không lỗi, chỉ nhạt hơn.
