import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { minchoJA, sansLatin } from "./fonts";
import type { Line, Segment } from "./types";

/**
 * Nhịp hiện/tắt của chữ — chậm có chủ đích.
 *
 * Video này bán cảm giác thong thả, nên chữ phải trôi vào chứ không được bật ra.
 * 26 frame vào (~0,87 s) và 20 frame ra (~0,67 s), gần gấp đôi bản đầu.
 *
 * Câu ngắn nhất chỉ dài khoảng 99 frame, nên nếu cứ dùng cứng hai số này thì
 * gần nửa cảnh sẽ là animation. MAX_RATIO chặn chuyện đó: hiệu ứng không bao giờ
 * chiếm quá 30% chiều dài cảnh, câu ngắn tự động fade nhanh hơn một chút.
 */
const IN_FRAMES = 26;
const OUT_FRAMES = 20;
const MAX_RATIO = 0.3;

/**
 * Nhịp đổi giữa hai MẢNH của cùng một câu — nhanh hơn hẳn nhịp vào/ra ở trên.
 *
 * 26/20 frame là nhịp của một câu MỚI: nó xứng đáng được chờ. Còn đổi từ nửa
 * đầu sang nửa sau của cùng một câu thì không — giọng đọc lúc đó vẫn đang chạy
 * liền hơi, để chữ tắt gần một giây là người xem tưởng câu đã hết.
 *
 * Tắt hẳn rồi mới hiện, KHÔNG chồng lên nhau. Chồng lên nhau thì trong quãng
 * giao có hai câu khác nhau cùng nằm giữa khung, đọc ra chữ nọ xọ chữ kia. Thà
 * có một nhịp hụt rất ngắn — nó đọc ra như một hơi thở, mà giọng đọc thì vẫn
 * đang chạy nên tai không thấy hụt.
 */
const SWAP_FRAMES = 8;

/**
 * Vùng an toàn — xem CLAUDE.md.
 *
 * TikTok/Reels dán tên tài khoản, mô tả và thanh nhạc lên khoảng 350 px đáy
 * màn hình. Caption neo vào ĐÁY khối an toàn này chứ không neo giữa màn hình:
 * khối chữ cao hay thấp thì cũng nở lên trên, không bao giờ thò xuống vùng bị che.
 *
 * Với 1920 px chiều cao, khối caption kết thúc ở y = 1520 và thường bắt đầu
 * quanh y = 1050 — tức tâm chữ rơi vào khoảng 2/3 dưới, đúng chỗ mắt người xem
 * dừng lại khi lướt dọc.
 */
const SAFE_BOTTOM = 400;

/**
 * Dải icon bên phải (tim, bình luận, chia sẻ) rộng khoảng 130 px. Đệm đều hai
 * bên để chữ vẫn cân giữa khung, chỉ hẹp lại vừa đủ tránh dải đó.
 */
const SAFE_SIDE = 110;

/**
 * CỠ CHỮ CỐ ĐỊNH, không co theo độ dài câu nữa.
 *
 * Bản cũ có một thang năm bậc (62/55/48/42/36 theo số chữ). Nó không bao giờ
 * làm tràn khung, nhưng nó làm một việc tệ hơn: câu 12 chữ hiện ở cỡ 62 rồi câu
 * 22 chữ ngay sau đó hiện ở cỡ 55, nên suốt video cỡ chữ nhảy lên nhảy xuống —
 * mà độ dài câu thì chẳng nói lên điều gì với người xem.
 *
 * Giờ câu dài được CẮT ra chứ không bị bóp lại (xem pipeline/phrase.py), nên
 * mảnh nào cũng nằm dưới ngưỡng và dùng chung một cỡ. Câu dài hơn thì khối chữ
 * cao thêm một dòng — mà khối neo đáy nên nó nở lên trên, chân chữ không xê dịch.
 *
 * Hai bậc nhỏ phía sau CHỈ là lưới an toàn cho câu không cắt được (không có dấu
 * ngắt nào). Rơi vào đó thì `make content` đã kêu một dòng rồi: cỡ chữ nhỏ bất
 * thường ở một cảnh là TRIỆU CHỨNG, không phải cách chữa.
 *
 * Ngưỡng 30 chữ Nhật / 88 ký tự Việt là chỗ chữ phải xuống DÒNG THỨ BA ở cỡ
 * chuẩn — nó phải khớp JA_FIT và VI_FIT trong pipeline/phrase.py, vì bên đó lấy
 * đúng hai số này để quyết định có kêu hay không. Ngưỡng CẮT bên đó (JA_MAX 24 /
 * VI_MAX 60) chặt hơn hẳn, và chặt hơn là cố ý: nhờ khoảng đệm ấy, câu không cắt
 * được vẫn hiện nguyên ở đúng cỡ chữ này chứ không phải co lại.
 */
const JA_SIZE = 56;
const VI_SIZE = 38;

const fitJa = (len: number) =>
  len <= 30 ? JA_SIZE : len <= 40 ? 46 : 38;

