import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { brushJA } from "./fonts";
import type { TitleCard as TitleCardData } from "./types";

/**
 * Tiêu đề đầu video — ngày tháng viết nét bút lông, đè lên cảnh 1.
 *
 * Thay cho màn mở đầu nền gradient cũ. Video giờ vào thẳng hình thật từ frame
 * đầu tiên: khung đầu cũng là ảnh bìa người xem thấy khi lướt tới, một nền mực
 * trống ở đó là phí mất lần duy nhất được chú ý.
 *
 * Ba điều kiềm chế có chủ ý:
 *
 * 1. ĐẶT Ở 1/3 TRÊN, không ở giữa. Caption neo ở 2/3 dưới; tiêu đề ở giữa khung
 *    thì hai khối chữ dính vào nhau thành một mảng.
 * 2. CHỮ VÀO CHẬM HƠN CAPTION. Caption vào trong 26 frame vì phải nhường chỗ
 *    cho câu sau; tiêu đề không vội đi đâu nên vào trong 34 frame. Caption câu 1
 *    cũng chờ tiêu đề hiện xong mới vào — `captionStartInFrames`, timeline.py tính.
 * 3. CHỦ ĐỀ VÀO SAU NGÀY. Hai dòng hiện cùng lúc thì mắt không biết đọc dòng
 *    nào trước. Lệch nhau 14 frame là đủ để mắt tự đi từ trên xuống.
 */

/** Chữ trôi vào trong bao nhiêu frame. Chậm hơn caption (26) một cách có chủ ý. */
const TITLE_IN = 34;
/** Dòng chủ đề hiện sau dòng ngày bấy nhiêu frame. */
const SUBTITLE_DELAY = 14;
/** Tâm dòng ngày nằm ở 1/3 chiều cao khung hình, tính từ trên xuống. */
const TITLE_CENTER = 1 / 3;
const TITLE_LINE_HEIGHT = 1.3;
/** Lề hai bên — rộng hơn SAFE_SIDE của caption một chút, tiêu đề cần thở. */
const SIDE = 120;

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const TitleCard: React.FC<{
  data: TitleCardData;
  /** Độ dài cảnh 1 — tiêu đề sống đúng bằng cảnh đó. */
  durationInFrames: number;
  /** Số frame mờ đi ở cuối, đúng bằng độ dài chuyển cảnh sang cảnh 2. */
  fadeOutFrames: number;
}> = ({ data, durationInFrames, fadeOutFrames }) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const d = durationInFrames;

  const enter = interpolate(frame, [0, TITLE_IN], [0, 1], {
    ...CLAMP,
    easing: Easing.inOut(Easing.cubic),
  });
  const subtitleEnter = interpolate(
    frame,
    [SUBTITLE_DELAY, SUBTITLE_DELAY + TITLE_IN],
    [0, 1],
    { ...CLAMP, easing: Easing.inOut(Easing.cubic) },
  );
  // Mờ đi đúng quãng cảnh 2 đang chồng vào, để tiêu đề không nán lại trên hình
  // của câu sau.
  const exit = interpolate(frame, [d - fadeOutFrames, d], [1, 0], {
    ...CLAMP,
    easing: Easing.inOut(Easing.quad),
  });

  const size = fitTitle(visualLength(data.title));
  // Neo TÂM dòng ngày vào 1/3, không neo mép trên — cỡ chữ đổi thì tâm vẫn đứng yên.
  const top = height * TITLE_CENTER - (size * TITLE_LINE_HEIGHT) / 2;

  return (
    <AbsoluteFill style={{ opacity: exit }}>
      {/*
        Quầng tối sau chữ. Lớp phủ của Background cố tình nhạt nhất ở dải 1/3
        trên — đó là phần khán giả xem hình — nên chữ trắng đặt ở đây dễ chìm
        vào clip sáng. Tiêu đề tự mang một quầng tối riêng, hiện và tắt cùng chữ,
        thay vì phủ đậm cả khung cho mọi cảnh.
      */}
      <AbsoluteFill
        style={{
          opacity: enter,
          background: `radial-gradient(75% 18% at 50% ${TITLE_CENTER * 100 + 3}%, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0.22) 55%, rgba(0,0,0,0) 100%)`,
        }}
      />

      <div
        style={{
          position: "absolute",
          top,
          left: 0,
          right: 0,
          padding: `0 ${SIDE}px`,
          textAlign: "center",
        }}
      >
        {/* Ngày tháng — chữ to nhất trong cả video */}
        <div
          style={{
            opacity: enter,
            transform: `translateY(${interpolate(enter, [0, 1], [26, 0])}px)`,
            fontFamily: brushJA,
            color: "#f6efe2",
            fontSize: size,
            lineHeight: TITLE_LINE_HEIGHT,
            letterSpacing: 6,
            textWrap: "balance",
            textShadow:
              "0 0 40px rgba(255,244,222,0.22), 0 6px 30px rgba(0,0,0,0.75)",
          }}
        >
          {data.title}
        </div>

        {/* Chủ đề của ngày — chỉ hiện khi tiêu đề là ngày thật */}
        {data.subtitle ? (
          <>
            <div
              style={{
                opacity: subtitleEnter,
                width: 84,
                height: 1,
                background: "rgba(246,239,226,0.5)",
                margin: "30px auto",
              }}
            />
            <div
              style={{
                opacity: subtitleEnter,
                fontFamily: brushJA,
                color: "rgba(246,239,226,0.88)",
                fontSize: 54,
                lineHeight: 1.4,
                letterSpacing: 6,
                textShadow: "0 4px 22px rgba(0,0,0,0.75)",
              }}
            >
              {data.subtitle}
            </div>
          </>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

/**
 * Bề ngang ước lượng theo số "ô chữ": chữ Nhật chiếm một ô, chữ số và chữ Latin
 * chừng nửa ô. Đếm ký tự trần thì 8月20日 (6) và 10月10日 (7) rơi vào hai cỡ chữ
 * khác nhau, và tiêu đề sẽ to nhỏ thất thường theo ngày.
 */
const visualLength = (text: string) =>
  [...text].reduce((n, ch) => n + (ch.charCodeAt(0) < 0x2000 ? 0.55 : 1), 0);

/**
 * Tiêu đề dài thì chữ nhỏ lại. Mọi ngày trong năm (dài nhất 12月31日 = 4,2 ô)
 * đều nằm ở mốc đầu, nên dòng ngày luôn cùng một cỡ. Các mốc sau dành cho kịch
 * bản không đặt tên theo ngày, khi chủ đề lên làm tiêu đề.
 */
const fitTitle = (len: number) =>
  len <= 6.5 ? 132 : len <= 10 ? 96 : len <= 16 ? 72 : len <= 24 ? 56 : 44;
