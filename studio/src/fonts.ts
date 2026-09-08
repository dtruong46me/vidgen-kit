/**
 * Nạp font 1 lần cho cả project.
 *
 * Phải ghép HAI họ font, không thể dùng một họ duy nhất:
 *
 *   Shippori Mincho  -> dòng tiếng Nhật. Có subset "japanese" nhưng KHÔNG có
 *                       subset "vietnamese", nên nó không vẽ nổi chữ Việt có dấu.
 *   Be Vietnam Pro   -> dòng romaji và dòng tiếng Việt. Có "vietnamese" (dấu
 *                       tiếng Việt) và "latin-ext" (macron ō, ū của romaji Hepburn).
 *
 * Đây chính là nguyên nhân romaji từng hiện ra "Kyo¯mo" thay vì "Kyō mo":
 * font Nhật không có ō nên trình duyệt phải chắp vá o + dấu macron rời.
 *
 * Nếu quên nạp font Nhật, Chrome lúc render sẽ vẽ chữ Nhật thành ô vuông (tofu)
 * vì máy render không cài sẵn font CJK.
 *
 * Chỉ nạp đúng độ đậm đang dùng. Google cắt font CJK thành ~122 mảnh nhỏ, nên
 * mỗi weight thừa của font Nhật là hơn trăm request tải font.
 */
import { loadFont as loadBeVietnamPro } from "@remotion/google-fonts/BeVietnamPro";
import { loadFont as loadShipporiMincho } from "@remotion/google-fonts/ShipporiMincho";

/** Dòng tiếng Nhật — chữ chính. */
export const { fontFamily: minchoJA } = loadShipporiMincho("normal", {
  weights: ["600"],
  subsets: ["japanese", "latin", "latin-ext"],
  ignoreTooManyRequestsWarning: true,
});

/** Dòng romaji và dòng tiếng Việt. */
export const { fontFamily: sansLatin } = loadBeVietnamPro("normal", {
  weights: ["400"],
  subsets: ["latin", "latin-ext", "vietnamese"],
  ignoreTooManyRequestsWarning: true,
});

// Romaji in nghiêng. Nạp bản italic THẬT thay vì để Chrome tự bóp nghiêng chữ
// đứng — chữ bóp nghiêng làm dấu macron trượt lệch khỏi thân chữ.
loadBeVietnamPro("italic", {
  weights: ["400"],
  subsets: ["latin", "latin-ext"],
  ignoreTooManyRequestsWarning: true,
});
