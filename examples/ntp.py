"""
This module provides a simple (non complete) implementation of NTPv4 header as described here:
https://tools.ietf.org/html/rfc5905#page-19
We don't take in account extensions in our implementation to make it simple.
There is a client example retrieving clock information from a server. If you want to work with IPV6, replace
AF_INET by AF_INET6 everywhere and change the hostname with "2.pool.ntp.org".
This example is based on trio work here: https://github.com/python-trio/trio/blob/master/notes-to-self/ntp-example.py
"""
import socket
import struct
import time
from datetime import datetime, timedelta

from kifurushi import Packet, ByteBitsField, FieldPart, ByteField, IntField, LongField, ConditionalField

leap_indicator = {
    0: 'no warning',
    1: 'last minute of the day has 61 seconds',
    2: 'last minute of the day has 59 seconds',
    3: 'unknown (clock unsynchronized)'
}

modes = {
    0: 'reserved',
    1: 'symmetric active',
    2: 'symmetric passive',
    3: 'client',
    4: 'server',
    5: 'broadcast',
    6: 'NTP control message',
    7: 'reserved for private use'
}


def extract_datetime(transmit_timestamp: bytes) -> datetime:
    # The timestamp is stored in the "NTP timestamp format", which is a 32
    # byte count of whole seconds, followed by a 32 byte count of fractions of
    # a second. See: https://tools.ietf.org/html/rfc5905#page-13
    seconds, fraction = struct.unpack('!II', transmit_timestamp)

    # The timestamp is the number of seconds since January 1, 1900 (ignoring
    # leap seconds). To convert it to a datetime object, we do some simple
    # datetime arithmetic:
    base_time = datetime(1900, 1, 1)
    offset = timedelta(seconds=seconds + fraction / 2 ** 32)
    return base_time + offset


# noinspection PyArgumentList
class NTP(Packet):
    __fields__ = [
        ByteBitsField(
            [FieldPart('li', 0b11, 2, leap_indicator), FieldPart('vn', 0b100, 3), FieldPart('mode', 0b011, 3, modes)]
        ),
        ByteField('stratum', 0),
        ByteField('poll', 0),
        ByteField('precision', 0),
        IntField('root_delay', 0),
        IntField('root_dispersion', 0),
        # if stratum is less than 2, it represents an IPV4 address or the first four octets of the MD5 hash
        # of an IPV6 address
        ConditionalField(IntField('ip_id', 0), lambda p: p.stratum < 2),
        ConditionalField(IntField('reference_id', 0), lambda p: p.stratum > 1),
        LongField('reference_timestamp', 0),
        LongField('origin_timestamp', 0),
        LongField('receive_timestamp', 0),
        LongField('transmit_timestamp', 0)
    ]


if __name__ == '__main__':
    print("Our clock currently reads (in UTC):", datetime.utcnow())

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # we look up some ntp servers
        # (See www.pool.ntp.org for information about the NTP pool.)
        servers = socket.getaddrinfo('pool.ntp.org', 'ntp', socket.AF_INET, socket.SOCK_DGRAM)

        print('== sending queries ==')
        for server in servers:
            address = server[-1]
            print('send query to:', address)
            sock.sendto(NTP().raw, address)

        print('== reading responses ==')
        for _ in range(len(servers)):
            data, address = sock.recvfrom(1024)
            print('got response from:', address)
            ntp = NTP.from_bytes(data)
            clock = extract_datetime(ntp.fields[-1].raw())
            print('Their clock read (in UTC):', clock)
            current_time = time.time()
