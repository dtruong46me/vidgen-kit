/**
 * Kiểu dữ liệu của file content/<slug>.build.json — do pipeline/contract.py sinh ra.
 * Đây chính là "props" mà Remotion nhận vào để render.
 *
 * Mọi trường thêm vào từ BƯỚC 3 trở đi đều là TUỲ CHỌN hoặc có mặc định trung
 * tính, theo P-3: bản Remotion cũ phải render được build.json bản mới.
 */

export type Line = {
  /** Câu tiếng Nhật */
  ja: string;
  /** Cách đọc (romaji) */
  romaji: string;
  /** Cách đọc bằng hiragana. Có từ BƯỚC 3; chỉ hiện khi showHira bật */
  hira?: string;
  /** Nghĩa tiếng Việt */
  vi: string;
  /** Đường dẫn file giọng đọc, tính từ thư mục public/ */
  audio: string;
  /** Độ dài file giọng đọc, tính bằng frame */
  audioDurationInFrames: number;
  /** Tổng độ dài cảnh = lead-in + giọng đọc + khoảng lặng sau */
  durationInFrames: number;
  /** Giọng đọc bắt đầu ở frame thứ mấy trong cảnh */
  audioStartInFrames: number;
  /** Clip nền, tính từ public/. null = dùng nền gradient */
  clip: string | null;
  /** Độ dài clip nền tính bằng frame (để loop khi clip ngắn hơn cảnh) */
  clipDurationInFrames: number | null;
  /** Cắt clip từ giây thứ mấy */
  clipStartInSeconds: number;
};

/** Màn mở đầu. null = không có, và đó là mặc định. */
export type Intro = {
  /** Chủ đề của ngày, viết bằng nét bút lông */
  title: string;
  /** Ngày kiểu Nhật kèm thứ, vd. 八月二十日　木曜日. Rỗng nếu tên kịch bản không phải ngày */
  dateText: string;
  durationInFrames: number;
};

/** Màn kết. null = không có. */
export type Outro = {
  text: string;
  durationInFrames: number;
};

/**
 * Kiểu chuyển cảnh.
 *   crossfade    — cảnh sau mờ chồng lên cuối cảnh trước (mặc định, có từ trước BƯỚC 5)
 *   dip_to_black — cảnh trước tối hẳn rồi cảnh sau mới sáng lên
 *   cut          — cắt thẳng, không hiệu ứng
 */
export type Transition = "crossfade" | "dip_to_black" | "cut";

export type DailyVideoProps = {
  id: string;
  title: string;
  fps: number;
  width: number;
  height: number;
  /** Nhạc nền, tính từ public/. null = không có nhạc nền */
  bgm: string | null;
  /** Độ dài file nhạc nền (frame), dùng để loop cho đủ video */
  bgmDurationInFrames: number | null;
  bgmVolume: number;
  /** BƯỚC 5 — cả bốn trường dưới đây đều tuỳ chọn */
  intro?: Intro | null;
  outro?: Outro | null;
  transition?: Transition;
  transitionInFrames?: number;
  /** Hiện dòng hiragana dưới romaji. Mặc định tắt */
  showHira?: boolean;
  lines: Line[];
};
