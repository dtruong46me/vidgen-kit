import { CalculateMetadataFunction, Composition } from "remotion";
import buildData from "../content/2026-08-20.build.json";
import { DailyVideo } from "./DailyVideo";
import type { DailyVideoProps } from "./types";

/**
 * Tính metadata từ chính dữ liệu đầu vào thay vì gõ số cứng.
 *
 * Nhờ hàm này mà độ dài video luôn khớp tổng độ dài giọng đọc:
 * thêm/bớt/sửa 1 câu -> chạy lại scripts/build.py -> video tự dài/ngắn theo,
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

export const MyComposition = () => {
  return (
    <Composition
      id="Daily"
      component={DailyVideo}
      calculateMetadata={calculateMetadata}
      defaultProps={buildData as DailyVideoProps}
      // Các số dưới đây chỉ là giá trị tạm; calculateMetadata sẽ ghi đè hết
      durationInFrames={1}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};