const fitVi = (len: number) => (len <= 88 ? VI_SIZE : len <= 120 ? 32 : 28);

/**
 * Chia chữ thành các dòng dài gần bằng nhau thay vì nhồi đầy dòng trên rồi bỏ
 * một chữ lẻ loi xuống dòng dưới. Không có nó, câu 16 ký tự bị cắt thành
 * 15 + 1 — dòng dưới trơ trọi mỗi chữ "た。".
 */
const BALANCED = { textWrap: "balance" } as const;

/**
 * Viền tối sát nét + quầng sáng dịu, không phải neon.
 *
 * Bốn lớp bóng, lớp viết trước nằm trên:
 *   1. viền tối 3px sát nét -> tách rìa chữ trắng khỏi nền trắng (tuyết, giấy,
 *                               cánh hoa). Mỏng tới mức mắt không thấy thành viền.
 *   2. bóng tối gần         -> dày thêm cho nét mảnh của font Mincho
 *   3. quầng ấm tán rộng    -> phần cảm xúc. Nhạt hơn bản cũ (0,30 -> 0,14): quầng
 *                               SÁNG quanh chữ trắng trên nền sáng là tự xoá chữ
 *   4. bóng tối đổ xuống    -> như cũ
 *
 * Lớp phủ của Background.tsx giờ rất nhẹ, chữ không còn nằm sẵn trên nền tối.
 * Lớp 1, lớp 2 và CAPTION_SCRIM bên dưới là ba thứ giữ chữ đọc được.
 */
const SOFT_GLOW = [
  "0 0 3px rgba(0,0,0,0.55)",
  "0 2px 10px rgba(0,0,0,0.45)",
  "0 0 18px rgba(255,248,235,0.14)",
  "0 6px 28px rgba(0,0,0,0.6)",
].join(", ");

/**
 * Quầng tối ĐI THEO khối chữ — thay cho việc phủ tối cả khung hình.
 *
 * Nó nằm trong khối chữ, nên tự khớp kích thước (câu hai dòng hay ba dòng),
 * trôi lên cùng chữ và mờ đi cùng chữ. Giữa hai câu, lúc không có chữ nào, clip
 * sáng trọn vẹn — đó là chỗ video lấy lại độ tươi.
 *
 * `closest-side` cho elip chạm đúng bốn mép hộp, tới mép là trong suốt hẳn, nên
 * không có đường viền hộp nào lộ ra. Hộp tràn khỏi khối chữ (SCRIM_BLEED) để
 * phần đậm phủ hết chữ còn phần nhạt tan ra ngoài.
 */
const CAPTION_SCRIM =
  "radial-gradient(closest-side, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.4) 45%, rgba(0,0,0,0.16) 75%, rgba(0,0,0,0) 100%)";
const SCRIM_BLEED = { x: 150, y: 110 };

/** Khối ba dòng chữ. Không biết gì về frame — chỉ nhận độ mờ và độ trôi. */
const Block: React.FC<{
  piece: Segment;
  showHira: boolean;
  opacity: number;
  translateY: number;
}> = ({ piece, showHira, opacity, translateY }) => (
  <div
    style={{
      position: "relative",
      // Giữ quầng tối (zIndex -1) nằm SAU chữ nhưng vẫn TRƯỚC clip nền. Thiếu
      // dòng này thì quầng tụt xuống dưới cả Background, và chỉ còn đúng nhờ
      // `transform` tình cờ tạo stacking context.
      isolation: "isolate",
      opacity,
      transform: `translateY(${translateY}px)`,
      textAlign: "center",
      textShadow: SOFT_GLOW,
    }}
  >
    <div
      style={{
        position: "absolute",
        inset: `-${SCRIM_BLEED.y}px -${SCRIM_BLEED.x}px`,
        zIndex: -1,
        background: CAPTION_SCRIM,
      }}
    />

    {/* Câu tiếng Nhật — chữ chính, to nhất */}
    <div
      style={{
        ...BALANCED,
        fontFamily: minchoJA,
        color: "#ffffff",
        fontSize: fitJa(piece.ja.length),
        fontWeight: 600,
        lineHeight: 1.55,
        letterSpacing: 1,
      }}
    >
      {piece.ja}
    </div>

    {/*
      Cách đọc — chữ nhỏ, nhạt hơn dòng chính, để người mới đọc theo được.
      0,82 chứ không 0,62 như trước: chữ nghiêng 30px mà trong suốt quá thì chìm
      hẳn trên nền sáng, từ khi lớp phủ không còn tối sẵn bên dưới.
    */}
    {piece.romaji ? (
      <div
        style={{
          fontFamily: sansLatin,
          color: "rgba(255,255,255,0.82)",
          fontSize: 30,
          fontWeight: 400,
          fontStyle: "italic",
          lineHeight: 1.5,
          marginTop: 22,
          letterSpacing: 0.5,
        }}
      >
        {piece.romaji}
      </div>
    ) : null}

    {/*
      Dòng hiragana — mặc định TẮT.

      Nó hữu ích hơn romaji với người đang học thật sự, nhưng bật lên là
      caption thành bốn dòng, và bốn dòng thì khối chữ cao thêm khoảng 60px,
      lấn dần vào vùng an toàn 380px dưới đáy. Bật `showHira` trong kịch bản
      để xem thử rồi tự quyết — đừng quyết bằng cách tưởng tượng.

      Câu nào vốn đã toàn kana (vd. おはようございます。) thì `hira` giống hệt
      `ja`, in ra là lặp nguyên một dòng. Bỏ qua đúng những câu đó: dòng
      hiragana chỉ có nghĩa khi nó đọc hộ được chữ kanji.
    */}
    {showHira && piece.hira && piece.hira !== piece.ja ? (
      <div
        style={{
          fontFamily: minchoJA,
          color: "rgba(255,255,255,0.5)",
          fontSize: 26,
          fontWeight: 600,
          lineHeight: 1.5,
          marginTop: 14,
          letterSpacing: 1,
        }}
      >
        {piece.hira}
      </div>
    ) : null}

    {/* Gạch ngăn giữa phần tiếng Nhật và phần tiếng Việt */}
    <div
      style={{
        width: 120,
        height: 1,
        background: "rgba(255,255,255,0.55)",
        margin: "34px auto",
      }}
    />

    {/* Nghĩa tiếng Việt */}
    <div
      style={{
        ...BALANCED,
        fontFamily: sansLatin,
        color: "#f2e9dc",
        fontSize: fitVi(piece.vi.length),
        fontWeight: 400,
        lineHeight: 1.55,
      }}
    >
      {piece.vi}
    </div>
  </div>
);

