"""
Lớp A (nội dung) và lớp B (tài sản) của vidgen-kit.

Toàn bộ package này chỉ có một sản phẩm duy nhất: file
`content/<slug>.build.json` — hợp đồng với Remotion. Không module nào ở đây
được biết Remotion vẽ chữ ra sao, và không file nào bên studio/ được đọc
ngược vào đây.

Thứ tự phụ thuộc, đọc từ dưới lên:

    env       nạp .env (khoá API)
    probe     đo giây     (không biết frame, không biết kịch bản)
    script    đọc + kiểm kịch bản người viết
    reading   sinh romaji + hiragana từ câu Nhật
    tts       sinh giọng đọc, có cache
    library   sổ đăng ký tài sản: nguồn, tác giả, giấy phép, tag
    fetch     tải clip mới về và ghi sổ  (chỉ chạy khi người dùng gọi tay)
    shots     chọn clip cho từng cảnh    (cần biết cảnh dài bao nhiêu -> sau tts)
    assets    xác minh clip nền và nhạc nền có thật
    timeline  ĐỔI GIÂY RA FRAME — nơi duy nhất được phép (P-2)
    contract  ghi build.json
    run       xâu cả dây chuyền lại thành một lệnh
"""
