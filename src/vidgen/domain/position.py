from dataclasses import dataclass
from enum import Enum
from typing import Literal


class Alignment(Enum):
    CENTER = "center"
    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"
    BOTTOM_RIGHT = "bottom-right"
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class Position:
    kind: Literal["preset", "custom"]
    alignment: Alignment | None = None
    x: float | None = None
    y: float | None = None
    unit: Literal["ratio", "pixel"] = "ratio"

    @classmethod
    def preset(cls, alignment: Alignment) -> "Position":
        return cls(kind="preset", alignment=alignment)

    @classmethod
    def custom(
        cls, x: float, y: float, unit: Literal["ratio", "pixel"] = "ratio"
    ) -> "Position":
        if unit == "ratio" and not (0 <= x <= 1 and 0 <= y <= 1):
            raise ValueError(
                f"Position.custom with unit='ratio' requires 0 <= x <= 1 and "
                f"0 <= y <= 1, got x={x!r}, y={y!r}"
            )
        if unit == "pixel" and not (x >= 0 and y >= 0):
            raise ValueError(
                f"Position.custom with unit='pixel' requires non-negative x/y, "
                f"got x={x!r}, y={y!r}"
            )
        return cls(kind="custom", x=x, y=y, unit=unit)
