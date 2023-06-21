import ctypes
import struct
from typing import BinaryIO, Dict, TypeVar, ByteString, Iterator, Optional
from pathlib import Path
from functools import cache


ROOM_DATA_RESOURCE_ID = 0x3f05

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


class LureFileResourceLoader:
    UNUSED_HEADER_ENTRY_ID = 0xffff

    def __init__(self, file_path: Path, lang_code: int = ENG_LANG_CODE):
        self._data_file = file_path.open("rb")
        self._lang_code = lang_code
        self._base_offset = self._find_header()
        self._entries = self._read_header()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @cache
    def get_resource(self, resource_id: int) -> Optional[ByteString]:
        if resource_id in self._entries:
            entry = self._entries[resource_id]
            self._data_file.seek(entry.offset * 32 + self._base_offset)
            resource_size = entry.size + (0x1000 if entry.size_extension else 0)
            return self._data_file.read(resource_size)

    def close(self):
        self._data_file.close()

    def _find_header(self) -> int:
        class LangOffset(LureStruct):
            _pack_ = 1
            _fields_ = [
                ("code", ctypes.c_uint8),
                ("offset", ctypes.c_uint32)
            ]

        ident = b'lure\x00\x00'
        assert self._data_file.read(len(ident)) == ident

        while offset := LangOffset.unpack(self._data_file):
            if offset.code == 0xFF:
                raise RuntimeError("Could not find English language section")
            if offset.code == self._lang_code:
                return offset.offset

    def _read_header(self) -> Dict[int, FileEntry]:
        self._data_file.seek(self._base_offset)
        assert self._data_file.read(8) == b'heywow\x00\x00'
        entries = dict()
        for _ in range(NUM_ENTRIES_IN_HEADER):
            next_entry = FileEntry.unpack(self._data_file)
            if next_entry.ref_id != LureFileResourceLoader.UNUSED_HEADER_ENTRY_ID:
                entries[next_entry.ref_id] = next_entry
        return entries


def read_room_resources(room_data: ByteString) -> Iterator[RoomResource]:
    for raw_word in zip(room_data[::2], room_data[1::2]):
        offset, = struct.unpack("<H", bytes(raw_word))
        if offset == 0xFFFF:
            return
        yield RoomResource.from_buffer_copy(room_data, offset)


def file_for_id(ref_id: int) -> str:
    if (ref_id >> 8) == 0x3f:
        return DATA_FILE_NAME
    file_no = ((ref_id >> 14) & 3) + 1
    return f"disk{file_no}.vga"


def main():
    data_path = Path(".") / file_for_id(ROOM_DATA_RESOURCE_ID)
    with LureFileResourceLoader(data_path) as loader:
        room_data = loader.get_resource(ROOM_DATA_RESOURCE_ID)
        print("Room\tNum\tLayer\tFile")
        print("Number\tLayers\tId")
        for room in read_room_resources(room_data):
            print(room.room_number, room.num_layers,
                  list(room.layers), file_for_id(room.layers[0]), sep='\t')


if __name__ == "__main__":
    main()
