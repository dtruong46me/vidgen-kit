import { AbsoluteFill, Audio, Loop, Sequence, staticFile } from "remotion";
import { Background } from "./Background";
import { Caption } from "./Caption";
import { Intro } from "./Intro";
import { Outro } from "./Outro";
import type { DailyVideoProps } from "./types";

/**
 * Độ dài đoạn mờ chồng giữa 2 cảnh (frame) khi build.json không nói gì.
 *
 * Đi cùng nhịp với hiệu ứng chữ trong Caption.tsx: chữ trôi vào trong 26 frame
 * thì nền cũng phải đổi chậm tương đương, không thì nền cắt xoẹt trong khi chữ
 * còn đang trôi — hai lớp lệch nhịp nhau, mất cảm giác thong thả.
 *
 * Từ BƯỚC 5 con số này do kịch bản quyết (`transitionSeconds`), nhưng mặc định
 * vẫn đúng 24 — nên build.json cũ không có trường đó vẫn ra video y hệt.
 */
export const CROSSFADE = 24;

/** Vị trí bắt đầu (frame) của từng câu, cộng dồn từ độ dài các câu trước. */
export const getStarts = (
  lines: { durationInFrames: number }[],
  offset = 0,
) => {
  const starts: number[] = [];
  let cursor = offset;
  for (const line of lines) {
    starts.push(cursor);
    cursor += line.durationInFrames;
  }
  return starts;
};

export const DailyVideo: React.FC<DailyVideoProps> = ({
  lines,
  bgm,
  bgmDurationInFrames,
  bgmVolume,
  intro = null,
  outro = null,
  transition = "crossfade",
  transitionInFrames,
  showHira = false,
}) => {
  const fade = transitionInFrames ?? CROSSFADE;
  const introFrames = intro?.durationInFrames ?? 0;
  const outroFrames = outro?.durationInFrames ?? 0;

  // Mọi cảnh dịch xuống sau màn mở đầu. Đây là chỗ DUY NHẤT cộng offset đó —
  // caption, giọng đọc và nền đều lấy mốc từ cùng một mảng `starts`.
  const starts = getStarts(lines, introFrames);
  const scenesEnd =
    starts[starts.length - 1] + lines[lines.length - 1].durationInFrames;
  const total = scenesEnd + outroFrames;

  // crossfade cho cảnh bắt đầu SỚM hơn để chồng lên cảnh trước; hai kiểu kia
  // để cảnh nằm đúng ô của nó. Tính một lần ở đây thay vì rải if khắp JSX.
  const overlaps = transition === "crossfade";

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0c0b" }}>
      {/* Lớp 0 — MÀN MỞ ĐẦU. Không có thì cả khối này biến mất, video bắt đầu ngay ở câu 1. */}
      {intro ? (
        <Sequence durationInFrames={introFrames} name="Mở đầu">
          <Intro data={intro} fadeOutFrames={fade} />
        </Sequence>
      ) : null}

      {/*
        Lớp 1 — NỀN.
        Với crossfade, mỗi cảnh bắt đầu sớm hơn đúng `fade` frame và sáng dần
        lên trong quãng đó, nên nó chồng lên cuối cảnh trước.
      */}
      {lines.map((line, i) => {
        const early = overlaps && i > 0 ? fade : 0;
        const windowFrames = line.durationInFrames + early;
        return (
          <Sequence
            key={`bg-${i}`}
            from={Math.max(0, starts[i] - early)}
            durationInFrames={windowFrames}
            name={`Nền ${i + 1}`}
          >
            <Background
              line={line}
              index={i}
              fadeInFrames={fade}
              mode={transition}
              windowFrames={windowFrames}
            />
          </Sequence>
        );
      })}

      {/*
        Lớp 2 — CAPTION + GIỌNG ĐỌC.
        Lớp này KHÔNG chồng nhau: mỗi câu nằm đúng ô thời gian của nó,
        để giọng đọc không bao giờ bị chồng tiếng.
      */}
      {lines.map((line, i) => (
        <Sequence
          key={`line-${i}`}
          from={starts[i]}
          durationInFrames={line.durationInFrames}
          name={`Câu ${i + 1} — ${line.ja.slice(0, 12)}`}
        >
          <Caption line={line} showHira={showHira} />
          {/* Câu chưa có giọng đọc (props mặc định của Studio) thì bỏ qua lớp tiếng */}
          {line.audio ? (
            <Sequence from={line.audioStartInFrames} name="Giọng đọc">
              <Audio src={staticFile(line.audio)} />
            </Sequence>
          ) : null}
        </Sequence>
      ))}

      {/* Lớp 3 — MÀN KẾT */}
      {outro ? (
        <Sequence from={scenesEnd} durationInFrames={outroFrames} name="Kết">
          <Outro data={outro} />
        </Sequence>
      ) : null}

      {/*
        Lớp 4 — NHẠC NỀN: lặp lại cho đủ độ dài video, âm lượng nhỏ để không át lời.
        Chạy suốt cả video KỂ CẢ màn mở đầu và màn kết — nhạc dừng giữa chừng ở
        chỗ nối là thứ tai bắt được ngay, còn rõ hơn cả hình cắt.
      */}
      {bgm && bgmDurationInFrames ? (
        <Sequence durationInFrames={total} name="Nhạc nền">
          <Loop durationInFrames={bgmDurationInFrames}>
            <Audio src={staticFile(bgm)} volume={bgmVolume} />
          </Loop>
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};
