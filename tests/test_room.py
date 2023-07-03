import pytest

from pylure.room import read_room_resources, PixelDecoder, ROOM_DATA_RESOURCE_ID
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
    screen_width = 320
    with LureGameResourceManager(pytestconfig.rootpath / "data") as manager:
        room_bytes = manager[ROOM_DATA_RESOURCE_ID]
        for room in read_room_resources(room_bytes):
            decoder = PixelDecoder()
            layer_bytes = decoder.decode_layer_pixels(manager[room.layers[0]])
            assert len(layer_bytes) > screen_width
            assert len(layer_bytes) % screen_width == 0


def test_pixel_decode_is_one_time_only(pytestconfig):
    with LureGameResourceManager(pytestconfig.rootpath / "data") as manager:
        room_bytes = manager[ROOM_DATA_RESOURCE_ID]
        decoder = PixelDecoder()
        room = next(read_room_resources(room_bytes))
        compressed_layer = manager[room.layers[0]]
        decoder.decode_layer_pixels(compressed_layer)
        with pytest.raises(RuntimeError):
            decoder.decode_layer_pixels(compressed_layer)

