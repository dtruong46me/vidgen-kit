# Khung sản xuất video trà đạo / triết lý song ngữ Nhật – Việt

Tài liệu này hướng dẫn dựng **một khung (template) làm sẵn một lần, sau đó mỗi ngày chỉ cần
thay nội dung là ra một video mới**.

Đặc tả video:

| Hạng mục | Giá trị |
|---|---|
| Khổ hình | 1080×1920 dọc (TikTok / Shorts / Reels), 30 fps |
| Độ dài | 35–45 giây |
| Nội dung | ~9 câu tiếng Nhật, giọng nữ đọc chậm |
| Caption | 3 tầng: câu Nhật → cách đọc romaji → nghĩa tiếng Việt |
| Hình | Mỗi câu = một cảnh, hết câu thì chuyển cảnh mờ chồng |
| Âm | Giọng đọc từng câu + nhạc nền nhỏ chạy suốt |

Toàn bộ hướng dẫn dưới đây đã được dựng và render thật ở
`tmp/remotion_lab/tea-philosophy/`. Kết quả thực tế: `out/2026-08-20.mp4`, 1080×1920,
30 fps, **44,3 giây**, h264 + aac, 13 MB.

> Nếu bạn chưa từng cài Remotion, đọc [remotion-guide.md](remotion-guide.md) trước —
> tài liệu đó nói về cài đặt và giao diện Studio nói chung. Tài liệu này là bước tiếp theo:
> dựng một dây chuyền sản xuất cụ thể.

---

## 1. Nguyên lý của khung này

Điểm mấu chốt khiến khung này dùng lại được hàng ngày:

> **Bạn không bao giờ tự gõ thời lượng.**
> Bạn viết câu → máy đọc câu đó → đo xem giọng đọc dài bao nhiêu giây → độ dài cảnh
> và độ dài cả video tự suy ra từ đó.

Nhờ vậy, thêm một câu hay sửa một câu cho dài hơn cũng không làm lệch tiếng khỏi hình.
Dòng chảy dữ liệu:

```
content/2026-08-20.json          bạn viết tay: 9 câu, mỗi câu 3 dòng ja/romaji/vi
        │
        │  scripts/build.py  →  edge-tts đọc từng câu  →  public/audio/2026-08-20/line-01..09.mp3
        │                    →  ffprobe đo từng file   →  biết mỗi câu dài mấy frame
        ▼
content/2026-08-20.build.json    máy sinh: nội dung + đường dẫn audio + số frame từng cảnh
        │
        │  npx remotion render Daily --props=...
        ▼
out/2026-08-20.mp4
```

Một cảnh gồm 3 quãng thời gian:

```
│← leadIn 0.2s →│←──── giọng đọc ────→│← pauseAfter 0.35s →│
│               │                      │                    │
caption hiện ra   máy đọc câu tiếng Nhật   khoảng lặng để người xem đọc kịp nghĩa
```

---

## 2. Chuẩn bị môi trường

Ngoài Node.js + Remotion (xem tài liệu cài đặt), khung này cần thêm 2 thứ:

```bash
# 1. ffmpeg — để đo độ dài file audio (lệnh ffprobe đi kèm)
sudo apt-get install -y ffmpeg          # macOS: brew install ffmpeg

# 2. edge-tts — công cụ đọc tiếng Nhật, miễn phí, giọng neural nghe rất tự nhiên
pip install edge-tts
```

Kiểm tra nhanh:

```bash
ffprobe -version | head -1
python3 -m edge_tts --voice ja-JP-NanamiNeural --text "おはようございます。" --write-media test.mp3
```

Nghe thử `test.mp3`, thấy giọng nữ đọc rõ ràng là được.

**Các giọng dùng được** (`python3 -m edge_tts --list-voices`):

