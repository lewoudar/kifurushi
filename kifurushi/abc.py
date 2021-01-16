"""Module which contains base abstract classes"""
import copy
import struct
from abc import ABC, abstractmethod
from typing import Any

import attr

from .random_values import (
    rand_signed_bytes, rand_bytes, rand_signed_short, rand_short, rand_signed_int, rand_int, rand_signed_long,
    rand_long, rand_string
)


@attr.s(repr=False)
class Field(ABC):
    _name: str = attr.ib(validator=attr.validators.instance_of(str))
    _default: Any = attr.ib()
    _value: Any = attr.ib(init=False)
    _format: str = attr.ib(
        kw_only=True,
        validator=[attr.validators.instance_of(str), attr.validators.matches_re(r'b|B|h|h|H|i|I|q|Q|\d+s')]
    )
    _size: int = attr.ib(init=False)
    _struct: struct.Struct = attr.ib(init=False)
    _order: str = attr.ib(kw_only=True, default='!', validator=attr.validators.in_(['<', '>', '!', '@', '=']))

    def __attrs_post_init__(self):
        _format = f'{self._order}{self._format}'
        self._value = self._default
        self._struct = struct.Struct(_format)
        self._size = struct.calcsize(_format)

    @property
    def size(self) -> int:
        """Returns the size in bytes of the field."""
        return self._size

    @property
    def name(self) -> str:
        """Returns field's name."""
        return self._name

    @property
    def default(self) -> Any:
        """Returns field's default value."""
        return self._default

    @property
    def struct_format(self) -> str:
        """Returns the struct format used under the hood for computation of raw internal value."""
        return f'{self._order}{self._format}'

    @property
    def value(self) -> Any:
        """Returns field's internal value."""
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """Sets field's internal value"""
        self._value = value
        attr.validate(self)

    def random_value(self) -> Any:
        """Returns a random value according to the field format."""
        if self._format == 'b':
            return rand_signed_bytes()

        elif self._format == 'B':
            return rand_bytes()

        elif self._format == 'h':
            return rand_signed_short()

        elif self._format == 'H':
            return rand_short()

        elif self._format == 'i':
            return rand_signed_int()

        elif self._format == 'I':
            return rand_int()

        elif self._format == 'q':
            return rand_signed_long()

        elif self._format == 'Q':
            return rand_long()
        else:
            return rand_string(int(self._format[:-1]))

    def __repr__(self):
        return f'<{self.__class__.__name__}: name={self._name}, value={self._value}, default={self._default}>'

    def clone(self) -> 'Field':
        """
        Returns a copy of the current field.
        """
        return copy.copy(self)

    @abstractmethod
    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        """
        Sets internal field value and returns the remaining bytes to parse from `data`.

        **Parameters:**

        * **data:**: The raw data currently being parsed by a packet object.
        * **packet:** The optional packet currently parsing a raw bytes object. It can be useful
        when current field value depends of another one.
        """

    @property
    def raw(self) -> bytes:
        """
        Returns the bytes representation of the object internal value.
        """
        return self._struct.pack(self._value)
