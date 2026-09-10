# Màn mở đầu, màn kết, chuyển cảnh

Cả ba đều **tắt hoặc trung tính theo mặc định**. Kịch bản không khai gì thì video
ra đúng như trước BƯỚC 5, không lệch một frame nào.

---

## Tiêu đề ngày — không còn màn mở đầu riêng

```json
{
  "intro": { "title": "小さな幸せ", "pauseSeconds": 1.5 }
}
```

Video **vào thẳng cảnh 1 ở frame 0**, không còn cảnh nền gradient nào đứng
trước. Tiêu đề hiện đè lên chính cảnh 1:

- **Chữ to: ngày tháng** — `8月20日`, tâm đặt ở **1/4 khung hình từ trên xuống**.
- **Chữ nhỏ bên dưới: chủ đề** — `小さな幸せ`, hiện sau ngày 14 frame.
- Cảnh 1 **lặng `pauseSeconds`** rồi mới đọc câu 1 (`今日は、8月20日です。おはようございます。`).
  Caption câu 1 cũng chờ bấy nhiêu, để tiêu đề và caption không hiện cùng lúc.
- Tiêu đề mờ đi đúng lúc cảnh 2 chồng vào.

| Trường | Bỏ trống thì | Ghi chú |
|---|---|---|
| `title` | lấy `title` của cả kịch bản | Chủ đề, dòng nhỏ dưới ngày |
| `pauseSeconds` | 1,5 | Tiêu đề vào trong 34 frame (~1,1 giây); ngắn hơn thế thì tiếng đọc chen vào lúc chữ còn đang hiện. Dưới 1,5 thì ảnh bìa bắt chủ đề đang hiện dở |

Không khai `intro` thì không có tiêu đề, và cảnh 1 cũng không lặng thêm.

**Ngày do máy sinh, đừng gõ tay.** Nó suy từ tên file kịch bản: `2026-08-20.json`
ra `8月20日` — viết đúng như trong câu đọc, để chữ trên màn hình và tiếng đọc là
cùng một thứ. Tên kịch bản không phải dạng ngày (`thu-nghiem.json`) thì chủ đề
lên làm chữ to, không có dòng nhỏ. Không lỗi.

Kịch bản cũ còn `"seconds"` trong `intro` thì `make content` dừng lại và bảo đổi
thành `pauseSeconds` — trường cũ là độ dài của cảnh gradient, giữ im lặng mà bỏ
qua thì người sửa số đó sẽ không hiểu vì sao video không đổi.

### Hợp đồng

`build.json` có trường `titleCard: {"title", "subtitle"}`, và mỗi câu có
`captionStartInFrames` (0 ở mọi cảnh trừ cảnh 1). Trường `intro` **vẫn còn nhưng
luôn là `null`** — Remotion bản cũ cộng `intro.durationInFrames` vào tổng, null
tức 0, nên nó vẫn đếm đúng tổng frame (P-3). Tổng giờ là **các cảnh + màn kết**.

### Sóng giọng đọc

Ngay trên dòng ngày là một hàng vạch nhỏ nhảy theo giọng đang đọc — người xem
tắt tiếng vẫn biết video đang có lời. Nó đọc từ chính file giọng của từng câu,
không phải nhạc nền, nên chỉ động khi có người nói; nghỉ giữa câu thì phẳng
thành một hàng chấm.

- Chạy suốt các cảnh ở cùng một chỗ, kể cả sau khi tiêu đề đã tắt.
- Hiện dần cùng tiêu đề ở đầu video, tắt đi trước màn kết. Ảnh bìa bắt nó ở
  dạng hàng chấm, vì lúc đó chưa có tiếng.
- Neo vào `TITLE_CENTER` của `TitleCard.tsx`: dời tiêu đề là sóng đi theo.
- Không có trường nào trong hợp đồng — `audio`, `audioStartInFrames` đã đủ.
  Dùng `useAudioData` + `visualizeAudio` của `@remotion/media-utils`, gói này
  phải cùng bản với `remotion` (hiện 4.0.513).

Sóng cao thấp theo `GAIN` trong `VoiceWave.tsx`: giọng nói bình thường nên lên
chừng 2/3 chiều cao, chừa chỗ cho chỗ nhấn giọng.

### Ảnh bìa

