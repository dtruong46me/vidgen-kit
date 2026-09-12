import {
  AbsoluteFill,
  interpolate,
  Loop,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Line, Transition } from "./types";

/** Bảng màu nền dùng khi 1 câu chưa có clip quay — tông trầm kiểu trà đạo. */
const PALETTES = [
  ["#1b2a24", "#3f5d4e"], // rêu
  ["#241f1a", "#5a4632"], // đất nung
  ["#1a1f26", "#3c4a5c"], // tro xanh
  ["#2a221f", "#6b4f3a"], // gỗ
  ["#161a17", "#37453a"], // sumi
  ["#231d24", "#54415a"], // tử đằng
  ["#1d2422", "#456156"], // matcha
  ["#26201c", "#6a5140"], // hoàng thổ
  ["#191d1f", "#3d5157"], // sương sớm
];

/**
 * Ba kiểu chuyển cảnh, khác nhau ở CHỖ NÀO trong thời gian chứ không chỉ ở
 * hiệu ứng — nên phải đọc cùng với DailyVideo.tsx, nơi quyết định mỗi cảnh bắt
 * đầu ở frame nào:
 *
 *   crossfade    cảnh này bắt đầu SỚM hơn T frame và sáng dần lên, chồng lên
 *                cuối cảnh trước. Không cảnh nào tối đi. Đây là kiểu êm nhất
 *                và là mặc định.
 *   dip_to_black cảnh nằm đúng ô của nó, sáng lên trong T/2 đầu và tối đi trong
 *                T/2 cuối. Giữa hai cảnh có một khoảnh khắc đen thật sự.
 *   cut          cắt thẳng, không frame nào dành cho hiệu ứng.
 *
 * Vì sao chia đôi T ở dip_to_black: hai nửa cộng lại đúng bằng T, nên đổi kiểu
 * chuyển cảnh không làm đổi cảm giác về nhịp — chỉ đổi cách nối.
 */
const opacityFor = (
  mode: Transition,
  frame: number,
  index: number,
  fadeFrames: number,
  windowFrames: number,
) => {
  if (mode === "cut") return 1;

  if (mode === "dip_to_black") {
    const half = Math.max(1, Math.round(fadeFrames / 2));
    return (
      interpolate(frame, [0, half], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      }) *
      interpolate(frame, [windowFrames - half, windowFrames], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    );
  }

  // crossfade — cảnh đầu tiên không fade từ màu đen ra: nó chính là khung hình
  // đầu video, cũng là ảnh bìa lúc người xem lướt tới, nên phải có hình ngay từ
  // frame 0. Các cảnh sau fade chồng lên cảnh trước.
  if (index === 0) return 1;
  return interpolate(frame, [0, fadeFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
};

export const Background: React.FC<{
  line: Line;
  index: number;
  /** Số frame dành cho hiệu ứng chuyển cảnh */
  fadeInFrames: number;
  /** Kiểu chuyển cảnh. Không truyền thì crossfade, đúng hành vi trước BƯỚC 5 */
  mode?: Transition;
  /** Độ dài THẬT của Sequence bọc ngoài — crossfade dài hơn cảnh đúng T frame */
  windowFrames?: number;
}> = ({ line, index, fadeInFrames, mode = "crossfade", windowFrames }) => {
  const frame = useCurrentFrame();
  const window = windowFrames ?? line.durationInFrames;

  const opacity = opacityFor(mode, frame, index, fadeInFrames, window);

  // Ken Burns: phóng to rất chậm để khung hình không bị "chết"
  const scale = interpolate(frame, [0, window], [1.06, 1.14], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const [from, to] = PALETTES[index % PALETTES.length];

  return (
    <AbsoluteFill style={{ opacity }}>
      <AbsoluteFill style={{ transform: `scale(${scale})` }}>
        {line.clip ? (
          <ClipLayer line={line} />
        ) : (
          <AbsoluteFill
            style={{
              background: `linear-gradient(160deg, ${from} 0%, ${to} 100%)`,
            }}
          />
        )}
      </AbsoluteFill>

      {/*
        Lớp phủ tối — NHẸ TAY. Nó chỉ nâng tông, không gánh việc giữ chữ đọc được.

        Bản trước phủ 34–88% cả khung, đậm nhất ở dải caption. Chữ thì đọc được,
        nhưng video nào cũng xỉn như trời sắp tối — kể cả những lúc KHÔNG có
        chữ nào trên hình. Giờ việc giữ chữ đọc được giao cho chính lớp chữ:
        quầng tối đi theo khối caption (CAPTION_SCRIM trong Caption.tsx) và
        quầng tối sau tiêu đề (TitleCard.tsx). Hai quầng đó hiện cùng chữ, tắt
        cùng chữ, nên giữa hai câu clip sáng trọn vẹn.

        Lớp này chỉ còn hai việc: đỉnh khung hơi tối cho thanh trạng thái điện
        thoại khỏi lẫn vào hình, và đáy tối dần vì TikTok/Reels dán tên tài
        khoản với mô tả ở đó — chữ trắng của họ cũng cần nền.

        Muốn chữ rõ hơn thì đậm quầng hoặc viền chữ, ĐỪNG đậm lại lớp này.

        Nền gradient vốn đã tối sẵn -> phủ nhẹ thôi kẻo thành đen kịt.
      */}
      <AbsoluteFill
        style={{
          background: line.clip
            ? "linear-gradient(180deg, rgba(0,0,0,0.22) 0%, rgba(0,0,0,0.06) 16%, rgba(0,0,0,0.04) 40%, rgba(0,0,0,0.14) 56%, rgba(0,0,0,0.28) 74%, rgba(0,0,0,0.42) 100%)"
            : "linear-gradient(180deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.05) 45%, rgba(0,0,0,0.35) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

/**
 * Clip đậm màu hơn bản gốc một chút. Clip Pexels thường quay màu phẳng, hơi
 * xám; lớp phủ đậm cũ giấu được chuyện đó, phủ nhẹ rồi thì lộ ra nhạt. 8% là
 * vừa để hoa ra hồng, lá ra xanh mà da người chưa ngả cam.
 */
const CLIP_FILTER = "saturate(1.08)";

const ClipLayer: React.FC<{ line: Line }> = ({ line }) => {
  const { fps } = useVideoConfig();

  const video = (
    <OffthreadVideo
      src={staticFile(line.clip as string)}
      trimBefore={Math.round(line.clipStartInSeconds * fps)}
      muted
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        filter: CLIP_FILTER,
      }}
    />
  );

  // Clip ngắn hơn cảnh thì cho chạy lặp lại thay vì để màn hình đen
  if (
    line.clipDurationInFrames &&
    line.clipDurationInFrames < line.durationInFrames
  ) {
    return (
      <Loop durationInFrames={line.clipDurationInFrames}>{video}</Loop>
    );
  }

  return video;
};
