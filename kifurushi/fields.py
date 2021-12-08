"""This module contains field implementations."""
import enum
import inspect
import random
import struct
from copy import copy
from typing import Dict, Any, Union, Optional, List, Tuple, Callable, TYPE_CHECKING, AnyStr

import attr

from kifurushi.utils.random_values import (
    LEFT_BYTE, RIGHT_BYTE, LEFT_SIGNED_BYTE, RIGHT_SIGNED_BYTE, LEFT_SHORT, RIGHT_SHORT,
    LEFT_SIGNED_SHORT, RIGHT_SIGNED_SHORT, LEFT_INT, RIGHT_INT, LEFT_SIGNED_INT, RIGHT_SIGNED_INT,
    LEFT_LONG, RIGHT_LONG, LEFT_SIGNED_LONG, RIGHT_SIGNED_LONG
)
from .abc import Field, CommonField, name_validator

if TYPE_CHECKING:  # pragma: no cover
    from .packet import Packet


def check_boundaries(left: int, right: int, value: int, message: str) -> None:
    if not left <= value <= right:
        raise ValueError(message)


def numeric_validator(field: CommonField, attribute: attr.Attribute, value: int) -> None:
    attribute_name = attribute.name if attribute.name[0] != '_' else attribute.name[1:]
    message = '{name} {attribute_name} must be between {left} and {right}'
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
            check_boundaries(
                left, right, value, message.format(
                    name=field.name, attribute_name=attribute_name, left=left, right=right
                )
            )
            break


@attr.s(repr=False)
class HexMixin:
    """Mixin class to get hexadecimal representation of field value."""
    _hex: bool = attr.ib(kw_only=True, default=False, validator=[attr.validators.instance_of(bool)])

    def __repr__(self):
        value = hex(self._value) if self._hex else self._value
        default = hex(self._default) if self._hex else self._default
        return f'<{self.__class__.__name__}: name={self._name}, value={value}, default={default}>'

    @property
    def hex(self) -> bool:
        """Returns hex property value."""
        return self._hex

# Something important to note when implemented compute_value method of the different fields.
# If we don't have enough data to parse, we must return an empty byte. There are two reasons:
# 1. If we don't do it, the struct object will raise an error saying that it doesn't have enough data
# to compute the value
# 2. When parsing protocol data from the network we sometimes don't have enough data to interpret the
# whole message, so when we return empty data when computing a field, we ensure that the property
# "value_was_computed" remains to False. Also, if we return an empty byte the following packet fields to parse
# will also not affect "value_was_computed" property. So the end user will just have to check this property on all
# fields to know if the protocol was entirely parsed or not.
# As a consequence of the second point, when a field is successfully parsed, the property "value_was_computed"
# must be set to True.


@attr.s(repr=False)
class NumericField(HexMixin, CommonField):
    r"""
    Base class for many integer fields.

    **Parameters:**

    * **name:** The name of the field.
    * **default:** A default value for the field.
    * **format:** The format used by the [struct](https://docs.python.org/3/library/struct.html) module to allocate
    the correct size in bytes of the field value. The value provided is validated against the following regex:
    `r'b|B|h|h|H|i|I|q|Q|\d+s'`.
    * **order:** Order used to format raw data using the `struct` module. Defaults to `"!"` (network). Valid values are
    `"!"`, `"<"` (little-endian), `">"` (big-endian), `"@"` (native), `"="` (standard).
    """
    _default: int = attr.ib(validator=[attr.validators.instance_of(int), numeric_validator])
    _value: int = attr.ib(init=False, validator=[attr.validators.instance_of(int), numeric_validator])

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        if len(data) < self._size:
            return b''

        self._value = self._struct.unpack(data[:self._size])[0]
        self._value_was_computed = True
        return data[self._size:]


def enum_to_dict(enumeration: enum.EnumMeta) -> Any:
    if not isinstance(enumeration, enum.EnumMeta):
        return enumeration

    return {item.value: item.name for item in enumeration}


def enum_key_validator(field: CommonField, _, enumeration: Dict[int, str]) -> None:
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

    @property
    def enumeration(self) -> Dict[int, str]:
        """Returns dict enumeration given friendly name to a specific value."""
        return self._enumeration


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
    according to their meaning for the packet being forged / dissected. It will be used to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class SignedByteEnumField(SignedByteField, EnumMixin):
    """
    Similar to SignedByteField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. it will be used to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class ShortEnumField(ShortField, EnumMixin):
    """
    Similar to ShortField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. it will be used to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class SignedShortEnumField(SignedShortField, EnumMixin):
    """
    Similar to SignedShortField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. it will be used to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class IntEnumField(IntField, EnumMixin):
    """
    Similar to IntField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. it will be used to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class SignedIntEnumField(SignedIntField, EnumMixin):
    """
    Similar to SignedIntField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. it will be used to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class LongEnumField(LongField, EnumMixin):
    """
    Similar to LongField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. it will be used to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


