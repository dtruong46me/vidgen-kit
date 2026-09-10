import { AbsoluteFill, Audio, Loop, Sequence, staticFile } from "remotion";
import { Background } from "./Background";
import { Caption } from "./Caption";
import { Outro } from "./Outro";
import { TitleCard } from "./TitleCard";
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
  titleCard = null,
  outro = null,
  transition = "crossfade",
  transitionInFrames,
  showHira = false,
}) => {
  const fade = transitionInFrames ?? CROSSFADE;
  const outroFrames = outro?.durationInFrames ?? 0;

  // Video vào thẳng cảnh 1 ở frame 0 — không còn màn mở đầu nào đẩy các cảnh
  // lùi lại. Caption, giọng đọc và nền đều lấy mốc từ cùng một mảng `starts`.
  const starts = getStarts(lines);
  const scenesEnd =
    starts[starts.length - 1] + lines[lines.length - 1].durationInFrames;
  const total = scenesEnd + outroFrames;

  // crossfade cho cảnh bắt đầu SỚM hơn để chồng lên cảnh trước; hai kiểu kia
  // để cảnh nằm đúng ô của nó. Tính một lần ở đây thay vì rải if khắp JSX.
  const overlaps = transition === "crossfade";

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0c0b" }}>
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
        Lớp 2 — TIÊU ĐỀ NGÀY, đè lên cảnh 1 và sống đúng bằng cảnh đó.
        Nằm trên nền, dưới caption. Không có thì video vẫn bắt đầu y như vậy,
        chỉ thiếu dòng ngày.
      */}
      {titleCard ? (
        <Sequence
          from={starts[0]}
          durationInFrames={lines[0].durationInFrames}
          name="Tiêu đề"
        >
          <TitleCard
            data={titleCard}
            durationInFrames={lines[0].durationInFrames}
            fadeOutFrames={fade}
          />
        </Sequence>
      ) : null}

      {/*
        Lớp 3 — CAPTION + GIỌNG ĐỌC.
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

      {/* Lớp 4 — MÀN KẾT */}
      {outro ? (
        <Sequence from={scenesEnd} durationInFrames={outroFrames} name="Kết">
          <Outro data={outro} />
        </Sequence>
      ) : null}

      {/*
        Lớp 5 — NHẠC NỀN: lặp lại cho đủ độ dài video, âm lượng nhỏ để không át lời.
        Chạy suốt cả video KỂ CẢ khoảng lặng đầu và màn kết — nhạc dừng giữa chừng
        ở chỗ nối là thứ tai bắt được ngay, còn rõ hơn cả hình cắt.
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
