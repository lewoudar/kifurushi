"""Implementation of DNS protocol"""
import random
import struct
import string
from typing import List

import attr

from kifurushi import Field, rand_string


@attr.s(repr=False)
class DomainNameField(Field):
    """
    String fields can't be used for the dns name because of its particular way to serialize/deserialize data.
    So we need to create a custom field for that.
    """

    # it is a good idea to validate the given domain name, but I will not do it here
    _default: str = attr.ib(validator=attr.validators.instance_of(str))
    _name: str = attr.ib(default='name', validator=attr.validators.instance_of(str))
    _labels: List[str] = attr.ib(factory=list, init=False)
    _format: str = attr.ib(default='!', validator=attr.validators.in_(['!', '@', '<', '>', '=']))

    def __attrs_post_init__(self):
        self._default = self._default if self._default.endswith('.') else f'{self._default}.'
        self.value = self._default

    @property
    def name(self) -> str:
        return self._name

    @property
    def default(self) -> str:
        return self._default

    @property
    def value(self) -> str:
        return '.'.join(label for label in self._labels) + '.'

    @value.setter
    def value(self, value: str) -> None:
        # you probably want to check the given value but I will not do it here.
        value = value.rstrip('.')
        self._labels = value.split('.')

    @property
    def struct_format(self) -> str:
        result = f'{self._format}'
        for label in self._labels:
            result += f'B{len(label)}s'

        result += 'B'
        return result

    @property
    def size(self) -> int:
        return struct.calcsize(self.struct_format)

    @property
    def raw(self) -> bytes:
        parts = []
        struct_format = f'{self._format}'
        for label in self._labels:
            length = len(label)
            parts.extend([length, label.encode()])
            struct_format += f'B{length}s'

        struct_format += 'B'
        parts.append(0)
        return struct.pack(struct_format, *parts)

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:  # noqa
        # we do not handle label compression like specified in rfc 1035 but it is a good idea to do that
        length = data[0]
        index = 1
        labels: List[str] = []
        while length:
            label = data[index: index + length]
            labels.append(label.decode())
            index += length
            length = data[index]
            index += 1

        self._labels = labels
        return data[index:]

    def random_value(self) -> str:
        tld_list = ['fr', 'com', 'net', 'org', 'edu', 'gov']
        return f'{rand_string(10, string.ascii_lowercase)}.{random.choice(tld_list)}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: value={self.value}, default={self._default}>'


if __name__ == '__main__':
    field = DomainNameField('kifurushi.io')
    field.value = 'foo.bar.com'
    print(field.value)
    print(field.raw)
    remaining_data = field.compute_value(b'\x05hello\x03com\x00\x00\x01')
    print(field.value)
    print(remaining_data)
