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
        Clip quay thật thường sáng và nhiều chi tiết -> cần phủ đậm;
        nền gradient vốn đã tối sẵn -> phủ nhẹ thôi kẻo thành đen kịt.
      */}
      <AbsoluteFill
        style={{
          background: line.clip
            ? "linear-gradient(180deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.45) 40%, rgba(0,0,0,0.45) 60%, rgba(0,0,0,0.8) 100%)"
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