| Voice | Ngôn ngữ | Giới tính | Ghi chú |
|---|---|---|---|
| `ja-JP-NanamiNeural` | Nhật | Nữ | mặc định của khung này, giọng dịu, hợp nội dung tĩnh |
| `ja-JP-KeitaNeural` | Nhật | Nam | trầm hơn, hợp nội dung thiền / triết lý nặng |
| `vi-VN-HoaiMyNeural` | Việt | Nữ | nếu muốn làm bản đọc tiếng Việt |
| `vi-VN-NamMinhNeural` | Việt | Nam | |

---

## 3. Tạo project và cấu trúc thư mục

```bash
cd tmp/remotion_lab
npx create-video@latest tea-philosophy --blank --yes
cd tea-philosophy
npm i
npm i @remotion/google-fonts        # để có font chữ Nhật, xem mục 6.4
mkdir -p content scripts public/audio public/video
```

Cấu trúc cuối cùng — nhớ vai trò từng thư mục, đây là bản đồ để bạn biết sửa ở đâu:

```
tea-philosophy/
├── content/                     ← NƠI BẠN LÀM VIỆC HÀNG NGÀY
│   ├── 2026-08-20.json          kịch bản bạn viết tay
│   └── 2026-08-20.build.json    máy sinh, đừng sửa tay
│
├── public/                      ← NGUYÊN LIỆU
│   ├── audio/
│   │   ├── bgm.mp3              nhạc nền, dùng chung mọi video
│   │   └── 2026-08-20/          giọng đọc từng câu, máy sinh
│   └── video/
│       └── scene-01.mp4 …       clip nền cho từng cảnh
│
├── scripts/                     ← DÂY CHUYỀN
│   ├── build.py                 TTS + đo thời lượng + sinh build.json
│   └── make.sh                  chạy build.py rồi render, 1 lệnh ra video
│
└── src/                         ← KHUNG, viết 1 lần rồi hầu như không đụng lại
    ├── types.ts                 hình dạng dữ liệu
    ├── fonts.ts                 nạp font Nhật + Việt
    ├── Background.tsx           lớp hình nền + chuyển cảnh
    ├── Caption.tsx              khối chữ 3 tầng
    ├── DailyVideo.tsx           ghép các lớp theo dòng thời gian
    └── Composition.tsx          khai báo video, tính độ dài tự động
```

---

## 4. Bước 1 — Viết kịch bản

Đây là file duy nhất bạn gõ tay mỗi ngày: `content/<ngày>.json`.

```json
{
  "id": "2026-08-20",
  "title": "8月20日 - 小さな幸せ",

  "voice": "ja-JP-NanamiNeural",
  "rate": "+0%",
  "pitch": "+0Hz",

  "bgm": "audio/bgm.mp3",
  "bgmVolume": 0.12,

  "fps": 30,
  "width": 1080,
  "height": 1920,

  "leadIn": 0.2,
  "pauseAfter": 0.35,
  "targetSeconds": [35, 45],

  "lines": [
    {
      "ja": "今日も新しい一日が始まりました。",
      "romaji": "Kyō mo atarashii ichinichi ga hajimarimashita.",
      "vi": "Hôm nay, một ngày mới lại bắt đầu.",
      "clip": "video/scene-01.mp4"
    },
    {
      "ja": "おはようございます。",
      "romaji": "Ohayō gozaimasu.",
      "vi": "Chào buổi sáng.",
      "clip": "video/scene-02.mp4"
    }
  ]
}
```

Ý nghĩa các tham số điều khiển:

| Trường | Tác dụng |
|---|---|
| `rate` | tốc độ đọc. `"+0%"` bình thường, `"-10%"` chậm & thiền hơn, `"+8%"` nhanh để rút ngắn video |
| `leadIn` | caption hiện ra trước bao nhiêu giây rồi mới có tiếng — cho mắt kịp bắt chữ |
| `pauseAfter` | im lặng bao nhiêu giây sau khi đọc xong — cho não kịp ngấm nghĩa |
| `bgmVolume` | `0.12` là mức nhạc nền không át lời. Trên `0.2` bắt đầu tranh tiếng với giọng đọc |
| `targetSeconds` | khoảng độ dài mong muốn; chạy xong `build.py` sẽ cảnh báo nếu lệch ra ngoài |
| `clip` | clip nền của câu đó. **Thiếu file cũng không sao** — tự rơi về nền gradient |

