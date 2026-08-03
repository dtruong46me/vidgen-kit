import pytest

from vidgen.domain.position import Alignment, Position


def test_preset_stores_the_given_alignment():
    position = Position.preset(Alignment.TOP_RIGHT)

    assert position.kind == "preset"
    assert position.alignment is Alignment.TOP_RIGHT
    assert position.x is None
    assert position.y is None


def test_custom_stores_x_y_unit_for_ratio():
    position = Position.custom(0.25, 0.75, unit="ratio")

    assert position.kind == "custom"
    assert position.x == 0.25
    assert position.y == 0.75
    assert position.unit == "ratio"
    assert position.alignment is None


def test_custom_stores_x_y_unit_for_pixel():
    position = Position.custom(1080, 400, unit="pixel")

    assert position.kind == "custom"
    assert position.x == 1080
    assert position.y == 400
    assert position.unit == "pixel"


def test_custom_defaults_to_ratio_unit():
    position = Position.custom(0.5, 0.5)

    assert position.unit == "ratio"


@pytest.mark.parametrize("x, y", [(-0.1, 0.5), (0.5, 1.1), (1.5, 1.5)])
def test_custom_ratio_out_of_range_raises(x, y):
    with pytest.raises(ValueError):
        Position.custom(x, y, unit="ratio")


@pytest.mark.parametrize("x, y", [(-1, 100), (100, -1)])
def test_custom_pixel_negative_raises(x, y):
    with pytest.raises(ValueError):
        Position.custom(x, y, unit="pixel")


def test_position_is_frozen():
    position = Position.preset(Alignment.CENTER)

    with pytest.raises(AttributeError):
        position.alignment = Alignment.LEFT
