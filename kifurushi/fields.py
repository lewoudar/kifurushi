"""This module contains different field implementation"""
import enum
from typing import Dict, Any, Union

import attr

from .abc import Field
from .random_values import (
    LEFT_BYTE, RIGHT_BYTE, LEFT_SIGNED_BYTE, RIGHT_SIGNED_BYTE, LEFT_SHORT, RIGHT_SHORT,
    LEFT_SIGNED_SHORT, RIGHT_SIGNED_SHORT, LEFT_INT, RIGHT_INT, LEFT_SIGNED_INT, RIGHT_SIGNED_INT,
    LEFT_LONG, RIGHT_LONG, LEFT_SIGNED_LONG, RIGHT_SIGNED_LONG
)


def check_boundaries(left: int, right: int, value: int, message: str) -> None:
    if not left <= value <= right:
        raise ValueError(message)


def numeric_validator(field: Field, attribute: attr.Attribute, value: int) -> None:
    attribute_name = attribute.name if attribute.name[0] != '_' else attribute.name[1:]
    message = '{name} attribute must be between {left} and {right}'
    class_name = field.__class__.__name__
    for name, left, right in [
        ('ByteField', LEFT_BYTE, RIGHT_BYTE),
        ('SignedByteField', LEFT_SIGNED_BYTE, RIGHT_SIGNED_BYTE),
        ('ShortField', LEFT_SHORT, RIGHT_SHORT),
        ('SignedShortField', LEFT_SIGNED_SHORT, RIGHT_SIGNED_SHORT),
        ('IntField', LEFT_INT, RIGHT_INT),
        ('SignedIntField', LEFT_SIGNED_INT, RIGHT_SIGNED_INT),
        ('LongField', LEFT_LONG, RIGHT_LONG),
        ('SignedLongField', LEFT_SIGNED_LONG, RIGHT_SIGNED_LONG)
    ]:
        if class_name == name:
            check_boundaries(left, right, value, message.format(name=attribute_name, left=left, right=right))
            break


@attr.s(repr=False)
class HexMixin:
    """Mixin class to get hexadecimal representation of field value."""
    _hex: bool = attr.ib(kw_only=True, default=False, validator=[attr.validators.instance_of(bool)])

    def __repr__(self):
        value = hex(self._value) if self._hex else self._value
        default = hex(self._default) if self._hex else self._default
        return f'<{self.__class__.__name__}: name={self._name}, value={value}, default={default}>'


@attr.s(repr=False)
class NumericField(HexMixin, Field):
    """Base class for many numeric fields"""
    _default: int = attr.ib(validator=[attr.validators.instance_of(int), numeric_validator])
    _value: int = attr.ib(init=False, validator=[attr.validators.instance_of(int), numeric_validator])

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        self._value = self._struct.unpack(data[:self._size])[0]
        return data[self._size:]


def enum_to_dict(enumeration: enum.EnumMeta) -> Any:
    if not isinstance(enumeration, enum.EnumMeta):
        return enumeration

    return {item.value: item.name for item in enumeration}


def enum_key_validator(field: Field, _, enumeration: Dict[int, str]) -> None:
    class_name = field.__class__.__name__
    message = 'all keys in enumeration attribute must be between {left} and {right}'
    for key in enumeration:
        for name, left, right in [
            ('ByteEnumField', LEFT_BYTE, RIGHT_BYTE),
            ('SignedByteEnumField', LEFT_SIGNED_BYTE, RIGHT_SIGNED_BYTE),
            ('ShortEnumField', LEFT_SHORT, RIGHT_SHORT),
            ('SignedShortEnumField', LEFT_SIGNED_SHORT, RIGHT_SIGNED_SHORT),
            ('IntEnumField', LEFT_INT, RIGHT_INT),
            ('SignedIntEnumField', LEFT_SIGNED_INT, RIGHT_SIGNED_INT),
            ('LongEnumField', LEFT_LONG, RIGHT_LONG),
            ('SignedLongEnumField', LEFT_SIGNED_LONG, RIGHT_SIGNED_LONG)
        ]:
            if class_name == name:
                check_boundaries(left, right, key, message.format(left=left, right=right))
                break


