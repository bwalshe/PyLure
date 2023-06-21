import ctypes
import struct
from typing import ByteString, Iterator

ROOM_DATA_RESOURCE_ID = 0x3f05


class RoomRect(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("xs", ctypes.c_int16),
        ("xe", ctypes.c_int16),
        ("ys", ctypes.c_int16),
        ("ye", ctypes.c_int16)
    ]


class RoomResource(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("room_number", ctypes.c_uint16),
        ("hdr_flags", ctypes.c_uint8),
        ("unused", ctypes.c_uint8),
        ("actions", ctypes.c_uint32),
        ("desc_id", ctypes.c_uint16),
        ("num_layers", ctypes.c_uint16),
        ("layers", ctypes.c_uint16 * 4),
        ("sequence_offset", ctypes.c_uint16),
        ("clipping_x_start", ctypes.c_int16),
        ("clipping_x_end", ctypes.c_int16),
        ("area_flag", ctypes.c_uint8),
        ("num_exits", ctypes.c_uint8),
        ("exit_time", ctypes.c_uint32),
        ("walk_bounds", RoomRect)
    ]


def read_room_resources(room_data: ByteString) -> Iterator[RoomResource]:
    for raw_word in zip(room_data[::2], room_data[1::2]):
        offset, = struct.unpack("<H", bytes(raw_word))
        if offset == 0xFFFF:
            return
        yield RoomResource.from_buffer_copy(room_data, offset)
