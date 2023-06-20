import ctypes
import struct
from typing import BinaryIO, Dict, TypeVar

ROOM_DATA_RESOURCE_ID = 0x3f05
UNUSED_HEADER_ENTRY_ID = 0xffff
DATA_FILE_NAME = "lure.dat"
NUM_ENTRIES_IN_HEADER = 0xBF
ENG_LANG_CODE = 3


TLureStruct = TypeVar("TLureStruct", bound="LureStruct")


class LureStruct(ctypes.LittleEndianStructure):
    @classmethod
    def unpack(cls: TLureStruct, stream: BinaryIO) -> TLureStruct:
        size = ctypes.sizeof(cls)
        buffer = stream.read(size)
        return cls.from_buffer_copy(buffer)


class FileEntry(LureStruct):
    _pack_ = 1
    _fields_ = [
        ("ref_id", ctypes.c_uint16),
        ("unused", ctypes.c_byte),
        ("size_extension", ctypes.c_byte),
        ("size", ctypes.c_uint16),
        ("offset", ctypes.c_uint16)
    ]


class RoomRect(LureStruct):
    _pack_ = 1
    _fields_ = [
        ("xs", ctypes.c_int16),
        ("xe", ctypes.c_int16),
        ("ys", ctypes.c_int16),
        ("ye", ctypes.c_int16)
    ]


class RoomResource(LureStruct):
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


def find_header(data_file: BinaryIO, lang_code: int = ENG_LANG_CODE) -> int:
    class LangOffset(LureStruct):
        _pack_ = 1
        _fields_ = [
            ("code", ctypes.c_uint8),
            ("offset", ctypes.c_uint32)
        ]

    ident = b'lure\x00\x00'
    assert data_file.read(len(ident)) == ident

    while offset := LangOffset.unpack(data_file):
        if offset.code == 0xFF:
            raise RuntimeError("Could not find English language section")
        if offset.code == lang_code:
            return offset.offset


def read_header(data_file: BinaryIO, base_offset: int) -> Dict[int, FileEntry]:
    data_file.seek(base_offset)
    assert data_file.read(8) == b'heywow\x00\x00'
    entries = dict()
    for _ in range(NUM_ENTRIES_IN_HEADER):
        next_entry = FileEntry.unpack(data_file)
        if next_entry.ref_id != UNUSED_HEADER_ENTRY_ID:
            entries[next_entry.ref_id] = next_entry
    return entries


if __name__ == "__main__":
    with open(DATA_FILE_NAME, "rb") as data_file:
        base_offset = find_header(data_file)
        entries = read_header(data_file, base_offset)

        room_data_entry = entries[ROOM_DATA_RESOURCE_ID]
        data_file.seek(room_data_entry.offset * 32 + base_offset)
        print(room_data_entry.size, room_data_entry.size_extension)
        room_data = data_file.read(room_data_entry.size)
        print("Room\tNum\tLayer")
        print("Number\tLayers\tOffsets")
        for raw_word in zip(room_data[::2], room_data[1::2]):
            offset, = struct.unpack("<H", bytes(raw_word))
            if offset == 0xFFFF:
                break
            room = RoomResource.from_buffer_copy(room_data, offset)
            print(room.room_number, room.num_layers,
                  list(room.layers), sep='\t')