@attr.s
class EnumMixin:
    _enumeration: Union[enum.EnumMeta, Dict[int, str]] = attr.ib(converter=enum_to_dict, validator=[
        attr.validators.deep_mapping(
            key_validator=attr.validators.instance_of(int),
            value_validator=attr.validators.instance_of(str),
            mapping_validator=attr.validators.instance_of(dict)
        ),
        enum_key_validator
    ])


# Normal fields

# TODO: see why slots attribute does not work as expected
@attr.s(repr=False, slots=True)
class ByteField(NumericField):
    """Field class to represent one unsigned byte of network information."""
    _format: str = attr.ib(init=False, default='B')


@attr.s(repr=False, slots=True)
class SignedByteField(NumericField):
    """Field class to represent one signed byte of network information."""
    _format: str = attr.ib(init=False, default='b')


@attr.s(repr=False, slots=True)
class ShortField(NumericField):
    """Field class to represent two unsigned bytes of network information."""
    _format: str = attr.ib(init=False, default='H')


@attr.s(repr=False, slots=True)
class SignedShortField(NumericField):
    """Field class to represent two signed bytes of network information."""
    _format: str = attr.ib(init=False, default='h')


@attr.s(repr=False, slots=True)
class IntField(NumericField):
    """Field class to represent four unsigned bytes of network information."""
    _format: str = attr.ib(init=False, default='I')


@attr.s(repr=False, slots=True)
class SignedIntField(NumericField):
    """Field class to represent four signed bytes of network information."""
    _format: str = attr.ib(init=False, default='i')


@attr.s(repr=False, slots=True)
class LongField(NumericField):
    """Field class to represent eight unsigned bytes of network information."""
    _format: str = attr.ib(init=False, default='Q')


@attr.s(repr=False, slots=True)
class SignedLongField(NumericField):
    """Field class to represent eight signed bytes of network information."""
    _format: str = attr.ib(init=False, default='q')


# Enum Fields

@attr.s(repr=False, slots=True)
class ByteEnumField(ByteField, EnumMixin):
    """
    Similar to ByteField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. It will be use to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class SignedByteEnumField(SignedByteField, EnumMixin):
    """
    Similar to SignedByteField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. It will be use to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class ShortEnumField(ShortField, EnumMixin):
    """
    Similar to ShortField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. It will be use to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class SignedShortEnumField(SignedShortField, EnumMixin):
    """
    Similar to SignedShortField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. It will be use to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class IntEnumField(IntField, EnumMixin):
    """
    Similar to IntField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. It will be use to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class SignedIntEnumField(SignedIntField, EnumMixin):
    """
    Similar to SignedIntField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. It will be use to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class LongEnumField(LongField, EnumMixin):
    """
    Similar to LongField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. It will be use to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class SignedLongEnumField(SignedLongField, EnumMixin):
    """
    Similar to ByteField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. It will be use to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


class FixedStringField(Field):

    def __init__(self, name: str, default: str, length: int):
        if not isinstance(default, str):
            raise TypeError(f'default must be a string but you provided {default}')

        if not isinstance(length, int) or length <= 0:
            raise TypeError(f'length must be a positive integer but you provided {length}')

        if len(default) != length:
            raise ValueError('default length is different from the one given as third argument')

        self._length = length
        super().__init__(name, default, format=f'{length}s')

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        value: bytes = self._struct.unpack(data[:self._size])[0]
        self._value = value.decode()
        return data[self._size:]

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f'value must be a string but you provided {value}')

        if len(value) != self._length:
            raise ValueError(f'value length must be equal to {self._length}')

        self._value = value

    @property
    def raw(self) -> bytes:
        return self._value.encode()
