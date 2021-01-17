"""This module contains different field implementation"""
import enum
from typing import Dict, Any, Union, Optional

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
        """
        A field representing string data when length known in advance.

        **Parameters:**

        * **name:** The name of the field.
        * **default:** A default value for the field.
        * **length:** The length of the field.
        """
        if not isinstance(default, str):
            raise TypeError(f'default must be a string but you provided {default}')

        if not isinstance(length, int) or length <= 0:
            raise TypeError(f'length must be a positive integer but you provided {length}')

        if len(default) != length:
            raise ValueError('default length is different from the one given as third argument')

        self._length = length
        super().__init__(name, default, format=f'{length}s')

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        """Sets internal string value and returns remaining bytes."""
        value: bytes = self._struct.unpack(data[:self._size])[0]
        self._value = value.decode()
        return data[self._size:]

    @property
    def value(self) -> str:
        """Returns internal string."""
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        """Sets internal string."""
        if not isinstance(value, str):
            raise TypeError(f'value must be a string but you provided {value}')

        if len(value) != self._length:
            raise ValueError(f'value length must be equal to {self._length}')

        self._value = value

    @property
    def raw(self) -> bytes:
        """Returns bytes encoded value of the internal string."""
        return self._value.encode()


@attr.s(slots=True)
class FieldPart:
    """
    This class represents information to combine to form a BitsField object (signed byte, signed short, etc..).

    **Parameters:**

    * **name:** The name of field part.
    * **default:** The default value of the field part.
    * **size**: The number of bits this field part will take in the concrete field.
    * **enumeration:** A `dict` or `enum.Enum` enumeration given friendly name to a specific value. This
    attribute is optional.
    """
    _name: str = attr.ib(validator=attr.validators.instance_of(str))
    _default: int = attr.ib(validator=attr.validators.instance_of(int))
    _size: int = attr.ib(validator=attr.validators.instance_of(int))
    _value: int = attr.ib(init=False)
    _max_value: int = attr.ib(init=False)
    _enumeration: Optional[Union[enum.EnumMeta, Dict[int, str]]] = attr.ib(
        default=None,
        converter=enum_to_dict,
        validator=attr.validators.optional(attr.validators.deep_mapping(
            key_validator=attr.validators.instance_of(int),
            value_validator=attr.validators.instance_of(str),
            mapping_validator=attr.validators.instance_of(dict)
        )
        )
    )

    def __attrs_post_init__(self):
        self._max_value = 2 ** self._size - 1
        if self._default < 0 or self._default > self._max_value:
            raise ValueError(f'default must be between 0 and {self._max_value} but you provided {self._default}')

        self._value = self._default

    @property
    def name(self) -> str:
        """Returns the name of the field part."""
        return self._name

    @property
    def default(self) -> int:
        """Returns the default value of the field part."""
        return self._default

    @property
    def value(self) -> int:
        """Returns the current value of the field part."""
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        """Sets the current value of the field part."""
        if not isinstance(value, int):
            raise TypeError(f'value must be a positive integer but you provided {value}')

        if value < 0 or value > self._max_value:
            raise ValueError(f'value must be between 0 and {self._max_value} but you provided {value}')

    @property
    def size(self) -> int:
        """Returns the number of bits this object will take in the BitsField object."""
        return self._size

    @property
    def enumeration(self) -> Optional[Dict[int, str]]:
        """Returns dict enumeration given friendly name to a specific value."""
        return self._enumeration
