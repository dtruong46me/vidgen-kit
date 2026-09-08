"""
Lớp A (nội dung) và lớp B (tài sản) của vidgen-kit.

Toàn bộ package này chỉ có một sản phẩm duy nhất: file
`content/<slug>.build.json` — hợp đồng với Remotion. Không module nào ở đây
được biết Remotion vẽ chữ ra sao, và không file nào bên studio/ được đọc
ngược vào đây.

Thứ tự phụ thuộc, đọc từ dưới lên:

    probe     đo giây     (không biết frame, không biết kịch bản)
    script    đọc + kiểm kịch bản người viết
    tts       sinh giọng đọc, có cache
    assets    xác minh clip nền và nhạc nền có thật
    timeline  ĐỔI GIÂY RA FRAME — nơi duy nhất được phép (P-2)
    contract  ghi build.json
    run       xâu sáu bước trên lại thành một lệnh
"""