@attr.s(repr=False, slots=True)
class SignedLongEnumField(SignedLongField, EnumMixin):
    """
    Similar to ByteField, but has a third mandatory field, a dict or enum mapping values to their name
    according to their meaning for the packet being forged / dissected. it will be used to pretty print
    value which can be useful when playing / debugging in the terminal.
    """


class FixedStringField(CommonField):
    """
    A field representing string data when length known in advance.

    **Parameters:**

    * **name:** The name of the field.
    * **default:** A default value for the field.
    * **length:** The length of the field.
    * **decode:** keyword-only boolean parameter to know if this field represents raw bytes or utf-8 text.
    Defaults to `False` meaning it is bytes which is considered by default.
    """

    def __init__(self, name: str, default: AnyStr, length: int, *, decode: bool = False):
        if not isinstance(default, (str, bytes)):
            raise TypeError(f'default must be a string or bytes but you provided {default}')

        if not isinstance(decode, bool):
            raise TypeError(f'decode must be a boolean but you provided {decode}')

        if not isinstance(length, int) or length <= 0:
            raise TypeError(f'length must be a positive integer but you provided {length}')

        if isinstance(default, str) and not decode:
            raise TypeError('default must be bytes')

        if isinstance(default, bytes) and decode:
            raise TypeError('default must be a string')

        if len(default) != length:
            raise ValueError('default length is different from the one given as third argument')

        self._length = length
        self._decode = decode
        super().__init__(name, default, format=f'{length}s')

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> Optional[bytes]:
        if len(data) < self._size:
            return b''

        value: bytes = self._struct.unpack(data[:self._size])[0]
        self._value = value.decode() if self._decode else value
        self._value_was_computed = True
        return data[self._size:]

    @property
    def value(self) -> AnyStr:
        """Returns internal string."""
        return self._value

    @value.setter
    def value(self, value: AnyStr) -> None:
        """Sets internal string."""
        if not isinstance(value, (str, bytes)):
            raise TypeError(f'{self._name} value must be a string or bytes but you provided {value}')

        if isinstance(value, str) and not self._decode:
            raise TypeError(f'{self._name} value must be bytes but you provided {value}')

        if isinstance(value, bytes) and self._decode:
            raise TypeError(f'{self._name} value must be a string but you provided {value}')

        if len(value) != self._length:
            raise ValueError(f'the length of {self._name} value must be equal to {self._length}')

        self._value = value

    def raw(self, packet: 'Packet' = None) -> bytes:
        """Returns bytes encoded value of the internal string."""
        if self._decode:
            return self._value.encode()
        return self._value

    def random_value(self) -> AnyStr:
        """Returns a random string."""
        random_string = super().random_value()
        return random_string if self._decode else random_string.encode()


@attr.s(slots=True, repr=False)
class FieldPart(HexMixin):
    """
    This class represents information to combine to form a BitsField object (signed byte, signed short, etc..).

    **Parameters:**

    * **name:** The name of field part.
    * **default:** The default value of the field part.
    * **size**: The number of bits this field part will take in the concrete field.
    * **enumeration:** A `dict` or `enum.Enum` enumeration given friendly name to a specific value. This
    attribute is optional.
    """
    _name: str = attr.ib(validator=[attr.validators.instance_of(str), name_validator])
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
            raise TypeError(f'{self._name} value must be a positive integer but you provided {value}')

        if value < 0 or value > self._max_value:
            raise ValueError(f'{self._name} value must be between 0 and {self._max_value} but you provided {value}')

        self._value = value

    @property
    def size(self) -> int:
        """Returns the number of bits this object will take in the BitsField object."""
        return self._size

    @property
    def hex(self) -> bool:
        """Returns hex property value."""
        return self._hex

    @hex.setter
    def hex(self, value: bool) -> None:
        """Sets hex property value"""
        if not isinstance(value, bool):
            raise TypeError(f'hex value must be a boolean but you provided {value}')
        self._hex = value

    @property
    def enumeration(self) -> Optional[Dict[int, str]]:
        """Returns dict enumeration given friendly name to a specific value."""
        return self._enumeration

    def clone(self) -> 'FieldPart':
        return copy(self)

    def __repr__(self):
        if self._enumeration is not None:
            value = self._enumeration.get(self._value, self._value)
            default = self._enumeration.get(self._default, self._default)
        else:
            value = hex(self._value) if self._hex else self._value
            default = hex(self._default) if self._hex else self._default
        return f'{self.__class__.__name__}(name={self._name}, default={default}, value={value})'