### Quy tắc tách câu

**Một dòng trong `lines` = một câu = một cảnh.** Cắt theo dấu `。` là chuẩn nhất.
Với câu dài có `けれど` / `が` nối hai vế, cứ để nguyên một dòng — chữ sẽ tự co nhỏ lại
(xem mục 6.3), tách đôi sẽ làm cảnh vụn và mất nhịp.

Với 9 câu như ví dụ, độ dài rơi vào khoảng 44 giây — vừa đúng khung 35–45s.

### Ba tầng nội dung

- **`ja`** — câu gốc. Viết đúng chính tả và dấu câu tiếng Nhật (`、` và `。`, không dùng
  `,` `.` của tiếng Anh) vì edge-tts dựa vào dấu câu để ngắt nghỉ.
- **`romaji`** — cách đọc, dành cho người mới chưa đọc được kana/kanji. Dùng kiểu Hepburn,
  giữ dấu macron cho nguyên âm dài: `Kyō` (không phải `Kyou`), `gozaimasu`, `pēsu`.
  Lưu ý số và ngày tháng phải ghi cách đọc thật: `8月20日` → `hachigatsu hatsuka`
  (ngày 20 đọc là *hatsuka*, không phải *nijūnichi*).
- **`vi`** — nghĩa tiếng Việt. Dịch thoát cho mượt, giữ được trợ từ cuối câu vì đó là
  toàn bộ cái "chất" của thể loại này: `〜ね` → "nhỉ", `〜ように` → "chúc/mong sao",
  `〜たり…たり` → liệt kê "nào là… nào là…". Cố gắng giữ dưới ~85 ký tự cho một dòng đẹp.

---

## 5. Bước 2 — Chuẩn bị nguyên liệu hình và nhạc

### 5.1 Clip nền

Đặt vào `public/video/`, đặt tên `scene-01.mp4` … `scene-09.mp4` khớp với thứ tự câu.

Quy cách nên theo:

| Tiêu chí | Khuyến nghị | Lý do |
|---|---|---|
| Khổ | dọc 1080×1920, hoặc ngang rồi để `objectFit: cover` cắt | khung đã cắt tự động, nhưng clip dọc sẽ giữ được nhiều chi tiết hơn |
| Độ dài | ≥ 5 giây | clip ngắn hơn cảnh sẽ **tự động chạy lặp**, nhưng lặp quá nhiều lần sẽ lộ |
| Nội dung | cảnh tĩnh, máy quay chuyển động chậm | khung đã tự thêm hiệu ứng phóng chậm; clip đã động sẵn sẽ thành rối |
| Tông màu | trầm, ít tương phản | caption chữ trắng nằm đè lên giữa hình |

Nguồn clip miễn phí dùng thương mại được: Pexels Videos, Pixabay, Coverr — tìm theo từ khoá
`japanese tea ceremony`, `matcha`, `zen garden`, `rain window`, `steam cup`, `bamboo forest`.

Không có clip cũng không sao: cứ để tên file trong `clip`, script phát hiện thiếu file sẽ báo
`(thiếu video/scene-02.mp4 -> dùng nền gradient)` và cảnh đó dùng nền chuyển sắc tông trầm.
Bạn hoàn toàn có thể ra video đầu tiên mà chưa có một clip nào.

### 5.2 Nhạc nền

Một file `public/audio/bgm.mp3` dùng chung cho mọi video. Khung sẽ **tự lặp** nó cho
đủ độ dài, nên file 20–30 giây là đủ. Chọn nhạc không lời, không có nhịp mạnh —
koto, shakuhachi, ambient piano, tiếng mưa.

---

## 6. Bước 3 — Dây chuyền và khung dựng hình

