import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { brushJA } from "./fonts";
import type { Outro as OutroData } from "./types";

/**
 * Màn kết — một câu chào, rồi tối dần.
 *
 * Ngắn hơn màn mở đầu và chỉ có một dòng. Lý do: người xem đã nhận được thứ họ
 * đến để nhận: kéo dài phần kết chỉ tạo cơ hội cho họ lướt đi trước khi video
 * hết, mà lướt đi sớm thì thuật toán hiểu là video dở.
 *
 * Nền tối dần về đen tuyệt đối ở frame cuối. Video kết thúc bằng màn hình đen
 * chứ không phải bằng một khung hình đứng — khác biệt nhỏ nhưng là khác biệt
 * giữa "hết rồi" và "đơ máy".
 */

const IN_FRAMES = 30;

export const Outro: React.FC<{ data: OutroData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const d = data.durationInFrames;

  const enter = interpolate(frame, [0, IN_FRAMES], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  // Chữ bắt đầu nhạt đi từ 55% màn, tắt hẳn trước khi hết — để khung cuối cùng
  // là màn đen sạch, không còn vệt chữ mờ.
  const fade = interpolate(frame, [d * 0.55, d * 0.92], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.quad),
  });

  // Nền tối dần cùng nhịp, chậm hơn chữ một chút.
  const ground = interpolate(frame, [0, d], [0.09, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: `rgb(${Math.round(ground * 255)}, ${Math.round(
          ground * 275,
        )}, ${Math.round(ground * 258)})`,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          opacity: enter * fade,
          transform: `translateY(${interpolate(enter, [0, 1], [20, 0])}px)`,
          fontFamily: brushJA,
          color: "#f6efe2",
          fontSize: 76,
          letterSpacing: 10,
          textShadow: "0 0 38px rgba(255,244,222,0.2)",
        }}
      >
        {data.text}
      </div>
    </AbsoluteFill>
  );
};
