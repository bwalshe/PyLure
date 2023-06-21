import ctypes
from functools import cache
from typing import BinaryIO, ByteString, Dict, Optional

ENG_LANG_CODE = 3


class LangOffset(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("code", ctypes.c_uint8),
        ("offset", ctypes.c_uint32)
    ]


class FileEntry(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("ref_id", ctypes.c_uint16),
        ("unused", ctypes.c_byte),
        ("size_extension", ctypes.c_byte),
        ("size", ctypes.c_uint16),
        ("offset", ctypes.c_uint16)
    ]


class LureFileResourceLoader:
    def __init__(self, data: BinaryIO, lang_code: int = ENG_LANG_CODE):
        self._data = data
        self._lang_code = lang_code
        self._base_offset = self._find_header()
        self._entries = self._read_header()

    @cache
    def __getitem__(self, resource_id: int) -> Optional[ByteString]:
        if resource_id in self._entries:
            entry = self._entries[resource_id]
            self._data.seek(entry.offset * 32 + self._base_offset)
            resource_size = entry.size + (0x1000 if entry.size_extension else 0)
            return self._data.read(resource_size)

    def __len__(self):
        return len(self._entries)

    def __contains__(self, item):
        return item in self._entries

    def keys(self):
        return self._entries.keys()

    def close(self):
        self._data.close()

    def _seek_and_check(self, location: int, magic_word: ByteString):
        self._data.seek(location)
        response = self._data.read(len(magic_word))
        if response != magic_word:
            raise RuntimeError("Invalid data file. "
                               f"Expected to find {magic_word} at offset {location:x}, but found {response} instead.")

    def _find_header(self) -> int:
        self._seek_and_check(0, b'lure\x00\x00')
        while offset := self._unpack(LangOffset):
            if offset.code == 0xFF:
                raise RuntimeError(f"Could not find header for language {self._lang_code}")
            if offset.code == self._lang_code:
                return offset.offset

    def _read_header(self) -> Dict[int, FileEntry]:
        num_entries_in_header = 0xBF
        self._seek_and_check(self._base_offset, b'heywow\x00\x00')
        entries = dict()
        for _ in range(num_entries_in_header):
            next_entry = self._unpack(FileEntry)
            if next_entry.ref_id != 0xFFFF:
                entries[next_entry.ref_id] = next_entry
        return entries

    def _unpack(self, struct_type):
        size = ctypes.sizeof(struct_type)
        buffer = self._data.read(size)
        return struct_type.from_buffer_copy(buffer)


def file_for_id(ref_id: int) -> str:
    if (ref_id >> 8) == 0x3f:
        return "lure.dat"
    file_no = ((ref_id >> 14) & 3) + 1
    return f"disk{file_no}.vga"

