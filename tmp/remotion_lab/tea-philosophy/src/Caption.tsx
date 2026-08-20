import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { serifJP } from "./fonts";
import type { Line } from "./types";

const IN_FRAMES = 14;
const OUT_FRAMES = 10;

/**
 * Câu càng dài thì chữ càng nhỏ lại, để khối caption không bao giờ tràn khung
 * hay đẩy nhau lệch bố cục giữa các cảnh. Câu dài/ngắn bao nhiêu cũng an toàn.
 */
const fitJa = (len: number) =>
  len <= 14 ? 66 : len <= 22 ? 58 : len <= 32 ? 50 : len <= 44 ? 44 : 38;

const fitVi = (len: number) =>
  len <= 30 ? 42 : len <= 55 ? 38 : len <= 85 ? 34 : 30;

export const Caption: React.FC<{ line: Line }> = ({ line }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const d = line.durationInFrames;

  // Hiện lên: mờ dần vào + trượt lên nhẹ (spring cho mượt, không bị "cứng")
  const enter = spring({
    frame,
    fps,
    config: { damping: 200 },
    durationInFrames: IN_FRAMES,
  });

  // Tắt đi ở cuối cảnh để chữ không đè lên câu tiếp theo lúc chuyển cảnh
  const exit = interpolate(frame, [d - OUT_FRAMES, d], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const opacity = enter * exit;
  const translateY = interpolate(enter, [0, 1], [26, 0]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "0 90px",
      }}
    >
      <div
        style={{
          opacity,
          transform: `translateY(${translateY}px)`,
          fontFamily: serifJP,
          textAlign: "center",
          textShadow: "0 4px 24px rgba(0,0,0,0.85)",
        }}
      >
        {/* Câu tiếng Nhật — chữ chính, to nhất */}
        <div
          style={{
            color: "#ffffff",
            fontSize: fitJa(line.ja.length),
            fontWeight: 600,
            lineHeight: 1.55,
            letterSpacing: 1,
          }}
        >
          {line.ja}
        </div>

        {/* Cách đọc — chữ nhỏ, mờ, để người mới đọc theo được */}
        {line.romaji ? (
          <div
            style={{
              color: "rgba(255,255,255,0.62)",
              fontSize: 30,
              fontWeight: 400,
              fontStyle: "italic",
              lineHeight: 1.5,
              marginTop: 22,
              letterSpacing: 0.5,
            }}
          >
            {line.romaji}
          </div>
        ) : null}

        {/* Gạch ngăn giữa phần tiếng Nhật và phần tiếng Việt */}
        <div
          style={{
            width: 120,
            height: 1,
            background: "rgba(255,255,255,0.35)",
            margin: "34px auto",
          }}
        />

        {/* Nghĩa tiếng Việt */}
        <div
          style={{
            color: "#f2e9dc",
            fontSize: fitVi(line.vi.length),
            fontWeight: 400,
            lineHeight: 1.55,
          }}
        >
          {line.vi}
        </div>
      </div>
    </AbsoluteFill>
  );
};
