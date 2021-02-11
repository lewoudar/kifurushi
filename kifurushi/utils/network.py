"""Module which contains various helper functions usefule when handling kifurushi packets."""
from typing import Union


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
    """Returns tcpdump / wireshark like hexadecimal view of the packet."""
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