@attr.s(slots=True, repr=False)
class BitsField(HexMixin, Field):
    """
    A field representing bytes where where some bits have a specific meaning like we can see in IPV4 or TCP headers.

    **Parameters:**

    * **parts:** The list of FieldPart used to compose the field object.
    * **format:** The `struct` format used to represent the field in its binary representation. Valid values are "B"
    (1 byte), "H" (2 bytes), "I" (4 bytes) and "Q" (8 bytes).

    For example, if we take the [IPV4 header](https://en.wikipedia.org/wiki/IPv4) the first byte contains two
    information, the `version` (4 bits) and the `IHL` (4bits). To represent it we can define a field like the following:
    `BitsField([FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)], format='B')`
    """
    _parts: List[FieldPart] = attr.ib(validator=attr.validators.deep_iterable(
        member_validator=attr.validators.instance_of(FieldPart)
    ))
    _format: str = attr.ib(validator=attr.validators.in_(['B', 'H', 'I', 'Q']))
    _order: str = attr.ib(kw_only=True, default='!', validator=attr.validators.in_(['<', '>', '!', '@', '=']))
    _struct: struct.Struct = attr.ib(init=False)
    _size: int = attr.ib(init=False)

    @_parts.validator
    def _validate_parts(self, _, value: List[FieldPart]) -> None:
        if not value:
            raise ValueError('parts must not be an empty list')

    def __attrs_post_init__(self):
        _format = f'{self._order}{self._format}'
        self._struct = struct.Struct(_format)
        self._size = struct.calcsize(_format)

        parts_size = sum(part.size for part in self._parts)
        field_size_in_bits = self._size * 8
        if field_size_in_bits != parts_size:
            raise ValueError(
                f'the sum in bits of the different FieldPart ({parts_size}) is different'
                f' from the field size ({field_size_in_bits})'
            )
        # if hexadecimal representation is needed for this field, we need to forward
        # this information to all field parts
        if self._hex:
            for part in self._parts:
                part.hex = self._hex

    @property
    def parts(self) -> List[FieldPart]:
        """Returns the list of field parts of this field."""
        return self._parts

    @property
    def struct_format(self) -> str:
        return f'{self._order}{self._format}'

    @property
    def size(self) -> int:
        return self._size

    def __repr__(self):
        representation = f'{self.__class__.__name__}('
        for part in self._parts:
            representation += f'{part!r}, '
        representation = representation.strip(', ')
        representation += ')'
        return representation

    def _get_int_value_from_field_parts(self, default: bool = False) -> int:
        binary_representation = ''
        for field_part in self._parts:
            field_value = field_part.default if default else field_part.value
            bin_value = bin(field_value)[2:]
            if len(bin_value) < field_part.size:
                difference = field_part.size - len(bin_value)
                bin_value = '0' * difference + bin_value
            binary_representation += bin_value

        return int(binary_representation, base=2)

    @property
    def default(self) -> int:
        return self._get_int_value_from_field_parts(default=True)

    @property
    def value(self) -> int:
        """Returns the integer value corresponding to this field."""
        return self._get_int_value_from_field_parts()

    @property
    def value_as_tuple(self) -> Tuple[int, ...]:
        """Returns the value of each field part in a tuple."""
        return tuple(part.value for part in self._parts)

    @value.setter
    def value(self, value: Union[int, Tuple[int, ...]]) -> None:
        if not isinstance(value, (int, tuple)):
            raise TypeError('value must be an integer or a tuple of integers')

        if isinstance(value, tuple):
            if not value:
                raise ValueError('value must not be an empty tuple')

            if len(self._parts) != len(value):
                raise ValueError('tuple length is different from field parts length')

            for index, item in enumerate(value):
                if not isinstance(item, int):
                    raise ValueError('all items in tuple must be integers')

                field_part = self._parts[index]
                max_value = 2 ** field_part.size - 1
                if not 0 <= item <= max_value:
                    raise ValueError(
                        f'item {field_part.name} must be between 0 and {max_value} according to the field part size'
                    )
                # everything is ok, we can set the value to the field part
                field_part.value = item
        else:
            max_value = 2 ** (8 * self._size) - 1
            if not 0 <= value <= max_value:
                raise ValueError(f'integer value must be between 0 and {max_value}')

            # we add leading 0 if necessary in the binary representation
            bin_value = bin(value)[2:]
            bin_value_length = len(bin_value)
            size_in_bits = self._size * 8
            if bin_value_length < size_in_bits:
                bin_value = '0' * (size_in_bits - bin_value_length) + bin_value

            # we fill the value with each field part and take care to update bin_value
            # to the rest of the string not parsed
            for field_part in self._parts:
                str_value = bin_value[:field_part.size]
                field_part.value = int(str_value, base=2)
                bin_value = bin_value[field_part.size:]

    def raw(self, packet: 'Packet' = None) -> bytes:
        return self._struct.pack(self.value)

    def random_value(self) -> int:
        # bandit raises a B311 warning because it thinks we use random module for security/cryptographic purposes
        # since it is not the case here, we can disable this error with confidence
        # more about the error here: https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b311-random
        return random.randint(0, 2 ** (self._size * 8) - 1)  # nosec

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        """Sets internal value of each field part and returns remaining bytes if any."""
        if len(data) < self._size:
            return b''

        self.value = self._struct.unpack(data[:self._size])[0]
        self._value_was_computed = True
        return data[self._size:]

    def __getitem__(self, name: str) -> FieldPart:
        """Returns FieldPart which name corresponds to the one passed as argument."""
        for field_part in self._parts:
            if field_part.name == name:
                return field_part
        raise KeyError(f'no field part was found with name {name}')

    def clone(self) -> 'BitsField':
        """Returns a copy if the field ensuring that parts attribute of the cloned object is not a shallow copy."""
        cloned_field = copy(self)
        cloned_field._parts = [part.clone() for part in self._parts]
        return cloned_field

    def get_field_part_value(self, name: str) -> int:
        """
        Returns the value of a field part identified by its name.

        **Parameters:**

        * **name:** The name of the field part whose value is requested.
        """
        return self[name].value

    def set_field_part_value(self, name: str, value: int) -> None:
        """
        Sets the value of a field part identified by its name.

        **Parameters:**

        * **name:** The name of the field part whose value must be set.
        * **value:** The value to set to the field part.
        """
        self[name].value = value


