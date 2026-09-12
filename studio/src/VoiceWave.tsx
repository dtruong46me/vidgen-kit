import { useAudioData, visualizeAudio } from "@remotion/media-utils";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { TITLE_CENTER } from "./TitleCard";
import type { Line } from "./types";

/**
 * Sóng giọng đọc — hàng vạch nhỏ ngay trên tiêu đề, nhảy theo đúng giọng đang đọc.
 *
 * Đọc từ CHÍNH file giọng của câu, không phải nhạc nền: nó chỉ động khi có
 * người nói, nghỉ giữa câu thì phẳng thành một hàng chấm. Người xem tắt tiếng
 * vẫn biết video đang có lời.
 *
 * Ba lựa chọn có chủ ý:
 *
 * 1. ĐỐI XỨNG QUANH TÂM. Dải tần thấp — nơi giọng người dồn năng lượng — nằm
 *    giữa, dải cao toả ra hai bên, nên sóng tự cao ở giữa và thấp dần ra mép.
 * 2. LÀM MƯỢT giữa các frame (`smoothing`). Không làm mượt thì vạch giật từng
 *    frame một, trái hẳn nhịp thong thả của cả video.
 * 3. MỖI CÂU MỘT BẢN, CÙNG MỘT HÌNH HỌC. Sóng nằm trong Sequence của từng câu
 *    nên chỉ phải giải mã đúng một file mp3; các câu nối liền nhau và vẽ ở cùng
 *    vị trí, nên mắt thấy một hàng sóng liền mạch suốt video.
 *
 * Không có trường nào trong hợp đồng cho lớp này: `audio`, `audioStartInFrames`
 * và `audioDurationInFrames` đã có sẵn trong build.json.
 */

/** Số dải tần FFT. Phải là luỹ thừa của 2; 128 dải ~172 Hz một dải ở 44,1 kHz. */
const SAMPLES = 128;
/** Chỉ lấy 24 dải đầu (tới ~4 kHz): giọng nói nằm gần hết ở đó, phần trên luôn phẳng. */
const BANDS = 24;
/** Chấm đứng yên ở mỗi đầu, kéo dài hàng sóng như một đường kẻ chấm. */
const TAIL_DOTS = 6;

const BAR_WIDTH = 4;
const BAR_GAP = 6;
/** Vạch thấp nhất là một chấm tròn. */
const MIN_HEIGHT = BAR_WIDTH;
const MAX_HEIGHT = 72;
/** Tâm hàng sóng nằm cao hơn tâm dòng ngày bấy nhiêu px. */
const ABOVE_TITLE = 170;

/** Hiện dần cùng nhịp tiêu đề (34 frame), tắt cùng nhịp caption (20 frame). */
const FADE_IN = 34;
const FADE_OUT = 20;

/**
 * Biên độ FFT của giọng nói rất nhỏ và dồn về vài dải đầu. Căn bậc hai kéo các
 * dải yếu lên để sóng có dáng, GAIN đưa giọng bình thường tới khoảng 2/3 chiều
 * cao — chừa chỗ cho chỗ nhấn giọng.
 */
const GAIN = 2.2;

export const VoiceWave: React.FC<{
  line: Line;
  /** Câu đầu tiên: hiện dần từ trong suốt, cùng lúc với tiêu đề. */
  fadeIn: boolean;
  /** Câu cuối cùng: tắt đi trước khi màn kết vào. */
  fadeOut: boolean;
}> = ({ line, fadeIn, fadeOut }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const audioData = useAudioData(staticFile(line.audio));
  const d = line.durationInFrames;

  // Frame tính trong file giọng đọc. Ngoài quãng có tiếng (leadIn, pauseAfter)
  // thì mọi dải bằng 0 — sóng nằm phẳng thành hàng chấm.
  const audioFrame = frame - line.audioStartInFrames;
  const speaking =
    audioData !== null &&
    audioFrame >= 0 &&
    audioFrame < line.audioDurationInFrames - 1;
  const spectrum = speaking
    ? visualizeAudio({
        audioData,
        fps,
        frame: audioFrame,
        numberOfSamples: SAMPLES,
        smoothing: true,
      }).slice(0, BANDS)
    : new Array<number>(BANDS).fill(0);

  // Dải thấp ở giữa, dải cao ra mép: [23 … 1 0 | 0 1 … 23]. Thêm một đường bao
  // hạ dần về hai đầu để mép sóng không bao giờ cao ngang giữa.
  const half = spectrum.map((v, i) => {
    const taper = 0.4 + 0.6 * Math.cos(((i / (BANDS - 1)) * Math.PI) / 2);
    const level = Math.min(1, Math.sqrt(v) * GAIN) * taper;
    return MIN_HEIGHT + (MAX_HEIGHT - MIN_HEIGHT) * level;
  });
  const tail = new Array<number>(TAIL_DOTS).fill(MIN_HEIGHT);
  const bars = [...tail, ...[...half].reverse(), ...half, ...tail];

  const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
  const opacity =
    (fadeIn
      ? interpolate(frame, [0, FADE_IN], [0, 1], {
          ...clamp,
          easing: Easing.inOut(Easing.cubic),
        })
      : 1) *
    (fadeOut
      ? interpolate(frame, [d - FADE_OUT, d], [1, 0], {
          ...clamp,
          easing: Easing.inOut(Easing.quad),
        })
      : 1);

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: height * TITLE_CENTER - ABOVE_TITLE - MAX_HEIGHT / 2,
          left: 0,
          right: 0,
          height: MAX_HEIGHT,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: BAR_GAP,
          opacity,
          // Viền tối sát vạch trước, bóng tán sau — vạch 4px trắng trên nền
          // sáng (lớp phủ giờ rất nhẹ) mà chỉ có bóng tán thì nhoè mất.
          filter:
            "drop-shadow(0 0 2px rgba(0,0,0,0.5)) drop-shadow(0 2px 10px rgba(0,0,0,0.55))",
        }}
      >
        {bars.map((h, i) => (
          <div
            key={i}
            style={{
              width: BAR_WIDTH,
              height: h,
              borderRadius: BAR_WIDTH / 2,
              background: "rgba(246,239,226,0.9)",
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};
