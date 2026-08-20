# Hướng dẫn cài đặt & edit video bằng Remotion

[Remotion](https://www.remotion.dev/) là framework dùng React để dựng video bằng code (mỗi frame là một lần render React component). Tài liệu này hướng dẫn cài Remotion và dựng một video edit thật (intro + clip + watermark + nhạc nền) trong `tmp/remotion_lab/`.

Toàn bộ các bước dưới đây đã được chạy thật để xác nhận hoạt động — project mẫu nằm sẵn tại `tmp/remotion_lab/flower-showcase/`.

> Đọc xong tài liệu này, xem tiếp [tea-philosophy-video-guide.md](tea-philosophy-video-guide.md) — dựng một dây chuyền hoàn chỉnh làm video trà đạo / triết lý song ngữ Nhật–Việt (TTS từng câu, caption 3 tầng, chuyển cảnh theo câu) để sản xuất hàng loạt.

## 1. Yêu cầu hệ thống

- Node.js ≥ 18 (máy hiện có Node `v24.14.0`, npm `11.9.0` — kiểm tra bằng `node -v`)
- `ffmpeg`/`ffprobe` (Remotion cần để encode video — máy hiện đã có sẵn tại `/usr/bin/ffmpeg`)
- Trình duyệt Chromium sẽ được Remotion tự tải khi render lần đầu

## 2. Cài đặt: tạo project Remotion mới

Mỗi project Remotion là một thư mục Node độc lập (có `package.json` riêng). Quy ước trong repo này: mỗi lần thử nghiệm tạo **một thư mục con riêng** trong `tmp/remotion_lab/<ten-project>` để không lẫn lộn giữa các lần edit.

```bash
# Tạo project mới, không tương tác (--yes), dùng template blank (rỗng)
npx create-video@latest --yes --blank tmp/remotion_lab/<ten-project-cua-ban>

cd tmp/remotion_lab/<ten-project-cua-ban>
npm i
```

Ví dụ project mẫu đã tạo sẵn trong repo:

```bash
npx create-video@latest --yes --blank tmp/remotion_lab/flower-showcase
cd tmp/remotion_lab/flower-showcase
npm i
```

> Lưu ý: template `--blank` mặc định cài kèm Tailwind CSS (`@remotion/tailwind-v4`, import trong `src/index.css`). Cờ `--no-tailwind` không có tác dụng với template này (đã kiểm tra thực tế). Nếu không cần Tailwind, cứ để mặc định — nó không ảnh hưởng gì đến việc dựng video bằng code như trong hướng dẫn này; muốn gỡ thì xoá 2 dependency trên trong `package.json` và dòng `@import "tailwindcss"` trong `src/index.css`.

Các template khác có thể dùng thay `--blank`: `--hello-world`, `--audiogram`, `--still`, `--three`, `--tiktok`... Xem đầy đủ bằng `npx create-video@latest --help`.

### Cấu trúc project sau khi tạo

```
flower-showcase/
├── package.json
├── remotion.config.ts
├── public/              # asset tĩnh (video/ảnh/audio) — truy cập bằng staticFile()
├── src/
│   ├── index.ts         # entry point, gọi registerRoot()
│   ├── Root.tsx          # khai báo danh sách Composition (video) của project
│   └── Composition.tsx   # nơi định nghĩa nội dung video
```

- **Composition** = một video output (id, kích thước, fps, số frame).
- Mỗi component React render ra 1 frame tại một thời điểm (`useCurrentFrame()`), Remotion sẽ chụp từng frame rồi ghép thành video.

## 3. Đưa asset vào project

Asset (video/ảnh/audio) cần nằm trong thư mục `public/` của project Remotion, rồi tham chiếu bằng `staticFile("duong/dan/trong/public")`.

Trong ví dụ mẫu, asset được copy từ `assets/` gốc của repo vào:

```bash
mkdir -p public/video public/audio public/image
cp ../../../assets/video/big_buck_bunny.mp4 public/video/
cp ../../../assets/audio/sample.mp3        public/audio/
cp ../../../assets/image/sample.jpg        public/image/
```

## 4. Edit video: chỉnh sửa `src/Composition.tsx`

Đây là phần "edit" thật sự — ghép nhiều đoạn (Sequence), video, ảnh, audio lại với nhau bằng code. File mẫu (`tmp/remotion_lab/flower-showcase/src/Composition.tsx`) dựng một video gồm 3 lớp:

| Đoạn | Frame | Nội dung |
|---|---|---|
| Title card | 0 → 90 (0s–3s) | Chữ "Vidgen Kit" fade in/out trên nền đen |
| Video clip | 90 → 330 (3s–11s) | `big_buck_bunny.mp4` phát full khung hình |
| Watermark | 30 → hết | Ảnh `sample.jpg` nhỏ, fade in, góc dưới-phải |
| Audio | xuyên suốt | `sample.mp3` làm nhạc nền, volume 0.5 |

Các khối API chính dùng trong file:

```tsx
import {
  AbsoluteFill, Audio, Img, OffthreadVideo, Sequence,
  interpolate, staticFile, useCurrentFrame, useVideoConfig, Composition,
} from "remotion";

// 1. Khai báo composition: kích thước, fps, tổng số frame
<Composition id="MyComp" component={MyComponent}
  durationInFrames={330} fps={30} width={1280} height={720} />

// 2. Sequence = cắt một đoạn video con vào 1 khoảng frame nhất định
<Sequence durationInFrames={90}><TitleCard /></Sequence>
<Sequence from={90} durationInFrames={240}><VideoClip /></Sequence>

// 3. interpolate() = tính giá trị (opacity, vị trí...) biến thiên theo frame → tạo hiệu ứng fade
const opacity = interpolate(frame, [0, 20], [0, 0.85], { extrapolateLeft: "clamp" });

// 4. Video/Ảnh/Audio đọc từ public/ qua staticFile()
<OffthreadVideo src={staticFile("video/big_buck_bunny.mp4")} />
<Img src={staticFile("image/sample.jpg")} />
<Audio src={staticFile("audio/sample.mp3")} volume={0.5} />
```

Quy tắc khi edit:
- Muốn **thêm đoạn/cảnh mới** → thêm `<Sequence from={...} durationInFrames={...}>`.
- Muốn **hiệu ứng chuyển động/fade** → dùng `interpolate()` hoặc `spring()` dựa trên `useCurrentFrame()`.
- Muốn **đổi độ dài video** → sửa `durationInFrames` trong `<Composition>` (đơn vị: số frame, = giây × fps).
- Video/ảnh/audio phải nằm trong `public/` và gọi qua `staticFile()`, không import trực tiếp path ngoài project.

## 5. Xem trước video (Remotion Studio)

```bash
cd tmp/remotion_lab/flower-showcase
npm run dev
```

Lệnh này mở Remotion Studio (trình duyệt, mặc định `http://localhost:3000`) — cho phép tua từng frame, xem trực tiếp kết quả khi sửa code (hot reload).

## 6. Edit trực tiếp bằng giao diện Remotion Studio

Remotion Studio không phải editor kéo-thả thuần tuý — mọi thứ vẫn là code trong `src/Composition.tsx`, nhưng Studio cho sửa nhanh một phần trực tiếp trên UI và **tự ghi lại vào file code** giúp bạn.

### Sơ đồ giao diện

- **Thanh trên cùng**: menu `File / View / Composition / Tools / Help`. Tiêu đề giữa là `<ten-project> / <id-composition-dang-chon>`.
- **Sidebar trái**:
  - Tab **Compositions** — liệt kê mọi `<Composition>` khai báo trong `src/Root.tsx`.
  - Tab **Assets** — liệt kê file trong `public/`. Nếu tab này rỗng và canvas chỉ toàn ô vuông xám-trắng caro, nghĩa là chưa có asset nào và component đang render `null` (chưa có gì để xuất).
- **Khung giữa**: canvas preview đúng khung hình đang tua tới, có thước pixel để canh chỉnh, nút `Reset zoom`.
- **Panel phải — tab Inspector**: metadata của composition đang chọn (Dimensions, Frame rate, Duration), lấy trực tiếp từ props trong `<Composition>`. Có link `Composition.tsx:<dòng>` để nhảy thẳng tới code tương ứng. Bên dưới là 4 nút thao tác **có tác dụng thật, tự chèn code hộ**:
  - `Add Solid` → chèn 1 layer màu nền
  - `Add asset...` → chọn file từ máy, tự copy vào `public/` và chèn sẵn `<Img>/<Video>/<Audio>` dùng file đó
  - `Add composition...` → tạo thêm 1 `<Composition>` (video output) khác trong `Root.tsx`
  - `Browse Elements...` → thư viện component mẫu có sẵn (text animation, transition...)
- **Panel phải — tab Renders**: lịch sử các lần bấm nút `Render`, tương đương chạy `npx remotion render`.
- **Thanh dưới cùng (playback bar)**: đồng hồ thời gian/số frame → nút tua đầu, lùi 1 frame, Play/Pause, tới 1 frame, cuối → icon lặp (loop), icon loa (mute) → `[` `]` đặt điểm in/out để chỉ preview 1 đoạn → icon fit-canvas, icon snap (bắt dính khung), fullscreen → nút `Render` (góc phải, mở modal chọn định dạng/tên file xuất).
- **Vùng track/timeline** (dải dưới cùng): mỗi `<Sequence>`, `<Video>`, `<Audio>`... trong code hiện thành 1 thanh kéo-giãn được ở đây, đồng bộ 2 chiều với code.

### Sửa Dimensions / Frame rate / Duration trực tiếp trên Inspector

Các số này **sửa được trực tiếp**, không hề bị khoá cứng:

1. Bấm thẳng vào con số (vd. `60` cạnh "Duration") → nó biến thành ô nhập liệu → gõ số mới → `Enter` để lưu.
2. Hoặc bấm-giữ-kéo ngang ngay trên con số (kiểu "input dragger") để tăng/giảm nhanh.
3. Hover vào tên trường (`Dimensions`, `Frame rate`) sẽ hiện nút chọn theo **preset** có sẵn (vd. 1080×1920, 1920×1080, 30/50/60fps...).

Mỗi lần sửa, Remotion tự động ghi đè đúng dòng props tương ứng trong `<Composition ... durationInFrames={...} fps={...} width={...} height={...} />` ở `Composition.tsx` — sửa tay trong code rồi lưu file cũng có tác dụng y hệt (hot reload 2 chiều).

> Ngoại lệ: nếu bạn viết logic thật trong hàm `calculateMetadata` (mặc định sinh sẵn, đang `return {}`) để **tự tính** một trong các giá trị trên (vd. lấy fps theo file audio import vào), thì đúng field đó sẽ chuyển màu xám mờ và **không cho sửa tay trên UI nữa** — vì lúc này giá trị do code tính ra chứ không phải hằng số cố định trong props.

### Dựng nội dung qua UI thay vì gõ tay

1. Bấm **Add asset...** → chọn video/ảnh/audio → Studio tự copy vào `public/` và chèn `<Video src={staticFile(...)} />` (hoặc `<Img>`/`<Audio>`) vào `MyComponent` → canvas hết trống, xuất hiện track trong timeline.
2. Kéo mép trái/phải của track trong timeline để đổi thời điểm bắt đầu/độ dài đoạn đó — tương đương sửa `from`/`durationInFrames` của `<Sequence>` bọc ngoài trong code.
3. Muốn thêm cảnh mới, thêm layer khác → tiếp tục `Add asset...`/`Add Solid`, hoặc gõ thẳng `<Sequence>` mới như mục 4 ở trên — cả hai cách tương đương, chỉ khác chỗ gõ.
4. Xong thì bấm **Render** ở góc dưới-phải playback bar (tương đương lệnh CLI ở mục 7 dưới đây).

## 7. Render ra file video hoàn chỉnh

```bash
npx remotion render MyComp out/demo.mp4
```

Đã render thử và xác nhận thành công:

```
Rendered 330/330
+ out/demo.mp4  6 MB
```

Kiểm tra lại bằng `ffprobe`: video `1280x720`, có cả track video lẫn audio, thời lượng `~11s` — khớp với 330 frame ở 30fps.

File `out/` bị `.gitignore` bỏ qua trong project Remotion (không commit video render ra), chỉ commit code trong `src/`.

## 8. Các lệnh hữu ích khác

```bash
npm run lint          # eslint + kiểm tra type TypeScript
npx remotion still MyComp out/thumbnail.png --frame=45   # xuất 1 frame thành ảnh tĩnh
npx remotion upgrade   # nâng cấp Remotion lên bản mới nhất
```

## 9. Tạo project lab mới khác

Lặp lại bước 2 với tên thư mục khác, ví dụ:

```bash
npx create-video@latest --yes --blank tmp/remotion_lab/tiktok-caption-demo
```

Mỗi thư mục con trong `tmp/remotion_lab/` là một project độc lập, có `package.json`/`node_modules` riêng — không ảnh hưởng lẫn nhau.

## Tài liệu tham khảo

- Docs chính thức: https://www.remotion.dev/docs
- Danh sách API (`Sequence`, `interpolate`, `spring`, `Audio`, `Video`...): https://www.remotion.dev/docs/api
- Template có sẵn: https://www.remotion.dev/templates