/**
 * Câu chưa cắt cũng được coi là "một mảnh duy nhất" — nhờ vậy bên dưới chỉ có
 * MỘT đường chạy, không phải một nhánh cho câu thường và một nhánh cho câu dài.
 */
const pieces = (line: Line): Segment[] => {
  const start = line.captionStartInFrames ?? 0;
  if (line.segments && line.segments.length > 1) {
    return line.segments;
  }
  return [
    {
      ja: line.ja,
      romaji: line.romaji,
      hira: line.hira,
      vi: line.vi,
      fromInFrames: start,
      durationInFrames: line.durationInFrames - start,
    },
  ];
};

export const Caption: React.FC<{ line: Line; showHira?: boolean }> = ({
  line,
  showHira = false,
}) => {
  const frame = useCurrentFrame();
  const all = pieces(line);

  // Mảnh đang hiện: mảnh cuối cùng đã tới lượt. Trước mảnh đầu (cảnh 1 còn đang
  // chờ tiêu đề ngày hiện xong) thì vẫn là mảnh đầu — nó chưa hiện ra vì `local`
  // còn âm nên opacity bằng 0. Đó đúng là hành vi của bản trước.
  let i = 0;
  for (let k = 1; k < all.length; k++) {
    if (frame >= all[k].fromInFrames) i = k;
  }
  const piece = all[i];

  const local = frame - piece.fromInFrames;
  const d = piece.durationInFrames;

  // Mảnh đầu được nhịp vào thong thả của một câu mới; mảnh cuối được nhịp ra
  // thong thả trước khi chuyển cảnh. Ranh giới BÊN TRONG một câu thì nhanh.
  const inF = Math.min(
    i === 0 ? IN_FRAMES : SWAP_FRAMES,
    Math.round(d * MAX_RATIO),
  );
  const outF = Math.min(
    i === all.length - 1 ? OUT_FRAMES : SWAP_FRAMES,
    Math.round(d * MAX_RATIO),
  );

  // Hiện lên: mờ dần vào + trôi lên nhẹ.
  //
  // Dùng inOut chứ không phải out. Easing.out dồn phần lớn độ mờ vào mấy frame
  // đầu — kéo dài bao nhiêu thì mắt vẫn thấy chữ "bật" ra rồi mới đứng yên.
  // inOut giữ chữ mờ lâu hơn ở đầu, nên cả quãng đọc ra là thong thả thật.
  const enter = interpolate(local, [0, inF], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

  // Tắt đi ở cuối cảnh để chữ không đè lên câu tiếp theo lúc chuyển cảnh.
  // Easing.inOut cho chữ nhạt đi đều đặn thay vì tắt phụt ở khung cuối.
  const exit = interpolate(local, [d - outF, d], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.quad),
  });

  const opacity = enter * exit;
  // Trôi xa hơn bản cũ (26 -> 34 px) vì quãng đường dài trên nền thời gian dài
  // đọc ra là thong thả; trôi ngắn mà chậm lại thành ra ì. Mảnh giữa câu trôi
  // ít hơn: nó chỉ là nửa sau của một câu đang đọc dở, không phải một ý mới.
  const translateY = interpolate(enter, [0, 1], [i === 0 ? 34 : 14, 0]);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        padding: `0 ${SAFE_SIDE}px ${SAFE_BOTTOM}px`,
      }}
    >
      <Block
        piece={piece}
        showHira={showHira}
        opacity={opacity}
        translateY={translateY}
      />
    </AbsoluteFill>
  );
};
