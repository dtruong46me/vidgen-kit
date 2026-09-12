/**
 * Kiểu dữ liệu của file content/<slug>/build.json — do pipeline/contract.py sinh ra.
 * Đây chính là "props" mà Remotion nhận vào để render.
 *
 * Mọi trường thêm vào từ BƯỚC 3 trở đi đều là TUỲ CHỌN hoặc có mặc định trung
 * tính, theo P-3: bản Remotion cũ phải render được build.json bản mới.
 */

/**
 * Một MẢNH caption bên trong một cảnh.
 *
 * Câu dài không được bóp chữ nhỏ lại cho vừa khung nữa; nó được `pipeline/phrase.py`
 * cắt thành mấy mảnh hiện nối tiếp nhau. Mảnh KHÔNG phải cảnh: vẫn một clip nền,
 * vẫn một file giọng đọc, frame chạy tiếp — chỉ có chữ là đổi.
 *
 * `fromInFrames` tính từ ĐẦU CẢNH, cùng mốc với `captionStartInFrames` và
 * `audioStartInFrames`. Các mảnh cộng lại đúng bằng `durationInFrames` của cảnh.
 */
export type Segment = {
  ja: string;
  romaji: string;
  hira?: string;
  vi: string;
  fromInFrames: number;
  durationInFrames: number;
};

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
  /** Caption vào ở frame thứ mấy trong cảnh. Không có = 0. Cảnh 1 chờ tiêu đề hiện xong */
  captionStartInFrames?: number;
  /** Clip nền, tính từ public/. null = dùng nền gradient */
  clip: string | null;
  /** Độ dài clip nền tính bằng frame (để loop khi clip ngắn hơn cảnh) */
  clipDurationInFrames: number | null;
  /** Cắt clip từ giây thứ mấy */
  clipStartInSeconds: number;
  /**
   * Các mảnh caption của câu này. null/thiếu = hiện nguyên `ja`/`vi`, và đó là
   * đa số câu. `ja`/`vi` bên trên LUÔN là nguyên câu kể cả khi có mảnh — bản
   * Remotion cũ không biết trường này thì vẫn render đúng, chỉ là chữ nhỏ hơn.
   */
  segments?: Segment[] | null;
};

/**
 * Tiêu đề đầu video, hiện đè lên cảnh 1. null = không có.
 *
 * Thay cho màn mở đầu nền gradient cũ. build.json vẫn còn trường `intro` nhưng
 * luôn là null — giữ để Remotion bản cũ đếm đúng tổng frame (P-3). Bản này
 * không đọc `intro` nữa.
 */
export type TitleCard = {
  /** Chữ to ở 1/4 trên: ngày tháng, vd. 8月20日 */
  title: string;
  /** Chữ nhỏ dưới ngày: chủ đề của ngày. Rỗng thì không hiện */
  subtitle: string;
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

/**
 * Chữ để ĐĂNG kèm video — không có gì vẽ lên màn hình.
 *
 * Remotion không đọc trường này; `make export` mới đọc, để dựng caption.txt và
 * description.txt. Khai ở đây vì types.ts là bản mô tả hợp đồng: một trường có
 * trong build.json mà không có trong file này thì người đọc sẽ tưởng nó thừa.
 */
export type Post = {
  /** Nguyên dòng dán được: "11.09.26 🌿 Có nhiều thứ không thể nắm giữ…" */
  caption: string;
  /** Phần người viết gõ, chưa có ngày ở đầu */
  text: string;
  /** "11.09.26" */
  dateLabel: string;
  hashtags: string[];
  /** true = kịch bản chưa khai caption, máy mượn tạm câu tiếng Việt cuối cùng */
  borrowed: boolean;
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
  /** Tiêu đề ngày đè lên cảnh 1. Tuỳ chọn */
  titleCard?: TitleCard | null;
  /** BƯỚC 5 — các trường dưới đây đều tuỳ chọn */
  outro?: Outro | null;
  transition?: Transition;
  transitionInFrames?: number;
  /** Hiện dòng hiragana dưới romaji. Mặc định tắt */
  showHira?: boolean;
  /**
   * Hai trường dưới đây Remotion KHÔNG dùng — chúng có mặt để lệnh khác đọc.
   * `thumbnailFrame` cho `make thumbnail`, `post` cho `make export`.
   */
  thumbnailFrame?: number;
  post?: Post | null;
  lines: Line[];
};
