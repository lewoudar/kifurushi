"""Module which contains base abstract classes"""
import copy
import struct
from abc import ABC, abstractmethod
from typing import Any, Optional

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


# Due to its nature, it is impossible to inherit from Field class because we can't have
# a defined struct object here at instantiation. Some computations also need to change.
@attr.s(slots=True, repr=False)
class VariableStringField(ABC):
    """
    A field representing string data when length is not known in advance.

    **Parameters:**

    * **name:** The name of the field.
    * **default:** A default value for the field. Defaults to "kifurushi".
    * **length:** An optional maximum length of the field.
    * **order:** Order used to format raw data using `struct` module. Defaults to "!" (network). Valid values are
    "!", "<" (little-endian), ">" (big-endian), "@" (native), "=" (standard).
    """
    _name: str = attr.ib(validator=attr.validators.instance_of(str))
    _default: str = attr.ib(default='kifurushi', validator=attr.validators.instance_of(str))
    _max_length: Optional[int] = attr.ib(
        default=None, validator=attr.validators.optional(attr.validators.instance_of(int))
    )
    _order: str = attr.ib(default='!', validator=attr.validators.in_(['<', '>', '!', '@', '=']))
    _value: str = attr.ib(init=False)

    def __attrs_post_init__(self):
        if self._max_length is not None and len(self._default) > self._max_length:
            raise ValueError(f'default must be less or equal than maximum length ({self._max_length})')

        self._value = self._default

    @property
    def name(self) -> str:
        """Returns field's name"""
        return self._name

    @property
    def default(self) -> str:
        """Returns field's default value."""
        return self._default

    @property
    def max_length(self) -> Optional[int]:
        """Returns the optional max length of the field."""
        return self._max_length

    @property
    def value(self) -> str:
        """Returns internal string."""
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f'value must be a string but you provided {value}')

        if self._max_length is not None and len(value) > self._max_length:
            raise ValueError(f'value must be less or equal than maximum length ({self._max_length})')

        self._value = value

    @property
    def raw(self) -> bytes:
        """Returns bytes encoded value of the internal string."""
        return self._value.encode()

    def __repr__(self):
        return (
            f'<{self.__class__.__name__}: name={self._name}, value={self._value},'
            f' default={self._default}, max_length={self._max_length}>'
        )

    @property
    def struct_format(self) -> str:
        """Returns the struct format used under the hood for computation of raw internal value."""
        return f'{self._order}{len(self._value)}'

    @property
    def size(self) -> int:
        """Returns the size in bytes of the field."""
        return len(self._value)

    @abstractmethod
    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        """
        Sets internal string value and returns remaining bytes.

        **Parameters:**

        * **data:**: The raw data currently being parsed by a packet object.
        * **packet:** The optional packet currently parsing a raw bytes object. For a variable string field,
        it may be useful because the length of the field often depends on another field and we can retrieve if
        from the packet.
        """

    def clone(self) -> 'VariableStringField':
        """
        Returns a copy of the current field.
        """
        return copy.copy(self)

    def random_value(self) -> str:
        """
        Returns a random string. The length of the string is either the max length if given or the length
        of the default attribute.
        """
        length = self._max_length if self._max_length is not None else len(self._default)
        return rand_string(length)
