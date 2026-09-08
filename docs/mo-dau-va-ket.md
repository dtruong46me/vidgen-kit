# Màn mở đầu, màn kết, chuyển cảnh

Cả ba đều **tắt hoặc trung tính theo mặc định**. Kịch bản không khai gì thì video
ra đúng như trước BƯỚC 5, không lệch một frame nào.

---

## Màn mở đầu

```json
{
  "intro": { "title": "小さな幸せ", "seconds": 4.5 }
}
```

| Trường | Bỏ trống thì | Ghi chú |
|---|---|---|
| `title` | lấy `title` của cả kịch bản | Nên đặt riêng: `title` thường có cả ngày tháng, mà số Ả Rập lọt vào giữa hàng chữ thư pháp là gãy hẳn mạch |
| `seconds` | 4,5 | Dưới 3 giây thì chữ chưa kịp hiện xong đã tắt |

**Dòng ngày do máy sinh, đừng gõ tay.** Nó suy từ tên file kịch bản:
`2026-08-20.json` ra `八月二十日　木曜日`. Thứ trong tuần cũng tính từ chính ngày
đó. Gõ tay thứ mấy là kiểu sai không ai soi lại được — sai rồi thì phải tự nhớ
mới phát hiện, mà chẳng ai nhớ.

Tên kịch bản không phải dạng ngày (`thu-nghiem.json`) thì màn mở đầu chỉ có tiêu
đề, không có dòng ngày. Không lỗi.

Chữ dùng font **Yuji Syuku** — nét bút lông. Nó chỉ dùng ở đây và ở màn kết,
không dùng cho caption: nét mảnh và không đều, đọc lâu thì mỏi mắt, mà caption
thì người xem phải đọc kịp trong vài giây.

## Màn kết

```json
{
  "outro": { "text": "またあした", "seconds": 3.0 }
}
```

Ngắn hơn màn mở đầu có chủ ý. Người xem đã nhận được thứ họ đến để nhận; kéo dài
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
