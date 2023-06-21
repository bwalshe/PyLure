from pathlib import Path

from pylure.room import read_room_resources, ROOM_DATA_RESOURCE_ID
from pylure.resource import LureGameResourceManager


def test_read_room_resources():
    with LureGameResourceManager(Path("data")) as manager:
        room_bytes = manager[ROOM_DATA_RESOURCE_ID]
        assert room_bytes is not None
        assert len(room_bytes) > 0
        room_numbers = [room.room_number for room in read_room_resources(room_bytes)]
        assert len(room_numbers) == 45
        assert room_numbers[0] == 1
        assert sorted(room_numbers) == room_numbers
