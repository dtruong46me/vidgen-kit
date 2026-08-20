/**
 * Kiểu dữ liệu của file content/<slug>.build.json — do scripts/build.py sinh ra.
 * Đây chính là "props" mà Remotion nhận vào để render.
 */

export type Line = {
  /** Câu tiếng Nhật */
  ja: string;
  /** Cách đọc (romaji) */
  romaji: string;
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
  lines: Line[];
};
