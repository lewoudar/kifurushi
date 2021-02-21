"""
In this example we will implement ICMPv4 Packet.
There is a simple client example to show how to send a ping (echo request) message. You will need privileged
rights to run the example.
"""
import ipaddress
import random
import socket
from typing import Optional, Union

import attr

from kifurushi import (
    Field, Packet, ByteField, ShortField, IntField, ConditionalField, ByteEnumField, checksum
)


def check_ip_address(_, _param, address: str) -> bool:
    try:
        ipaddress.ip_address(address)
        return True
    except ipaddress.AddressValueError:
        raise ValueError(f'{address} is not a valid ip address')


@attr.s(slots=True, repr=False)
class IPField(Field):
    _name: str = attr.ib(validator=attr.validators.instance_of(str))
    _default: str = attr.ib(validator=check_ip_address)
    _address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = attr.ib(init=False)

    def __attrs_post_init__(self):
        self._address = ipaddress.ip_address(self._default)

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        return 4 if self._address.version == 4 else 16

    @property
    def default(self) -> str:
        return self._default

    @property
    def value(self) -> str:
        return f'{self._address}'

    @value.setter
    def value(self, value: str) -> None:
        self._address = ipaddress.ip_address(value)

    @property
    def struct_format(self) -> str:
        # not really useful here
        return '!I' if self._address.version == 4 else '!IIII'

    def raw(self, packet: 'Packet' = None) -> bytes:  # noqa
        return self._address.packed

    def random_value(self) -> str:
        if self._address.version == 4:
            return f'{random.randint(1, 192)}.{random.randint(1, 168)}.0.1'
        else:
            return f'fe80::{random.randint(1, 8)}'

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> Optional[bytes]:  # noqa
        cursor = 4 if self._address.version == 4 else 16
        self._address = ipaddress.ip_address(data[:cursor])
        return data[cursor:]

    def __repr__(self):
        return f'<{self.__class__.__name__}: default={self._default}, value={self._address}>'


icmp_types = {
    0: 'echo-reply',
    5: 'redirect',
    8: 'echo-request',
    11: 'time-exceeded'
}


# noinspection PyArgumentList
class ICMP(Packet):
    __fields__ = [
        ByteEnumField('type', 8, icmp_types),
        ByteField('code', 0),
        ShortField('checksum', 0),
        ConditionalField(ShortField('id', 0), lambda p: p.type in [0, 8, 13, 14, 15, 16, 17, 18]),
        ConditionalField(ShortField('sequence', 0), lambda p: p.type in [0, 8, 13, 14, 15, 16, 17, 18]),
        ConditionalField(IntField('original_timestamp', 0), lambda p: p.type in [13, 14]),
        ConditionalField(IntField('receive_timestamp', 0), lambda p: p.type in [13, 14]),
        ConditionalField(IntField('transmit_timestamp', 0), lambda p: p.type in [13, 14]),
        ConditionalField(IPField('gateway', '0.0.0.0'), lambda p: p.type == 5),
        ConditionalField(ByteField('ptr', 0), lambda p: p.type == 12),
        ConditionalField(ByteField('reserved', 0), lambda p: p.type in [3, 11]),
        ConditionalField(ByteField('length', 0), lambda pkt: pkt.type in [3, 11, 12]),
        ConditionalField(IPField('address_mask', '0.0.0.0'), lambda pkt: pkt.type in [17, 18]),
        ConditionalField(ShortField('next_hop_mtu', 0), lambda pkt: pkt.type == 3),
        ConditionalField(
            IntField('unused', 0), lambda pkt: pkt.type not in [0, 3, 5, 8, 11, 12, 13, 14, 15, 16, 17, 18]
        )
    ]

    def __init__(self, **kwargs):
        self._field_mapping = []
        self.payload = b''
        payload = kwargs.pop('payload', None)
        if payload is not None:
            self.payload = payload
        super().__init__(**kwargs)

    @property
    def raw(self) -> bytes:
        if not self.checksum:
            data = b''.join(field.raw(self) for field in self._fields) + self.payload
            setattr(self, 'checksum', checksum(data))
        return b''.join(field.raw(self) for field in self._fields) + self.payload


if __name__ == '__main__':
    # change with what suits best to you (your gateway, a well known site, etc..)
    DESTINATION = '127.0.0.1'
    HOST = socket.gethostbyname(DESTINATION)

    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 64)
        print(f'sending ping to {DESTINATION}')
        icmp = ICMP(payload=b'a' * 60, id=0, sequence=1)
        sent = sock.sendto(icmp.raw, (DESTINATION, 1))

        data, _ = sock.recvfrom(1024)
        print('== response ==')
        icmp = ICMP.from_bytes(data)
        print(icmp)
