import ctypes
import struct
from functools import cache
from pathlib import Path
from typing import BinaryIO, ByteString
from collections.abc import KeysView, Iterator
from itertools import chain

ENG_LANG_CODE = 3
LURE_FILES = [
        "lure.dat",
        "Disk1.vga",
        "Disk2.vga",
        "Disk3.vga",
        "Disk4.vga",
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


def _seek_and_check(data: BinaryIO, location: int, magic_word: ByteString):
    data.seek(location)
    response = data.read(len(magic_word))
    if response != magic_word:
        raise RuntimeError("Invalid data file. "
                           f"Expected to find {magic_word} at offset {location:x}, but found {response} instead.")


def find_language_offset(data: BinaryIO, lang_code: int = ENG_LANG_CODE) -> int:
    _seek_and_check(data, 0, b'lure\x00\x00')
    fmt = "<BI"
    code_offset_size = struct.calcsize(fmt)
    while code_offset := struct.unpack(fmt, data.read(code_offset_size)):
        code, offset = code_offset
        if code == 0xFF:
            raise RuntimeError(f"Could not find header for language {lang_code}")
        if code == lang_code:
            return offset


class LureFileResourceLoader:
    num_entries_in_header = 0xBF

    def __init__(self, data: BinaryIO, file_no: int, base_offset: int = 0):
        _seek_and_check(data, base_offset, b'heywow' + file_no.to_bytes(2, "big"))
        self._data = data
        self._base_offset = base_offset
        entry_size = ctypes.sizeof(FileEntry)
        self._entries = dict()
        for _ in range(LureFileResourceLoader.num_entries_in_header):
            next_entry = FileEntry.from_buffer_copy(data.read(entry_size))
            if next_entry.ref_id != 0xFFFF:
                self._entries[next_entry.ref_id] = next_entry

    @cache
    def __getitem__(self, ref_id: int) -> ByteString:
        entry = self._entries[ref_id]
        self._data.seek(entry.offset * 32 + self._base_offset)
        resource_size = entry.size + (0x1000 if entry.size_extension else 0)
        return self._data.read(resource_size)

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, item) -> bool:
        return item in self._entries

    def keys(self) -> KeysView[int]:
        return self._entries.keys()


def _file_no_for_id(ref_id: int) -> int:
    if (ref_id >> 8) == 0x3f:
        return 0
    return ((ref_id >> 14) & 3) + 1


def file_for_id(ref_id: int) -> str:
    return LURE_FILES[_file_no_for_id(ref_id)]


class LureGameResourceManager:
    def __init__(self, root: Path):
        self._root = root
        self._data_files = None
        self._loaders = None

    def __enter__(self):
        try:
            self._data_files = [(self._root / f).open("rb") for f in LURE_FILES]
            offsets = [0] * len(self._data_files)
            offsets[0] = find_language_offset(self._data_files[0])
            self._loaders = [LureFileResourceLoader(d, i, o) for i, (d, o) in
                             enumerate(zip(self._data_files, offsets))]
            return self
        except Exception as e:
            self.close()
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        if not self._data_files:
            return
        close_exceptions = []
        try:
            for d in self._data_files:
                try:
                    d.close()
                except Exception as e:
                    close_exceptions.append(e)
        finally:
            self._loaders = None
            self._data_files = None

        if len(close_exceptions) > 0:
            raise ExceptionGroup("Failed to close one or more resource files.",
                                 close_exceptions)

    def __getitem__(self, ref_id: int) -> ByteString:
        if self._loaders is None:
            raise ValueError("Game resource files are not currently open")
        file_no = _file_no_for_id(ref_id)
        loader = self._loaders[file_no]
        return loader[ref_id]

    def keys(self) -> Iterator[int]:
        return chain(*[loader.keys() for loader in self._loaders])
