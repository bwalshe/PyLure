import ctypes
import struct
from typing import ByteString, Iterator, List, Tuple

ROOM_DATA_RESOURCE_ID = 0x3f05
SCREEN_WIDTH = 320


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


def read_palette(raw_palette: ByteString) -> List[Tuple[int, int, int]]:
    if len(raw_palette) % 3 != 0:
        raise RuntimeError("This resource does not appear to be a pallet.")
    shift_palette = [(x << 2) + (x >> 4) for x in raw_palette]
    return [tuple(shift_palette[i * 3:(i + 1) * 3]) for i in range(len(shift_palette) // 3)]


def room_palette_id(room_id: int) -> int:
    return (room_id & 0xffe0) - 1


class BitIterator:
    def __init__(self, byte_data: ByteString):
        self._bytes = (b for b in byte_data)
        self._pos = 9
        self._current = next(self._bytes)

    def __next__(self) -> bool:
        self._pos -= 1
        if self._pos == 0:
            self._current = next(self._bytes)
            self._pos = 8
        result = (self._current & 0x80) != 0
        self._current <<= 1
        return result


def decode_layer_pixels(compressed_data: ByteString) -> ByteString:
    dssi_start = struct.unpack("<I", compressed_data[0x400:0x404])[0]
    dssi = (b for b in compressed_data[dssi_start:])
    code_bits = BitIterator(compressed_data[0x404:])
    output = b''

    loop_flag = True
    while loop_flag:
        al = next(dssi)
        output += bytes([al])
        bp = al << 2

        while True:
            if next(code_bits):
                if next(code_bits):
                    if next(code_bits):
                        break
                    al = compressed_data[bp + 3]
                else:
                    if next(code_bits):
                        al = compressed_data[bp + 2]
                    else:
                        al = compressed_data[bp + 1]
            else:
                if next(code_bits):
                    al = bp >> 2
                    ah = next(dssi)
                    if ah == 0:
                        al = next(dssi)
                        if al == 0:
                            loop_flag = False
                            break
                        else:
                            continue
                    else:
                        output += bytes([al] * ah)
                        continue
                else:
                    al = compressed_data[bp]

            output += bytes([al])
            bp = al << 2

    return output