### 6.1 `scripts/build.py` — biến câu chữ thành nguyên liệu có thời lượng

Script làm 4 việc cho từng câu:

1. Gọi edge-tts đọc câu đó ra `public/audio/<ngày>/line-XX.mp3`.
2. Dùng `ffprobe` đo độ dài thật của file vừa tạo.
3. Quy ra frame: `durationInFrames = ceil((leadIn + độ_dài_giọng + pauseAfter) × fps)`.
4. Kiểm tra clip nền có tồn tại không, nếu không thì ghi `null`.

Chạy:

```bash
python3 scripts/build.py 2026-08-20
```

Kết quả thật khi chạy với 9 câu ví dụ:

```
  [tts]   line-01.mp3  今日も新しい一日が始まりました。...
  [tts]   line-02.mp3  おはようございます。...
          (thiếu video/scene-02.mp4 -> dùng nền gradient)
  ...
Đã ghi content/2026-08-20.build.json
9 câu — tổng 1327 frame = 44.2 giây
```

Hai chi tiết đáng chú ý trong script:

- **Có bộ nhớ đệm.** Mỗi câu được băm theo `nội dung + voice + rate + pitch`. Lần chạy sau,
  câu nào không đổi sẽ hiện `[cache]` và bỏ qua TTS. Sửa 1 câu trong 9 câu thì chỉ 1 câu
  được đọc lại — rất đáng tiền khi làm hàng loạt.
- **Có cảnh báo độ dài.** Nếu tổng lệch ra ngoài `targetSeconds`, script in ra hướng chỉnh:

  ```
  [!] Video đang ngắn hơn khoảng mong muốn 35-45s.
      Cách chỉnh: sửa "rate" (vd. "+8%" đọc nhanh hơn), giảm/tăng "pauseAfter",
      hoặc thêm/bớt câu trong "lines".
  ```

Một lỗi rất dễ vấp nếu bạn tự viết lại script này: gọi edge-tts với tốc độ âm phải dùng dạng
`--rate=-10%` chứ **không** phải `--rate -10%`, vì `-10%` sẽ bị hiểu nhầm là tên một tuỳ chọn.

### 6.2 `src/DailyVideo.tsx` — ba lớp trên dòng thời gian

Đây là ý tưởng quan trọng nhất của khung. Video được xếp thành 3 lớp chồng lên nhau,
**mỗi lớp có quy tắc thời gian riêng**:

```
            0        129        213         324  …  (frame)
            │         │          │           │
lớp NỀN     ├─cảnh 1──┼──cảnh 2──┼──cảnh 3───┤    ← các cảnh CHỒNG MÉP 15 frame → chuyển cảnh mờ
                    ╲╱         ╲╱
lớp CHỮ+TIẾNG ├─câu 1─┼──câu 2──┼──câu 3────┤     ← KHÔNG chồng, để giọng đọc không đè nhau
lớp NHẠC      ├──────────────────────────────┤    ← chạy suốt, lặp lại cho đủ độ dài
```

```tsx
{/* Lớp 1 — NỀN: bắt đầu sớm hơn 15 frame và mờ dần hiện lên trong quãng đó,
    nên nó chồng lên cuối cảnh trước => ra hiệu ứng chuyển cảnh mờ */}
{lines.map((line, i) => (
  <Sequence
    key={`bg-${i}`}
    from={Math.max(0, starts[i] - CROSSFADE)}
    durationInFrames={line.durationInFrames + (i === 0 ? 0 : CROSSFADE)}
    name={`Nền ${i + 1}`}
  >
    <Background line={line} index={i} fadeInFrames={CROSSFADE} />
  </Sequence>
))}

{/* Lớp 2 — CAPTION + GIỌNG ĐỌC: mỗi câu nằm đúng ô thời gian của nó */}
{lines.map((line, i) => (
  <Sequence key={`line-${i}`} from={starts[i]} durationInFrames={line.durationInFrames}>
    <Caption line={line} />
    <Sequence from={line.audioStartInFrames} name="Giọng đọc">
      <Audio src={staticFile(line.audio)} />
    </Sequence>
  </Sequence>
))}

{/* Lớp 3 — NHẠC NỀN: lặp cho đủ độ dài video */}
{bgm && bgmDurationInFrames ? (
  <Sequence durationInFrames={total} name="Nhạc nền">
    <Loop durationInFrames={bgmDurationInFrames}>
      <Audio src={staticFile(bgm)} volume={bgmVolume} />
    </Loop>
  </Sequence>
) : null}
```

