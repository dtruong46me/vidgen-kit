import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { brushJA, minchoJA } from "./fonts";
import type { Intro as IntroData } from "./types";

/**
 * Màn mở đầu — chủ đề của ngày viết bằng nét bút lông, dưới là ngày tháng.
 *
 * Ba điều kiềm chế có chủ ý:
 *
 * 1. NỀN TĨNH, không clip. Người xem vừa lướt tới, mắt còn đang bắt nhịp; cho
 *    hình chuyển động ngay là bắt họ xử lý hai thứ cùng lúc. Nền tĩnh giữ mọi
 *    sự chú ý vào đúng mấy chữ.
 * 2. CHỮ VÀO CHẬM HƠN CAPTION. Caption vào trong 26 frame vì nó phải nhường
 *    chỗ cho câu sau; màn mở đầu không vội đi đâu cả nên vào trong 34 frame.
 * 3. NGÀY VÀO SAU TIÊU ĐỀ. Hai dòng hiện cùng lúc thì mắt không biết đọc dòng
 *    nào trước. Lệch nhau 14 frame là đủ để mắt tự đi từ trên xuống.
 */

/** Chữ trôi vào trong bao nhiêu frame. Chậm hơn caption (26) một cách có chủ ý. */
const TITLE_IN = 34;
/** Dòng ngày hiện sau tiêu đề bấy nhiêu frame. */
const DATE_DELAY = 14;

/**
 * Nền màn mở đầu — mực sumi loãng.
 *
 * Cùng tông với PALETTES trong Background.tsx nhưng tối hơn hẳn: màn mở đầu
 * không có clip nên không có lớp phủ tối, nền phải tự đủ tối để chữ trắng nổi.
 */
const INK = "radial-gradient(120% 90% at 50% 38%, #232a26 0%, #141917 45%, #0a0c0b 100%)";

export const Intro: React.FC<{
  data: IntroData;
  /** Số frame mờ dần ở cuối để nối sang cảnh đầu tiên. */
  fadeOutFrames: number;
}> = ({ data, fadeOutFrames }) => {
  const frame = useCurrentFrame();
  const d = data.durationInFrames;

  const enter = interpolate(frame, [0, TITLE_IN], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  const dateEnter = interpolate(
    frame,
    [DATE_DELAY, DATE_DELAY + TITLE_IN],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.inOut(Easing.cubic),
    },
  );

  // Cả màn mờ dần ở cuối, đúng bằng độ dài chuyển cảnh — để nó nối liền với
  // cảnh đầu tiên thay vì cắt phựt.
  const exit = interpolate(frame, [d - fadeOutFrames, d], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.quad),
  });

  // Nở ra rất nhẹ suốt cả màn: khung hình tĩnh hoàn toàn trông như ảnh đứng
  // hình, còn 2% là vừa đủ để mắt biết video vẫn đang chạy.
  const scale = interpolate(frame, [0, d], [1, 1.02], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: INK, opacity: exit }}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          transform: `scale(${scale})`,
        }}
      >
        <div style={{ textAlign: "center", padding: "0 120px" }}>
          {/* Chủ đề — nét bút lông, chữ to nhất trong cả video */}
          <div
            style={{
              opacity: enter,
              transform: `translateY(${interpolate(enter, [0, 1], [26, 0])}px)`,
              fontFamily: brushJA,
              color: "#f6efe2",
              fontSize: fitTitle(data.title.length),
              lineHeight: 1.45,
              letterSpacing: 6,
              textWrap: "balance",
              textShadow: "0 0 40px rgba(255,244,222,0.22), 0 8px 30px rgba(0,0,0,0.6)",
            }}
          >
            {data.title}
          </div>

          {/* Dòng ngày — chỉ hiện khi tên kịch bản là một ngày thật */}
          {data.dateText ? (
            <>
              <div
                style={{
                  opacity: dateEnter,
                  width: 84,
                  height: 1,
                  background: "rgba(246,239,226,0.4)",
                  margin: "44px auto",
                }}
              />
              <div
                style={{
                  opacity: dateEnter,
                  fontFamily: minchoJA,
                  color: "rgba(246,239,226,0.72)",
                  fontSize: 34,
                  fontWeight: 600,
                  letterSpacing: 8,
                }}
              >
                {data.dateText}
              </div>
            </>
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/**
 * Tiêu đề dài thì chữ nhỏ lại — cùng cách nghĩ với fitJa trong Caption.tsx,
 * nhưng mốc rộng rãi hơn vì màn mở đầu chừa lề 120px mỗi bên và không phải
 * nhường chỗ cho dòng nào khác.
 */
const fitTitle = (len: number) =>
  len <= 6 ? 108 : len <= 10 ? 88 : len <= 16 ? 68 : len <= 24 ? 54 : 44;
