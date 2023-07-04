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
    return [tuple(raw_palette[i * 3:(i + 1) * 3]) for i in range(len(raw_palette) // 3)]


def room_palette_id(room_id: int) -> int:
    return (room_id & 0xffe0) - 1


class PixelDecoder:

    def __init__(self):
        self._compressed_data = None
        self._data_pos_1 = None
        self._data_pos_2 = None
        self._output = b''
        self._ch = None
        self._cl = None
        self._ah = None
        self._al = None
        self._bp = None

    def _esbx(self):
        result = self._compressed_data[self._data_pos_2]
        self._data_pos_2 += 1
        return result

    def _dssi(self):
        result = 0 if self._data_pos_1 == len(self._compressed_data) \
            else self._compressed_data[self._data_pos_1]
        self._data_pos_1 += 1
        return result

    def _decr_ctr(self):
        self._cl -= 1
        if self._cl == 0:
            self._ch = self._esbx()
            self._cl = 8

    def _shl_carry(self):
        result = (self._ch & 0x80) != 0
        self._ch <<= 1
        return result

    def decode_layer_pixels(self, compressed_data: ByteString) -> ByteString:
        if self._compressed_data is not None:
            raise RuntimeError("decode_layer_pixels may only be invoked once")
        self._compressed_data = compressed_data
        self._data_pos_1 = struct.unpack("<I", compressed_data[0x400:0x404])[0]
        self._data_pos_2 = 0x404

        self._ch = self._esbx()
        self._cl = 9
        loop_flag = True
        while loop_flag:
            self._al = self._dssi()
            self._output += bytes([self._al])
            self._bp = self._al << 2

            while True:
                self._decr_ctr()
                if self._shl_carry():
                    self._decr_ctr()
                    if self._shl_carry():
                        self._decr_ctr()
                        if self._shl_carry():
                            break

                        self._al = self._compressed_data[self._bp + 3]
                    else:
                        self._decr_ctr()
                        if self._shl_carry():
                            self._al = self._compressed_data[self._bp + 3]
                        else:
                            self._al = self._compressed_data[self._bp + 1]
                else:
                    self._decr_ctr()
                    if self._shl_carry():
                        self._al = self._bp >> 2
                        self._ah = self._dssi()
                        if self._ah == 0:
                            self._al = self._dssi()
                            if self._al == 0:
                                loop_flag = False
                                break
                            else:
                                continue
                        else:
                            self._output += bytes([self._al] * self._ah)
                            continue
                    else:
                        self._al = self._compressed_data[self._bp]

                self._output += bytes([self._al])
                self._bp = self._al << 2

        return self._output