@attr.s(slots=True, repr=False)
class ByteBitsField(BitsField):
    """A specialized BitsField class dealing with one unsigned byte field."""
    _format: str = attr.ib(default='B', init=False)


@attr.s(slots=True, repr=False)
class ShortBitsField(BitsField):
    """A specialized BitsField class dealing with a two unsigned bytes field."""
    _format: str = attr.ib(default='H', init=False)


@attr.s(slots=True, repr=False)
class IntBitsField(BitsField):
    """A specialized BitsField class dealing with a four unsigned bytes field."""
    _format: str = attr.ib(default='I', init=False)


@attr.s(slots=True, repr=False)
class LongBitsField(BitsField):
    """A specialized BitsField class dealing with an eight unsigned bytes field."""
    _format: str = attr.ib(default='Q', init=False)


@attr.s(slots=True, repr=False)
class ConditionalField(Field):
    _field: Field = attr.ib(validator=attr.validators.instance_of(Field))
    _condition: Callable[['Packet'], bool] = attr.ib(validator=attr.validators.is_callable())

    def __attrs_post_init__(self):
        signature = inspect.signature(self._condition)
        length = len(signature.parameters)
        if length != 1:
            raise TypeError(
                f'callable {self._condition.__name__} must takes one parameter (a packet instance)'
                f' but yours has {length}'
            )

    @property
    def size(self) -> int:
        return self._field.size

    @property
    def default(self) -> Union[int, str]:
        return self._field.default

    @property
    def value(self) -> Union[int, str]:
        return self._field.value

    @value.setter
    def value(self, value: Any) -> None:
        self._field.value = value

    @property
    def struct_format(self) -> str:
        return self._field.struct_format

    @property
    def condition(self) -> Callable[['Packet'], bool]:
        return self._condition

    def random_value(self) -> Union[int, str]:
        return self._field.random_value()

    def clone(self) -> 'ConditionalField':
        cloned_field = copy(self)
        cloned_field._field = self._field.clone()
        return cloned_field

    def raw(self, packet: 'Packet' = None) -> bytes:
        """
        Returns the representation of field value in bytes as it will be sent on the network.

        **Parameters:**

        * **packet:** The optional packet currently parsing the raw `data` bytes. It is used to check
        if the inner field should return its raw value or not.
        """
        if self._condition(packet):
            return self._field.raw(packet)
        return b''

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        """
        Optionally computes the field value from the raw bytes and returns remaining bytes to parse
        from `data` if any. The `self._condition` callback is used to determine if you need to treat
        `data`.

        **Parameters:**

        * **data:**: The raw data currently being parsed by a packet object.
        * **packet:** The optional packet currently parsing the raw `data` bytes. It can be useful
        when the value of the current field depends on other fields.
        """
        if self._condition(packet):
            remaining_data = self._field.compute_value(data, packet)
            self._value_was_computed = self._field.value_was_computed
            return remaining_data
        return data

    def __getattr__(self, item):
        # this is useful to call attributes defined in the inner field.
        return getattr(self._field, item)

    def __repr__(self):
        return repr(self._field)
