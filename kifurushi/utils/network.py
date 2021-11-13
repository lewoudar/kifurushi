"""Module which contains various helper functions useful when handling kifurushi packets."""
import array
import struct
from typing import Union


# == hexdump ==

def smart_ord(value: Union[int, bytes]) -> int:
    if isinstance(value, int):
        return value
    return ord(value)


# I don't know how to test this function directly, so it is indirectly test by hexdump function.
def sane_value(value: bytes) -> str:
    result = ''
    for i in value:
        j = smart_ord(i)
        if (j < 32) or (j >= 127):
            result += '.'
        else:
            result += chr(j)
    return result


def hexdump(data: bytes) -> str:
    """
    Returns tcpdump / wireshark like hexadecimal view of the given data.

    **Parameters:**

    * **data:** The bytes to parse.
    """
    result = ''
    data_length = len(data)
    i = 0

    while i < data_length:
        result += '%04x  ' % i
        for j in range(16):
            if i + j < data_length:
                result += '%02X ' % smart_ord(data[i + j])
            else:
                result += '   '
        result += ' %s\n' % sane_value(data[i:i + 16])
        i += 16
    # remove trailing \n
    result = result[:-1] if result.endswith('\n') else result
    return result


# == checksum ==

def check_endian_transform(value: int) -> int:
    if struct.pack('H', 1) == b'\x00\x01':  # if native byte order is big endian
        return value

    return ((value >> 8) & 0xff) | value << 8


def checksum(data: bytes) -> int:
    """
    Returns the checksum of the given data.

    **Parameters:**

    * **data:** The bytes to parse.
    """
    if not isinstance(data, bytes):
        raise TypeError(f'data must be bytes but you provided {data}')

    if len(data) % 2 == 1:
        data += b'\0'
    s = sum(array.array('H', data))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    s = ~s
    return check_endian_transform(s) & 0xffff
