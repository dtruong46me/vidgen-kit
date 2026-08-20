import { AbsoluteFill, Audio, Loop, Sequence, staticFile } from "remotion";
import { Background } from "./Background";
import { Caption } from "./Caption";
import type { DailyVideoProps } from "./types";

/** Độ dài đoạn mờ chồng giữa 2 cảnh (frame). */
export const CROSSFADE = 15;

/** Vị trí bắt đầu (frame) của từng câu, cộng dồn từ độ dài các câu trước. */
export const getStarts = (lines: { durationInFrames: number }[]) => {
  const starts: number[] = [];
  let cursor = 0;
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
}) => {
  const starts = getStarts(lines);
  const total = starts[starts.length - 1] + lines[lines.length - 1].durationInFrames;

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0c0b" }}>
      {/*
        Lớp 1 — NỀN.
        Mỗi cảnh bắt đầu SỚM hơn đúng CROSSFADE frame và fade-in trong quãng đó,
        nên nó chồng lên cuối cảnh trước => ra hiệu ứng chuyển cảnh mờ.
      */}
      {lines.map((line, i) => (
        <Sequence
          key={`bg-${i}`}
          from={Math.max(0, starts[i] - CROSSFADE)}
          durationInFrames={line.durationInFrames + (i === 0 ? 0 : CROSSFADE)}
          name={`Nền ${i + 1}`}
        >
          <Background line={line} index={i} fadeInFrames={CROSSFADE} />
        </Sequence>
      ))}

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
          <Caption line={line} />
          <Sequence from={line.audioStartInFrames} name="Giọng đọc">
            <Audio src={staticFile(line.audio)} />
          </Sequence>
        </Sequence>
      ))}

      {/* Lớp 3 — NHẠC NỀN: lặp lại cho đủ độ dài video, âm lượng nhỏ để không át lời */}
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
