# Caption trên màn hình: cỡ chữ và câu dài

Hai chuyện này là một chuyện. Bản trước đối phó với câu dài bằng cách **bóp cỡ
chữ nhỏ lại**, nên câu càng dài chữ càng bé — và vì mỗi câu một độ dài khác nhau,
cỡ chữ nhảy lên nhảy xuống suốt video. Giờ câu dài được **cắt ra**, còn cỡ chữ
thì đứng yên.

---

## Chuyện gì đã đổi

Lấy đúng câu này của `2026-08-20`:

```
毎日の生活は、同じことの繰り返しに見えるけれど、小さな変化が、きっとどこかにあります。
```

43 chữ. Trước đây nó hiện nguyên một màn, ở cỡ 42 trong khi các cảnh khác ở cỡ
55–62. Giờ nó thành hai màn chữ nối tiếp nhau, cùng cỡ 56 như mọi cảnh:

```
|<---------------- MỘT cảnh, MỘT clip, MỘT file mp3 ----------------->|
| 毎日の生活は、同じことの繰り返しに見えるけれど、| 小さな変化が、きっとどこかにあります。|
0                                            137                    283
                                              ^
                              đổi chữ ở đây — KHÔNG cắt cảnh
```

**Mảnh không phải cảnh.** Vẫn một clip nền chạy liên tục, vẫn một file giọng đọc
liền hơi, frame chạy tiếp bình thường. Chỉ có chữ là đổi. Vì vậy cắt mảnh **không
cộng thêm một frame nào** vào video, và mốc hồi quy 1562 frame không nhúc nhích.

Không phải chia đôi cảnh, vì chia đôi cảnh thì giữa hai nửa câu sẽ có
`pauseAfter` + `leadIn` ≈ một giây im lặng, và TTS đọc hai nửa thành hai câu rời
— mất hẳn ngữ điệu.

---

## Mảnh sau vào ở đúng giây nào

Không ước lượng. `edge-tts` trả về **mốc từng chữ** (`WordBoundary`) ngay trong
lượt gọi sinh mp3, nên máy biết chính xác giọng đọc chạm vào 「小さな」 ở giây
4,562. Mảnh hai vào sớm hơn mốc đó đúng `leadIn` — bằng đúng khoảng chữ đi trước
tiếng ở đầu mỗi cảnh.

Đây vẫn là P-1: **audio là nguồn sự thật**. Không ai gõ tay một timestamp nào, và
sửa một câu không làm lệch chỗ nào khác.

Mốc từng chữ nằm trong `content/<ngày>/.cache.json`, cạnh vân tay TTS. Xoá file
đó đi thì máy đọc lại và sinh ra y hệt — nó vẫn chỉ là cache.

---

## Cỡ chữ giờ cố định

| | Cỡ | Đổi khi nào |
|---|---|---|
| Câu tiếng Nhật | 56 | chỉ khi một màn quá 30 chữ |
| Romaji | 30 | không bao giờ |
| Nghĩa tiếng Việt | 38 | chỉ khi một màn quá 88 ký tự |

Đo trên 286 câu của 31 ngày đang có: **292 màn chữ, không màn nào phải co lại.**
Tức là cỡ chữ 56/38 ở mọi cảnh, mọi ngày.

Câu dài hơn thì khối chữ cao thêm một dòng chứ không nhỏ đi. Khối caption neo vào
đáy vùng an toàn nên nó nở **lên trên**, chân chữ không xê dịch — người xem không
thấy gì nhảy.

Hai bậc nhỏ phía sau (46/38 cho tiếng Nhật, 32/28 cho tiếng Việt) chỉ là lưới an
toàn. Rơi vào đó là `make content` đã kêu một dòng rồi: **cỡ chữ nhỏ bất thường ở
một cảnh là triệu chứng, không phải cách chữa.**

---

## Bốn ngưỡng, hai việc khác nhau

Khai ở `pipeline/phrase.py`. Đừng lẫn hai cặp:

| Ngưỡng | Số | Trả lời câu hỏi |
|---|---|---|
| `JA_MAX` / `VI_MAX` | 24 chữ / 60 ký tự | **Có cắt không?** Bao nhiêu chữ thì đọc một màn là vừa |
| `JA_FIT` / `VI_FIT` | 30 chữ / 88 ký tự | **Có kêu không?** Bao nhiêu chữ thì còn vừa cỡ chữ chuẩn |

