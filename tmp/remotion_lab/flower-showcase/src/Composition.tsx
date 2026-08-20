import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  OffthreadVideo,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Composition,
} from "remotion";

const TitleCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const opacity = interpolate(
    frame,
    [0, fps * 0.5, durationInFrames - fps * 0.5, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0b0b0f",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          opacity,
          color: "white",
          fontFamily: "sans-serif",
          fontSize: 70,
          fontWeight: 700,
          textAlign: "center",
        }}
      >
        Vidgen Kit
        <div style={{ fontSize: 32, fontWeight: 400, marginTop: 16 }}>
          Remotion editing demo
        </div>
      </div>
    </AbsoluteFill>
  );
};

const VideoClip: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <OffthreadVideo
        src={staticFile("video/big_buck_bunny.mp4")}
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
    </AbsoluteFill>
  );
};

const Watermark: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 20], [0, 0.85], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-end" }}>
      <Img
        src={staticFile("image/sample.jpg")}
        style={{
          width: 160,
          height: 90,
          objectFit: "cover",
          borderRadius: 8,
          margin: 24,
          opacity,
          border: "2px solid white",
        }}
      />
    </AbsoluteFill>
  );
};

export const MyComposition = () => {
  return (
    <Composition
      id="MyComp"
      component={MyComponent}
      durationInFrames={330}
      fps={30}
      width={1280}
      height={720}
    />
  );
};

export const MyComponent: React.FC = () => {
  return (
    <AbsoluteFill>
      <Sequence durationInFrames={90}>
        <TitleCard />
      </Sequence>

      <Sequence from={90} durationInFrames={240}>
        <VideoClip />
      </Sequence>

      <Sequence from={30}>
        <Watermark />
      </Sequence>

      <Audio src={staticFile("audio/sample.mp3")} volume={0.5} />
    </AbsoluteFill>
  );
};
