import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { minchoJA, sansLatin } from "./fonts";
import type { Line } from "./types";

const IN_FRAMES = 14;
const OUT_FRAMES = 10;

/**
 * Vùng an toàn — xem CLAUDE.md.
 *
 * TikTok/Reels dán tên tài khoản, mô tả và thanh nhạc lên khoảng 350 px đáy
 * màn hình. Caption neo vào ĐÁY khối an toàn này chứ không neo giữa màn hình:
 * khối chữ cao hay thấp thì cũng nở lên trên, không bao giờ thò xuống vùng bị che.
 *
 * Với 1920 px chiều cao, khối caption kết thúc ở y = 1520 và thường bắt đầu
 * quanh y = 1050 — tức tâm chữ rơi vào khoảng 2/3 dưới, đúng chỗ mắt người xem
 * dừng lại khi lướt dọc.
 */
const SAFE_BOTTOM = 400;

/**
 * Dải icon bên phải (tim, bình luận, chia sẻ) rộng khoảng 130 px. Đệm đều hai
 * bên để chữ vẫn cân giữa khung, chỉ hẹp lại vừa đủ tránh dải đó.
 */
const SAFE_SIDE = 110;

/**
 * Câu càng dài thì chữ càng nhỏ lại, để khối caption không bao giờ tràn khung
 * hay đẩy nhau lệch bố cục giữa các cảnh. Câu dài/ngắn bao nhiêu cũng an toàn.
 *
 * Các mốc dưới đây tính theo bề ngang dùng được là 1080 - 2*SAFE_SIDE = 860 px.
 * Đổi SAFE_SIDE thì phải tính lại các mốc này.
 */
const fitJa = (len: number) =>
  len <= 13 ? 62 : len <= 21 ? 55 : len <= 30 ? 48 : len <= 42 ? 42 : 36;

const fitVi = (len: number) =>
  len <= 28 ? 42 : len <= 52 ? 38 : len <= 80 ? 34 : 30;

/**
 * Chia chữ thành các dòng dài gần bằng nhau thay vì nhồi đầy dòng trên rồi bỏ
 * một chữ lẻ loi xuống dòng dưới. Không có nó, câu 16 ký tự bị cắt thành
 * 15 + 1 — dòng dưới trơ trọi mỗi chữ "た。".
 */
const BALANCED = { textWrap: "balance" } as const;

/**
 * Quầng sáng dịu, không phải neon.
 *
 * Ba lớp bóng chồng nhau, đọc từ trong ra ngoài:
 *   1. quầng ấm sát chữ    -> tạo cảm giác chữ tự phát sáng
 *   2. quầng ấm tán rộng   -> làm mềm rìa, tách chữ khỏi nền
 *   3. bóng tối đổ xuống   -> giữ chữ đọc được khi nền là cảnh sáng
 *
 * Lớp 3 mới là lớp lo phần dễ đọc; hai lớp trên chỉ lo phần cảm xúc. Bỏ lớp 3
 * là chữ trắng sẽ chìm mất trên nền trời hoặc nền tuyết.
 */
const SOFT_GLOW = [
  "0 0 18px rgba(255,248,235,0.30)",
  "0 0 46px rgba(255,244,220,0.16)",
  "0 6px 28px rgba(0,0,0,0.72)",
].join(", ");

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
        justifyContent: "flex-end",
        alignItems: "center",
        padding: `0 ${SAFE_SIDE}px ${SAFE_BOTTOM}px`,
      }}
    >
      <div
        style={{
          opacity,
          transform: `translateY(${translateY}px)`,
          textAlign: "center",
          textShadow: SOFT_GLOW,
        }}
      >
        {/* Câu tiếng Nhật — chữ chính, to nhất */}
        <div
          style={{
            ...BALANCED,
            fontFamily: minchoJA,
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
              fontFamily: sansLatin,
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
            ...BALANCED,
            fontFamily: sansLatin,
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