Nếu bạn tách hai lớp này ra mà cho **cả** caption chồng mép theo nền, hai giọng đọc sẽ
đè lên nhau 0,5 giây ở mỗi lần chuyển cảnh. Đó chính là lý do phải tách.

Muốn chuyển cảnh nhanh hay chậm hơn thì đổi mỗi hằng số:

```tsx
export const CROSSFADE = 15;   // 15 frame ở 30fps = 0.5 giây
```

### 6.3 `src/Caption.tsx` — khối chữ ba tầng

Bố cục từ trên xuống: câu Nhật (to, đậm) → romaji (nhỏ, nghiêng, mờ) → gạch ngăn →
nghĩa tiếng Việt (vừa, màu ngà ấm). Cả khối hiện lên bằng `spring` kèm trượt lên 26px,
và mờ đi 10 frame trước khi hết cảnh để không đè lên câu kế tiếp.

Chi tiết quan trọng cho việc sản xuất hàng loạt là **cỡ chữ tự co theo độ dài câu**:

```tsx
const fitJa = (len: number) =>
  len <= 14 ? 66 : len <= 22 ? 58 : len <= 32 ? 50 : len <= 44 ? 44 : 38;

const fitVi = (len: number) =>
  len <= 30 ? 42 : len <= 55 ? 38 : len <= 85 ? 34 : 30;
```

Nhờ nó, câu 5 chữ và câu 44 chữ đều nằm gọn giữa khung, bố cục không bao giờ vỡ —
bạn viết kịch bản mà không phải canh độ dài từng câu.

### 6.4 `src/fonts.ts` — không có bước này là ra ô vuông

Máy render (kể cả máy bạn, kể cả CI) thường **không cài sẵn font chữ Nhật**. Không nạp font
thì toàn bộ chữ Nhật render ra thành ô vuông trống (gọi là "tofu"). Noto Serif JP giải quyết
cả ba nhu cầu trong một font: chữ Nhật, macron của romaji, và dấu tiếng Việt.

```ts
import { loadFont } from "@remotion/google-fonts/NotoSerifJP";

export const { fontFamily: serifJP } = loadFont("normal", {
  // chỉ lấy đúng 2 độ đậm đang dùng — mỗi weight là hàng trăm request tải font
  weights: ["400", "600"],
  subsets: ["japanese", "latin", "latin-ext", "vietnamese"],
  ignoreTooManyRequestsWarning: true,
});
```

Bộ chữ Nhật bị Google chia thành hàng trăm mảnh nhỏ, nên **mỗi weight thừa là ~120 lượt tải
thêm** làm chậm render. Chỉ khai báo weight thật sự dùng.

### 6.5 `src/Composition.tsx` — độ dài tự tính

```tsx
const calculateMetadata: CalculateMetadataFunction<DailyVideoProps> = ({ props }) => {
  const total = props.lines.reduce((sum, l) => sum + l.durationInFrames, 0);
  return {
    durationInFrames: total,
    fps: props.fps,
    width: props.width,
    height: props.height,
  };
};

export const MyComposition = () => (
  <Composition
    id="Daily"
    component={DailyVideo}
    calculateMetadata={calculateMetadata}
    defaultProps={buildData as DailyVideoProps}
    // Các số dưới đây chỉ là giá trị tạm; calculateMetadata sẽ ghi đè hết
    durationInFrames={1}
    fps={30}
    width={1080}
    height={1920}
  />
);
```

