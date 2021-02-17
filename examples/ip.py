"""
Implementation of the IP field and the IPv4 protocol.
"""
import ipaddress
import random
from typing import Optional, Union

import attr

from kifurushi import Field


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
