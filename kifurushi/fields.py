"""This module contains different field implementation"""

import attr

from .abc import Field
from .random_values import (
    LEFT_BYTE, RIGHT_BYTE, LEFT_SIGNED_BYTE, RIGHT_SIGNED_BYTE, LEFT_SHORT, RIGHT_SHORT,
    LEFT_SIGNED_SHORT, RIGHT_SIGNED_SHORT, LEFT_INT, RIGHT_INT, LEFT_SIGNED_INT, RIGHT_SIGNED_INT,
    LEFT_LONG, RIGHT_LONG, LEFT_SIGNED_LONG, RIGHT_SIGNED_LONG
)


def numeric_validator(field: Field, attribute: attr.Attribute, value: int) -> None:
    attribute_name = attribute.name if attribute.name[0] != '_' else attribute.name[1:]
    message = '{name} attribute must be between {left} and {right}'
    class_name = field.__class__.__name__
    if class_name == 'ByteField' and not LEFT_BYTE <= value <= RIGHT_BYTE:
        raise ValueError(message.format(name=attribute_name, left=LEFT_BYTE, right=RIGHT_BYTE))

    if class_name == 'SignedByteField' and not LEFT_SIGNED_BYTE <= value <= RIGHT_SIGNED_BYTE:
        raise ValueError(message.format(name=attribute_name, left=LEFT_SIGNED_BYTE, right=RIGHT_SIGNED_BYTE))

    if class_name == 'ShortField' and not LEFT_SHORT <= value <= RIGHT_SHORT:
        raise ValueError(message.format(name=attribute_name, left=LEFT_SHORT, right=RIGHT_SHORT))

    if class_name == 'SignedShortField' and not LEFT_SIGNED_SHORT <= value <= RIGHT_SIGNED_SHORT:
        raise ValueError(message.format(name=attribute_name, left=LEFT_SIGNED_SHORT, right=RIGHT_SIGNED_SHORT))

    if class_name == 'IntField' and not LEFT_INT <= value <= RIGHT_INT:
        raise ValueError(message.format(name=attribute_name, left=LEFT_INT, right=RIGHT_INT))

    if class_name == 'SignedIntField' and not LEFT_SIGNED_INT <= value <= RIGHT_SIGNED_INT:
        raise ValueError(message.format(name=attribute_name, left=LEFT_SIGNED_INT, right=RIGHT_SIGNED_INT))

    if class_name == 'LongField' and not LEFT_LONG <= value <= RIGHT_LONG:
        raise ValueError(message.format(name=attribute_name, left=LEFT_LONG, right=RIGHT_LONG))

    if class_name == 'SignedLongField' and not LEFT_SIGNED_LONG <= value <= RIGHT_SIGNED_LONG:
        raise ValueError(message.format(name=attribute_name, left=LEFT_SIGNED_LONG, right=RIGHT_SIGNED_LONG))


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