Cần bật `"resolveJsonModule": true` trong `tsconfig.json` để `import` được file JSON.

> **Đây chính là lý do 3 ô Dimensions / Frame rate / Duration trong Remotion Studio bị xám
> và không sửa được bằng chuột** — điều bạn có thể đã thắc mắc ở tài liệu trước. Ở khung này
> nó là chủ ý: độ dài phải do giọng đọc quyết định, không được sửa tay, nếu không tiếng
> sẽ lệch khỏi hình.

---

## 7. Bước 4 — Xem và chỉnh trên giao diện Studio

```bash
npm run dev
```

Studio mở ở `http://localhost:3000`, chọn composition **Daily** ở sidebar trái.

### Đọc timeline

Vùng track dưới cùng chính là hình vẽ ở mục 6.2 nhưng ở dạng thật. Nhờ prop `name` đặt cho
từng `<Sequence>`, bạn sẽ thấy các thanh có tên tiếng Việt rõ ràng thay vì `Sequence`:

```
Nền 1 ▓▓▓▓▓▓▓
  Nền 2   ▓▓▓▓▓▓▓▓         ← thò sang trái, đè lên Nền 1: đó là đoạn chuyển cảnh
Câu 1 — 今日も新しい ▓▓▓▓▓▓
  └ Giọng đọc     ▓▓▓▓▓
Nhạc nền ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

Đặt tên có dấu như vậy khiến việc soát lỗi nhanh hơn hẳn — nhìn timeline là biết ngay câu nào
đang ở đâu. Bấm vào một thanh để nhảy tới đoạn đó.

### Việc nên làm trên giao diện

| Việc | Thao tác |
|---|---|
| **Soát mép chuyển cảnh** | Kéo con trỏ tới ranh giới 2 cảnh, tua từng frame bằng phím `←` `→`. Đúng thì thấy hình cũ mờ dần sang hình mới trong ~0.5s, chữ cũ đã tắt hẳn trước khi chữ mới hiện |
| **Nghe cân bằng tiếng** | Bấm Play. Nếu nhạc át lời → giảm `bgmVolume` xuống `0.08` trong file kịch bản rồi chạy lại `build.py` |
| **Kiểm tra chữ có tràn khung không** | Dùng `[` và `]` trên playback bar để khoanh riêng cảnh có câu dài nhất, xem đi xem lại đoạn đó |
| **Đổi màu / cỡ chữ / bố cục** | Sửa `src/Caption.tsx`, lưu file — Studio hot-reload ngay, không cần khởi động lại |
| **Xuất thử 1 khung hình** | Menu `Composition` → chụp still để xem chi tiết ở kích thước thật |

### Việc **không** nên làm trên giao diện

- Đừng kéo giãn các thanh trong timeline. Độ dài đến từ `build.json`; kéo tay chỉ sửa được
  tạm trong phiên đó và sẽ bị ghi đè ngay lần chạy `build.py` sau.
- Đừng sửa Duration ở Inspector (đã bị khoá, và đó là chủ ý — xem mục 6.5).
- Đừng dùng nút `Add asset...` để thêm cảnh. Ở khung này nguồn sự thật là `content/*.json`,
  thêm asset thẳng vào code sẽ khiến hai nơi lệch nhau.

Nói ngắn gọn: **giao diện Studio ở đây dùng để soi và chỉnh style, không dùng để dựng nội dung.**
Nội dung luôn đi từ file kịch bản.

---

## 8. Bước 5 — Render

```bash
npx remotion render Daily out/2026-08-20.mp4 --props=./content/2026-08-20.build.json
```

Số đo thật của lần render mẫu: **4 phút 36 giây** cho video 44,3 giây trên máy 2 nhân.
Máy nhiều nhân sẽ nhanh hơn nhiều — thêm `--concurrency=8` nếu máy khoẻ.

Kiểm tra lại kết quả trước khi đăng:

```bash
ffprobe -v error -show_entries format=duration \
  -show_entries stream=codec_type,width,height -of default=nw=1 out/2026-08-20.mp4
# phải thấy: 1080x1920, có cả codec_type=video lẫn codec_type=audio, duration ≈ 44.3

ffmpeg -hide_banner -i out/2026-08-20.mp4 -af volumedetect -vn -f null /dev/null 2>&1 \
  | grep -E "mean_volume|max_volume"
# mean_volume ≈ -21 dB, max_volume ≈ -6 dB là mức lành mạnh; max chạm 0.0 dB là bị vỡ tiếng
```

Thiếu luồng `codec_type=audio` nghĩa là đường dẫn audio sai — kiểm tra lại `public/audio/`.

---

## 9. Bước 6 — Sản xuất hàng loạt

Đây là mục đích cuối cùng của cả khung. Sau khi `src/` đã ổn định, **quy trình mỗi ngày chỉ
còn 2 bước**: viết một file JSON, chạy một lệnh.

`scripts/make.sh` gộp cả hai bước máy làm:

```bash
#!/usr/bin/env bash
set -euo pipefail
slug="${1:?Thiếu slug. Ví dụ: ./scripts/make.sh 2026-08-21}"
cd "$(dirname "$0")/.."

echo "==> [1/2] TTS + tính thời lượng"
python3 scripts/build.py "$slug"

echo "==> [2/2] Render"
npx remotion render Daily "out/$slug.mp4" --props="./content/$slug.build.json"

echo "==> Xong: out/$slug.mp4"
```

Làm một video:

```bash
./scripts/make.sh 2026-08-21
```

Làm cả loạt — copy nhiều file kịch bản vào `content/` rồi chạy:

```bash
for f in content/*.json; do
  case "$f" in *.build.json) continue;; esac
  ./scripts/make.sh "$(basename "$f" .json)"
done
```

Điều làm cho việc này chạy được là cờ `--props`: **một composition duy nhất, mỗi lần render
nạp một bộ dữ liệu khác nhau.** Bạn không cần tạo thêm `<Composition>` cho mỗi ngày.

### Nhịp làm việc gợi ý

1. **Một lần duy nhất:** tải sẵn 20–30 clip nền vào `public/video/`, đặt tên theo chủ đề
   (`tea-01.mp4`, `rain-03.mp4`, `garden-02.mp4`…) thay vì `scene-01`, để tái sử dụng chéo
   giữa các ngày.
2. **Mỗi buổi:** viết 5–10 file kịch bản một lượt. Đây là phần tốn công thật (dịch + romaji);
   phần còn lại máy làm.
3. **Chọn clip:** với mỗi câu, điền trường `clip` bằng tên clip hợp cảnh trong kho.
4. **Chạy vòng lặp** ở trên, đi pha trà, quay lại lấy video.
5. **Soát nhanh:** mở mỗi file, tua 3 mốc — đầu, giữa, cuối. Chủ yếu là để bắt lỗi
   chính tả và lỗi dịch, vì phần kỹ thuật đã cố định.

---

## 10. Bảng chỉnh độ dài về đúng 35–45 giây

Chạy `build.py` xong thấy cảnh báo lệch, tra bảng này:

| Tình huống | Cách xử lý | Mức ảnh hưởng |
|---|---|---|
| Dài hơn 45s một chút | `rate` từ `"+0%"` → `"+8%"` | rút ~8% tổng độ dài |
| Dài hơn nhiều | giảm `pauseAfter` `0.35` → `0.2` | rút ~0.15s × số câu |
| Dài hơn nhiều nữa | bớt 1–2 câu, hoặc gộp hai câu ngắn liền ý thành một | rút 3–5s mỗi câu |
| Ngắn hơn 35s | thêm câu, hoặc `rate` → `"-10%"` | mỗi câu thêm ~4s |
| Ngắn hơn ít | tăng `pauseAfter` → `0.6` | thêm ~0.25s × số câu |

Công thức để ước lượng trước khi chạy:

```
tổng ≈ Σ(độ dài giọng đọc từng câu) + số_câu × (leadIn + pauseAfter)
```

Với giọng `ja-JP-NanamiNeural` ở `rate: "+0%"`, một câu tiếng Nhật cỡ 15–20 ký tự đọc mất
khoảng 3,5–4 giây. Vậy **9 câu ≈ 44 giây** — chính là con số đo được ở ví dụ.

---

## 11. Tinh chỉnh phong cách

| Muốn đổi | Sửa ở đâu |
|---|---|
| Giọng đọc nam | `"voice": "ja-JP-KeitaNeural"` trong file kịch bản |
| Bảng màu nền gradient | mảng `PALETTES` trong `src/Background.tsx` — 9 cặp màu tông trầm |
| Tốc độ phóng hình (Ken Burns) | `interpolate(..., [1.06, 1.14], ...)` trong `src/Background.tsx` |
| Độ tối của lớp phủ trên clip | hai chuỗi `linear-gradient` cuối `src/Background.tsx` |
| Caption nằm thấp hơn (chừa chỗ cho UI TikTok) | `justifyContent: "center"` → `"flex-end"` + `paddingBottom: 320` trong `src/Caption.tsx` |
| Bỏ dòng romaji | xoá trường `romaji` khỏi kịch bản — `Caption.tsx` đã tự ẩn khi rỗng |
| Đổi sang khổ ngang 16:9 | `"width": 1920, "height": 1080` trong kịch bản; nhớ giảm cỡ chữ trong `fitJa`/`fitVi` |
| Chuyển cảnh nhanh/chậm | hằng số `CROSSFADE` trong `src/DailyVideo.tsx` |

---

## 12. Lỗi thường gặp

| Hiện tượng | Nguyên nhân | Cách sửa |
|---|---|---|
| Chữ Nhật ra ô vuông trống | chưa nạp font CJK | kiểm tra `src/fonts.ts` và `import "./fonts"` có được dùng trong `Caption.tsx` không |
| Tiếng Việt mất dấu / ra ô vuông | thiếu subset | thêm `"vietnamese"` và `"latin-ext"` vào `subsets` |
| Video ra nhưng không có tiếng | sai đường dẫn audio | `ffprobe` file ra, xem có `codec_type=audio` không; kiểm tra `public/audio/<ngày>/` có file thật |
| Hai giọng đọc chồng nhau | lớp caption bị cho chồng mép như lớp nền | lớp câu phải dùng `from={starts[i]}` không trừ `CROSSFADE` |
| Cảnh bị đen ở nửa sau | clip nền ngắn hơn cảnh và chưa bật loop | đảm bảo `build.py` có ghi `clipDurationInFrames`, `Background.tsx` có bọc `<Loop>` |
| `--rate` báo lỗi `expected one argument` | truyền giá trị âm dạng rời | dùng `--rate=-10%` chứ không phải `--rate -10%` |
| Render rất chậm ở đoạn đầu | tải font | giảm số `weights` trong `fonts.ts` |
| Nhạc nền tắt giữa chừng | file nhạc ngắn hơn video và chưa loop | kiểm tra `bgmDurationInFrames` có trong `build.json` không |
| `Cannot find module '.../*.build.json'` | chưa chạy `build.py` lần nào | chạy `python3 scripts/build.py <ngày>` trước khi mở Studio |

---

## Tài liệu tham khảo

- Cài đặt Remotion và giao diện Studio nói chung: [remotion-guide.md](remotion-guide.md)
- `calculateMetadata`: https://www.remotion.dev/docs/calculate-metadata
- Truyền dữ liệu khi render: https://www.remotion.dev/docs/passing-props
- `<Sequence>`: https://www.remotion.dev/docs/sequence
- `<Loop>`: https://www.remotion.dev/docs/loop
- `<Audio>`: https://www.remotion.dev/docs/audio
- `@remotion/google-fonts`: https://www.remotion.dev/docs/google-fonts
- edge-tts: https://github.com/rany2/edge-tts
