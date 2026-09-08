/**
 * Nạp font 1 lần cho cả project.
 *
 * Noto Serif JP có đủ 3 bộ ký tự cần dùng:
 *   japanese   -> 今日は…
 *   latin-ext  -> romaji có dấu macron (ō, ū)
 *   vietnamese -> tiếng Việt có dấu
 *
 * Nếu không nạp font này, Chrome trong lúc render sẽ vẽ chữ Nhật thành ô vuông
 * (tofu) vì máy render thường không cài sẵn font CJK.
 */
import { loadFont } from "@remotion/google-fonts/NotoSerifJP";

export const { fontFamily: serifJP } = loadFont("normal", {
  // chỉ lấy đúng 2 độ đậm đang dùng — mỗi weight là hàng trăm request tải font
  weights: ["400", "600"],
  subsets: ["japanese", "latin", "latin-ext", "vietnamese"],
  ignoreTooManyRequestsWarning: true,
});