```bash
make thumbnail DAY=2026-08-20    # out/2026-08-20-thumbnail.png
```

Chụp đúng frame caption câu 1 bắt đầu vào — `thumbnailFrame` trong build.json,
mặc định 45. Ở frame đó ngày và chủ đề đã hiện đủ (chủ đề vào xong ở frame 44),
caption còn trong suốt, và chưa có tiếng đọc. Frame do `timeline.py` chọn,
`render.py` chỉ đọc số đó (P-2).

Như `make still`, lệnh này chỉ vẽ từ build.json đã có. `make video` thì dựng
luôn ảnh bìa ngay sau MP4, nên ngày thường không phải gọi riêng.

### Chữ

Font **Yuji Syuku** — nét bút lông. Nó chỉ dùng cho tiêu đề và màn kết, không
dùng cho caption: nét mảnh và không đều, đọc lâu thì mỏi mắt, mà caption thì
người xem phải đọc kịp trong vài giây.

Lớp phủ tối của `Background.tsx` cố tình nhạt ở dải trên để khán giả xem hình,
nên tiêu đề tự mang một quầng tối nhỏ sau chữ, hiện và tắt cùng chữ. Cỡ chữ tính
theo bề ngang ước lượng (chữ số chỉ chiếm nửa ô), nên mọi ngày trong năm — từ
`1月1日` tới `12月31日` — đều cùng một cỡ.

## Màn kết

```json
{
  "outro": { "text": "またあした", "seconds": 3.0 }
}
```

Ngắn có chủ ý. Người xem đã nhận được thứ họ đến để nhận; kéo dài
phần kết chỉ tạo cơ hội cho họ lướt đi trước khi video hết, mà lướt đi sớm thì
thuật toán hiểu là video dở.

Nền tối dần về đen tuyệt đối ở frame cuối. Video kết thúc bằng màn hình đen chứ
không phải bằng một khung hình đứng — khác biệt nhỏ nhưng là khác biệt giữa
"hết rồi" và "đơ máy".

---

## Chuyển cảnh

```json
{
  "transition": "crossfade",
  "transitionSeconds": 0.8
}
```

| Kiểu | Cảnh sau bắt đầu ở đâu | Cảm giác |
|---|---|---|
| `crossfade` | sớm hơn T frame, chồng lên cuối cảnh trước | Êm nhất. **Mặc định** |
| `dip_to_black` | đúng ô của nó; sáng lên trong T/2, tối đi trong T/2 | Có một khoảnh khắc đen thật giữa hai cảnh — dứt khoát hơn |
| `cut` | đúng ô của nó, không hiệu ứng | Cắt thẳng. Hợp với kịch bản nhịp nhanh |

`transitionSeconds` mặc định 0,8 giây = 24 frame ở 30fps — đúng bằng hằng số
`CROSSFADE` mà Remotion vẫn dùng từ trước BƯỚC 5.

> Ba số hiệu ứng phải đi cùng nhau: chữ hiện 26 frame, tắt 20 frame, nền mờ
> chồng 24 frame. Kéo `transitionSeconds` lên 2 giây mà không đụng hai số kia
> thì nền đổi xong từ lâu chữ mới trôi tới — hai lớp lệch nhịp.

---

## Dòng hiragana

```json
{ "showHira": true }
```

**Mặc định tắt, và nên để tắt.** Trường `hira` đã có trong build.json từ BƯỚC 3,
đây chỉ là công tắc hiện nó ra.

Lý do để tắt, cả hai đều nhìn thấy được khi bật lên xem:

1. Caption thành **bốn dòng**. Khối chữ cao thêm khoảng 60px và lấn dần vào
   vùng an toàn 380px mà TikTok che mất.
2. Câu nào vốn đã toàn kana — như `おはようございます。` — thì `hira` **giống hệt**
   dòng tiếng Nhật, in ra là lặp nguyên một dòng.

Vấn đề thứ hai đã sửa bằng code: câu như vậy tự ẩn dòng hiragana. Vấn đề thứ
nhất thì không sửa được bằng code, phải chọn.

Bật lên xem rồi tự quyết — đừng quyết bằng cách tưởng tượng:

```bash
# thêm "showHira": true vào kịch bản
make content DAY=2026-08-20 && make still DAY=2026-08-20 FRAME=320
```
