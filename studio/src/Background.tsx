import {
  AbsoluteFill,
  interpolate,
  Loop,
  OffthreadVideo,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Line } from "./types";

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

export const Background: React.FC<{
  line: Line;
  index: number;
  /** Số frame fade-in — chính là hiệu ứng chuyển cảnh mờ chồng */
  fadeInFrames: number;
}> = ({ line, index, fadeInFrames }) => {
  const frame = useCurrentFrame();

  // Cảnh đầu tiên không fade từ màu đen ra, các cảnh sau fade chồng lên cảnh trước
  const opacity =
    index === 0
      ? 1
      : interpolate(frame, [0, fadeInFrames], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

  // Ken Burns: phóng to rất chậm để khung hình không bị "chết"
  const scale = interpolate(
    frame,
    [0, line.durationInFrames + fadeInFrames],
    [1.06, 1.14],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

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
        Lớp phủ tối để caption luôn đọc được.

        Caption neo ở 2/3 dưới (xem SAFE_BOTTOM trong Caption.tsx), nên lớp phủ
        phải ĐẬM NHẤT Ở DƯỚI chứ không phải đậm đều. Bản đầu phủ nhạt nhất đúng
        ở giữa khung, mà đó lại là chỗ chữ bắt đầu — chữ Việt nằm trên chiếu tre
        sáng gần như chìm mất.

        Nửa trên vẫn để nhẹ tay: đó là phần khán giả xem hình, phủ đậm là phí clip.

        Nền gradient vốn đã tối sẵn -> phủ nhẹ thôi kẻo thành đen kịt.
      */}
      <AbsoluteFill
        style={{
          background: line.clip
            ? "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.34) 28%, rgba(0,0,0,0.52) 50%, rgba(0,0,0,0.78) 70%, rgba(0,0,0,0.88) 100%)"
            : "linear-gradient(180deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.05) 45%, rgba(0,0,0,0.35) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

const ClipLayer: React.FC<{ line: Line }> = ({ line }) => {
  const { fps } = useVideoConfig();

  const video = (
    <OffthreadVideo
      src={staticFile(line.clip as string)}
      trimBefore={Math.round(line.clipStartInSeconds * fps)}
      muted
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
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
