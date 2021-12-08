"""Module which contains base abstract classes"""
import copy
import string
import struct
from abc import ABC, abstractmethod
from typing import Any, Optional, Union, AnyStr, TYPE_CHECKING

import attr

from kifurushi.utils.random_values import (
    rand_signed_bytes, rand_bytes, rand_signed_short, rand_short, rand_signed_int, rand_int, rand_signed_long,
    rand_long, rand_string
)

if TYPE_CHECKING:  # pragma: no cover
    from .packet import Packet


@attr.s(repr=False)
class Field(ABC):
    """The abstract base class that **all** fields **must** inherit."""
    # it helps to know if the intern value attribute has been computed by the method compute_value
    _value_was_computed: bool = attr.ib(init=False, default=False)

    @property
    def value_was_computed(self) -> bool:
        return self._value_was_computed

    @property
    @abstractmethod
    def size(self) -> int:
        """Returns the size in bytes of the field."""

    @property
    @abstractmethod
    def default(self) -> Union[int, str]:
        """Returns the default value of the field."""

    @property
    @abstractmethod
    def value(self) -> Union[int, str]:
        """Returns the current value of the field."""

    @value.setter
    @abstractmethod
    def value(self, value: Any) -> None:
        """Sets the value of the field."""

    @property
    @abstractmethod
    def struct_format(self) -> str:
        """Returns the struct format used under the hood for computation of field value."""

    @abstractmethod
    def raw(self, packet: 'Packet' = None) -> bytes:  # noqa: F821
        """
        Returns the representation of field value in bytes as it will be sent on the network.

        **Parameters:**

        * **packet:** The optional packet currently parsing the raw `data` bytes. It can be useful
        when the computation of the field value depends on other fields.
        """

    @abstractmethod
    def random_value(self) -> Union[int, str]:
        """Returns a valid random value for this field."""

    def clone(self) -> 'Field':
        """Returns a copy of the field."""
        return copy.copy(self)

    @abstractmethod
    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        """
        Computes the field value from the raw bytes and returns remaining bytes to parse from `data` if any.

        **Parameters:**

        * **data:**: The raw data currently being parsed by a packet object.
        * **packet:** The optional packet currently parsing the raw `data` bytes. It can be useful
        when the value of the current field depends on other fields.
        """

    @abstractmethod
    def __repr__(self):  # pragma: no cover
        pass


def name_validator(field: Field, _, name: str) -> None:
    message = (
        f'{field.__class__.__name__} name must starts with a letter and follow standard rules for declaring'
        f' a variable in python but you provided {name}'
    )
    punctuation = string.punctuation.replace('_', '')
    if not name[0].isalpha() or not name[-1].isalnum():
        raise ValueError(message)

    for character in punctuation:
        if character in name:
            raise ValueError(message)


# noinspection PyAbstractClass
@attr.s(repr=False)
class CommonField(Field):
    r"""
    A common interface for integer and fixed-size string fields.

    **Parameters:**

    * **name:** The name of the field.
    * **default:** A default value for the field.
    * **format:** The format used by the [struct](https://docs.python.org/3/library/struct.html) module to allocate
    the correct size in bytes of the field value. The value provided is validated against the following regex:
    `r'b|B|h|h|H|i|I|q|Q|\d+s'`.
    * **order:** Order used to format raw data using the `struct` module. Defaults to `"!"` (network). Valid values are
    `"!"`, `"<"` (little-endian), `">"` (big-endian), `"@"` (native), `"="` (standard).
    """
    _name: str = attr.ib(validator=[attr.validators.instance_of(str), name_validator])
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
        """Returns the struct format used under the hood for computation of field value."""
        return f'{self._order}{self._format}'

    @property
    def value(self) -> Union[int, str]:
        """Returns field's value."""
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """Sets field's value."""
        self._value = value
        attr.validate(self)

    def random_value(self) -> Union[int, str]:
        """Returns a valid random value according to the field format."""
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

    def raw(self, packet: 'Packet' = None) -> bytes:
        """
        Returns the representation of field value in bytes as it will be sent on the network.

        **Parameters:**

        * **packet:** The optional packet currently parsing the raw `data` bytes. It can be useful
        when the computation of the field value depends on other fields.
        """
        return self._struct.pack(self._value)


