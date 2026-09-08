import { CalculateMetadataFunction, Composition } from "remotion";
import { DailyVideo } from "./DailyVideo";
import type { DailyVideoProps } from "./types";

/**
 * Tính metadata từ chính dữ liệu đầu vào thay vì gõ số cứng.
 *
 * Nhờ hàm này mà độ dài video luôn khớp tổng độ dài giọng đọc:
 * thêm/bớt/sửa 1 câu -> chạy lại `make content` -> video tự dài/ngắn theo,
 * không phải chỉnh tay durationInFrames lần nào.
 *
 * Đổi lại, 4 ô Dimensions / Frame rate / Duration trong Remotion Studio sẽ
 * chuyển sang màu xám và không sửa được bằng chuột nữa — vì giá trị do code
 * tính ra chứ không còn là hằng số trong props.
 */
const calculateMetadata: CalculateMetadataFunction<DailyVideoProps> = ({
  props,
}) => {
  const total = props.lines.reduce((sum, l) => sum + l.durationInFrames, 0);

  return {
    durationInFrames: total,
    fps: props.fps,
    width: props.width,
    height: props.height,
  };
};

/**
 * Props mặc định — CHỈ để Remotion Studio có gì đó mà mở.
 *
 * Cố tình viết thẳng vào code chứ không trỏ vào file: mọi file build.json đều
 * do máy sinh và không được commit, nên clone mới sẽ không có file nào để đọc.
 * Không audio, không clip — cảnh rơi về nền gradient, đúng như một câu chưa
 * chọn được cảnh quay.
 *
 * Lúc render thật, `--props=../content/<ngày>.build.json` ghi đè toàn bộ chỗ này.
 */
const PLACEHOLDER: DailyVideoProps = {
  id: "preview",
  title: "Xem trước",
  fps: 30,
  width: 1080,
  height: 1920,
  bgm: null,
  bgmDurationInFrames: null,
  bgmVolume: 0.12,
  lines: [
    {
      ja: "静かな朝。",
      romaji: "Shizuka na asa.",
      vi: "Một buổi sáng tĩnh lặng.",
      audio: "",
      audioDurationInFrames: 0,
      durationInFrames: 120,
      audioStartInFrames: 0,
      clip: null,
      clipDurationInFrames: null,
      clipStartInSeconds: 0,
    },
  ],
};

export const MyComposition = () => {
  return (
    <Composition
      id="Daily"
      component={DailyVideo}
      calculateMetadata={calculateMetadata}
      defaultProps={PLACEHOLDER}
      // Các số dưới đây chỉ là giá trị tạm; calculateMetadata sẽ ghi đè hết
      durationInFrames={1}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};