Cặp đầu chặt hơn cặp sau, **cố ý**. Nhờ khoảng đệm đó, câu nào không cắt được vẫn
hiện nguyên ở đúng cỡ chữ như mọi cảnh khác — chỉ là một màn chữ hơi dày. Chỉ khi
vượt luôn cặp sau thì chữ mới phải co, và đó mới là lúc đáng kêu.

`JA_FIT` / `VI_FIT` phải khớp thang cỡ chữ trong `studio/src/Caption.tsx` — chúng
là chỗ chữ bắt đầu phải xuống dòng thứ ba. Đổi một bên thì đổi cả bên kia.

---

## Máy cắt ở đâu

Cắt ngay **sau** dấu ngắt ý: `、。！？` với tiếng Nhật, `,;.:!?` với tiếng Việt.
Dấu phẩy ở lại cuối mảnh trước — chính nó báo cho người xem biết câu chưa hết.

Trong các cách cắt hợp lệ, máy chọn cách **cân nhất** (mảnh dài nhất càng ngắn
càng tốt). Tất định: cùng câu thì lúc nào cũng ra cùng kết quả.

Câu Nhật và bản dịch phải ra **bằng số mảnh**, vì hai bên hiện cùng lúc trên một
khung. Số mảnh lấy theo bên nào cần nhiều hơn.

Không đủ dấu ngắt ở một bên thì câu **giữ nguyên**, không cắt lệch. Máy không tự
bịa ra chỗ ngắt giữa một mệnh đề.

---

## Tự chia bằng tay

Cùng quy ước với `clip`: bỏ trống thì máy làm hộ, ghi vào thì **người viết thắng**.
Viết `ja` và `vi` thành danh sách:

```json
{
  "ja": ["新しい月だからといって、", "急に変わらなくていいのです。"],
  "vi": ["Tháng mới không có nghĩa là", "bạn phải đổi khác ngay."]
}
```

Hai danh sách phải bằng số phần tử, nếu không `make content` dừng và nói rõ.

Dùng nó khi bản dịch không có dấu phẩy ở chỗ cần cắt — như ví dụ trên: tiếng Nhật
ngắt ở 「といって、」 mà tiếng Việt thì "Tháng mới không có nghĩa là bạn phải đổi
khác ngay." chẳng có dấu nào để bấu víu.

**Giọng đọc và bài đăng không đổi.** Máy ghép các mảnh lại thành nguyên câu trước
khi đưa cho TTS (tiếng Nhật ghép sát, tiếng Việt ghép bằng dấu cách), nên
`out/<ngày>/script.txt` và `description.txt` vẫn in nguyên câu như cũ.

---

## Xem lại cho chắc

```bash
make content DAY=2026-08-20    # in ra câu nào được cắt làm mấy mảnh
make check   DAY=2026-08-20    # trang duyệt: MỘT ảnh cho MỖI màn chữ
```

`make check` giờ trích một khung cho mỗi mảnh chứ không phải mỗi cảnh — lấy giữa
cảnh thì mảnh đầu không ai nhìn thấy. Nhãn ghi `Cảnh 4 · mảnh 1`.

`content/<ngày>/build.json` và `out/<ngày>/metadata.json` đều có trường
`segments`; `null` nghĩa là câu hiện nguyên một màn.

---

## Nhịp đổi chữ

| | Frame | Vì sao |
|---|---|---|
| Câu mới hiện vào | 26 | một ý mới, xứng đáng được chờ |
| Câu cũ tắt đi | 20 | nhường chỗ trước khi chuyển cảnh |
| Đổi giữa hai mảnh | 8 | giọng đọc đang chạy liền hơi — tắt lâu là tưởng hết câu |

Hai mảnh **không chồng lên nhau**: mảnh trước tắt hẳn rồi mảnh sau mới hiện. Chồng
lên nhau thì trong quãng giao có hai câu khác nhau cùng nằm giữa khung, đọc ra chữ
nọ xọ chữ kia. Nhịp hụt rất ngắn ở giữa đọc ra như một hơi thở, mà tai thì vẫn
đang nghe giọng đọc nên không thấy hụt.

---

## Xem thêm

- Trường nào là nội dung, trường nào là cài đặt: `docs/kich-ban-va-kiem-tra.md`
- Caption để ĐĂNG (khác hẳn caption trên màn hình): `docs/dang-bai.md`
- Tiêu đề ngày và màn kết: `docs/mo-dau-va-ket.md`