@attr.s(slots=True, repr=False)
class VariableStringField(Field):
    """
    A field representing string data when length is not known in advance.

    **Parameters:**

    * **name:** The name of the field.
    * **default:** A default value for the field. Defaults to `kifurushi` or `b'kifurushi'` depending of the
    string type. See explanation of `is_bytes` parameter below.
    * **length:** An optional maximum length of the field.
    * **order:** Order used to format raw data using the [struct](https://docs.python.org/3/library/struct.html) module.
    Defaults to `"!"` (network). Valid values are `"!"`, `"<"` (little-endian), `">"` (big-endian), `"@"` (native),
    `"="` (standard).
    * **decode:** keyword-only boolean parameter to know if this field represents raw bytes or utf-8 text.
    Defaults to `False` meaning it is bytes which is considered by default.
    """
    _name: str = attr.ib(validator=[attr.validators.instance_of(str), name_validator])
    # decode must come before default, look at default "default" factory method to see the relation.
    _decode: bool = attr.ib(default=False, kw_only=True, validator=attr.validators.instance_of(bool))
    _default: AnyStr = attr.ib(validator=attr.validators.instance_of((str, bytes)))
    _max_length: Optional[int] = attr.ib(
        default=None, validator=attr.validators.optional(attr.validators.instance_of(int))
    )
    _order: str = attr.ib(default='!', validator=attr.validators.in_(['<', '>', '!', '@', '=']))
    _value: AnyStr = attr.ib(init=False)

    def __attrs_post_init__(self):
        if self._max_length is not None and len(self._default) > self._max_length:
            raise ValueError(f'default must be less or equal than maximum length ({self._max_length})')

        if isinstance(self._default, str) and not self._decode:
            raise TypeError('default must be bytes')

        if isinstance(self._default, bytes) and self._decode:
            raise TypeError('default must be a string')

        self._value = self._default

    @_default.default
    def _get_default_value(self) -> AnyStr:
        return 'kifurushi' if self._decode else b'kifurushi'

    @property
    def name(self) -> str:
        """Returns field's name"""
        return self._name

    @property
    def default(self) -> AnyStr:
        """Returns field's default value."""
        return self._default

    @property
    def max_length(self) -> Optional[int]:
        """Returns the optional max length of the field."""
        return self._max_length

    @property
    def value(self) -> AnyStr:
        """Returns internal string."""
        return self._value

    @value.setter
    def value(self, value: AnyStr) -> None:
        if not isinstance(value, (str, bytes)):
            raise TypeError(f'{self._name} value must be bytes or string but you provided {value}')

        if isinstance(value, str) and not self._decode:
            raise TypeError(f'{self._name} value must be bytes but you provided {value}')

        if isinstance(value, bytes) and self._decode:
            raise TypeError(f'{self._name} value must be a string but you provided {value}')

        if self._max_length is not None and len(value) > self._max_length:
            raise ValueError(f'{self._name} value must be less or equal than maximum length ({self._max_length})')

        self._value = value

    def raw(self, packet: 'Packet' = None) -> bytes:
        """
        Returns the representation of field value in bytes as it will be sent on the network.

        **Parameters:**

        * **packet:** The optional packet currently parsing the raw `data` bytes. It can be useful
        when the computation of the field value depends on other fields.
        """
        if self._decode:
            return self._value.encode()
        return self._value

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
        Sets internal string value and returns remaining bytes from `data` if any.

        **Parameters:**

        * **data:**: The raw data currently being parsed by a packet object.
        * **packet:** The optional packet currently parsing  the raw `data` bytes. For a variable string field,
        it may be useful because the length of the field often depends on another field and we can retrieve if
        from the packet.
        """

    def random_value(self) -> AnyStr:
        """
        Returns a random string or bytes. The length of the string is either the max length if given or the length
        of the default attribute.
        """
        length = self._max_length if self._max_length is not None else len(self._default)
        random_string = rand_string(length)
        return random_string if self._decode else random_string.encode()
