"""AudioLayer — a background music / voiceover layer (Layer 0)."""

from dataclasses import dataclass

from vidgen.domain.asset import Asset


@dataclass
class AudioLayer:
    """One audio layer on an ``AudioTrack``.

    Always plays its asset in full from ``start`` — there is no ``end``
    field; duration comes from the resolved ``Asset`` at render time (a
    future trim option would add ``trim_in``/``trim_out`` fields here).

    Attributes:
        asset: The underlying audio asset (``asset.type`` must be
            ``"audio"``).
        start: Start time on the timeline, in seconds.
        volume: Playback volume multiplier (``1.0`` = original volume).
        fade_in: Fade-in duration in seconds.
        fade_out: Fade-out duration in seconds.
    """

    asset: Asset
    start: float = 0
    volume: float = 1.0
    fade_in: float = 0
    fade_out: float = 0

    def __post_init__(self) -> None:
        if self.asset.type != "audio":
            raise ValueError(
                f"AudioLayer requires an Asset with type='audio', got "
                f"{self.asset.type!r}"
            )
