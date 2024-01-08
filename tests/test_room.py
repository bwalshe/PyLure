from itertools import chain
import pytest

from pylure.room import read_room_resources, read_palette, decode_layer_pixels, ROOM_DATA_RESOURCE_ID, SCREEN_WIDTH
from pylure.resource import LureGameResourceManager


def test_read_room_resources(pytestconfig):
    with LureGameResourceManager(pytestconfig.rootpath / "data") as manager:
        room_bytes = manager[ROOM_DATA_RESOURCE_ID]
        assert room_bytes is not None
        assert len(room_bytes) > 0
        room_numbers = [room.room_number for room in read_room_resources(room_bytes)]
        assert len(room_numbers) == 45
        assert room_numbers[0] == 1
        assert sorted(room_numbers) == room_numbers


def test_pixel_decode(pytestconfig):
    with LureGameResourceManager(pytestconfig.rootpath / "data") as manager:
        room_bytes = manager[ROOM_DATA_RESOURCE_ID]
        for room in read_room_resources(room_bytes):
            layer_bytes = decode_layer_pixels(manager[room.layers[0]])
            assert len(layer_bytes) > SCREEN_WIDTH
            assert len(layer_bytes) % SCREEN_WIDTH == 0


def test_read_palette():
    expected = [(4, 4, 4), (16, 16, 16)]
    raw = bytes(list(chain((1, 1, 1), (4, 4, 4))))
    assert read_palette(raw) == expected


def test_read_palette_throws():
    with pytest.raises(RuntimeError):
        read_palette(b'\x00\x00\x00\x00')
