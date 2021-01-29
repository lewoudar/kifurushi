import enum
import struct
from typing import Tuple

import pytest

from kifurushi.abc import Field
from kifurushi.fields import (
    ByteField, SignedByteField, ShortField, SignedShortField, IntField, SignedIntField, LongField, SignedLongField,
    enum_to_dict, ByteEnumField, SignedByteEnumField, ShortEnumField, SignedShortEnumField, IntEnumField,
    SignedIntEnumField, LongEnumField, SignedLongEnumField, FixedStringField, FieldPart, BitsField, ByteBitsField,
    ShortBitsField, IntBitsField, LongBitsField
)
from kifurushi.random_values import (
    LEFT_BYTE, RIGHT_BYTE, LEFT_SIGNED_BYTE, RIGHT_SIGNED_BYTE, LEFT_SHORT, RIGHT_SHORT,
    LEFT_SIGNED_SHORT, RIGHT_SIGNED_SHORT, LEFT_INT, RIGHT_INT, LEFT_SIGNED_INT, RIGHT_SIGNED_INT,
    LEFT_LONG, RIGHT_LONG, LEFT_SIGNED_LONG, RIGHT_SIGNED_LONG
)

out_of_boundaries_parametrize = pytest.mark.parametrize(('field_class', 'left', 'right'), [
    (ByteField, LEFT_BYTE - 1, RIGHT_BYTE + 1),
    (SignedByteField, LEFT_SIGNED_BYTE - 1, RIGHT_SIGNED_BYTE + 1),
    (ShortField, LEFT_SHORT - 1, RIGHT_SHORT + 1),
    (SignedShortField, LEFT_SIGNED_SHORT - 1, RIGHT_SIGNED_SHORT + 1),
    (IntField, LEFT_INT - 1, RIGHT_INT + 1),
    (SignedIntField, LEFT_SIGNED_INT - 1, RIGHT_SIGNED_INT + 1),
    (LongField, LEFT_LONG - 1, RIGHT_LONG + 1),
    (SignedLongField, LEFT_SIGNED_LONG - 1, RIGHT_SIGNED_LONG + 1)
])

size_format_parametrize = pytest.mark.parametrize(('size', 'format_'), [
    (4, 'B'),
    (8, 'H'),
    (16, 'I'),
    (32, 'Q')
])

WITHIN_BOUNDARIES = [
    (ByteField, LEFT_BYTE),
    (ByteField, RIGHT_BYTE),
    (SignedByteField, LEFT_SIGNED_BYTE),
    (SignedByteField, RIGHT_SIGNED_BYTE),
    (ShortField, LEFT_SHORT),
    (ShortField, RIGHT_SHORT),
    (SignedShortField, LEFT_SIGNED_SHORT),
    (SignedShortField, RIGHT_SIGNED_SHORT),
    (IntField, LEFT_INT),
    (IntField, RIGHT_INT),
    (SignedIntField, LEFT_SIGNED_INT),
    (SignedIntField, RIGHT_SIGNED_INT),
    (LongField, LEFT_LONG),
    (LongField, RIGHT_LONG),
    (SignedLongField, LEFT_SIGNED_LONG),
    (SignedLongField, RIGHT_SIGNED_LONG)
]


# noinspection PyArgumentList
class TestNumericField:
    """Tests classes ByteField, ShortField, IntField, LongField and their signed version"""

    @pytest.mark.parametrize('value', ['4', 4.5])
    @pytest.mark.parametrize('field_class', [
        ByteField, SignedByteField, ShortField, SignedShortField,
        IntField, SignedIntField, LongField, SignedLongField
    ])
    def test_should_raise_error_if_default_attribute_is_not_a_string(self, value, field_class):
        with pytest.raises(TypeError):
            field_class('foo', value)

    @out_of_boundaries_parametrize
    def test_should_raise_error_if_default_attribute_is_out_of_boundaries(self, field_class, left, right):
        for value in [left, right]:
            with pytest.raises(ValueError) as exc_info:
                field_class('foo', value)

            assert f'foo default must be between {left + 1} and {right - 1}' == str(exc_info.value)

    @pytest.mark.parametrize(('field_class', 'default'), WITHIN_BOUNDARIES)
    def test_should_not_raise_error_when_default_attribute_is_correct(self, field_class, default):
        try:
            field_class('foo', default)
        except ValueError:
            pytest.fail(f'unexpected error when setting default attribute with value {default}')

    @out_of_boundaries_parametrize
    def test_should_raise_error_when_value_attribute_is_out_of_boundaries(self, field_class, left, right):
        for value in [left, right]:
            field = field_class('foo', 2)
            with pytest.raises(ValueError) as exc_info:
                field.value = value

            assert f'foo value must be between {left + 1} and {right - 1}' == str(exc_info.value)

    @pytest.mark.parametrize(('field_class', 'value'), WITHIN_BOUNDARIES)
    def test_should_set_value_attribute_when_giving_correct_value(self, field_class, value):
        field = field_class('foo', 2)
        field.value = value

        assert value == field.value

    @pytest.mark.parametrize(('field_class', 'size', 'struct_format'), [
        (ByteField, 1, '!B'),
        (SignedByteField, 1, '!b'),
        (ShortField, 2, '!H'),
        (SignedShortField, 2, '!h'),
        (IntField, 4, '!I'),
        (SignedIntField, 4, '!i'),
        (LongField, 8, '!Q'),
        (SignedLongField, 8, '!q')
    ])
    def test_should_correctly_instantiate_field(self, field_class, size, struct_format):
        field = field_class('foo', 2)

        assert 'foo' == field.name
        assert 2 == field.default == field.value
        assert struct_format == field.struct_format
        assert size == field.size
        assert not field._hex

    @pytest.mark.parametrize('hexadecimal', [True, False])
    @pytest.mark.parametrize('field_class', [
        ByteField, SignedByteField, ShortField, SignedShortField,
        IntField, SignedIntField, LongField, SignedLongField
    ])
    def test_should_correctly_represent_field(self, hexadecimal, field_class):
        field = field_class('foo', 2, hex=hexadecimal)
        field.value = 17
        if hexadecimal:
            assert f'<{field_class.__name__}: name=foo, value=0x11, default=0x2>' == repr(field)
        else:
            assert f'<{field_class.__name__}: name=foo, value=17, default=2>' == repr(field)

    @pytest.mark.parametrize(('field_class', 'format_', 'value'), [
        (ByteField, 'B', 6),
        (SignedByteField, 'b', -6),
        (ShortField, 'H', 6),
        (SignedShortField, 'h', -6),
        (IntField, 'I', 6),
        (SignedIntField, 'i', -6),
        (LongField, 'Q', 6),
        (SignedLongField, 'q', -6)
    ])
    def test_should_correctly_compute_value_and_return_remaining_bytes(self, field_class, format_, value):
        field = field_class('foo', 2)
        data = struct.pack(f'!{format_}5s', value, b'hello')
        remaining_data = field.compute_value(data)
        assert b'hello' == remaining_data
        assert value == field.value


class TestEnumToDict:
    """Tests function enum_to_dict"""

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('value', [[1, 2], {1: 'hello'}])
    def test_should_return_given_value_when_value_is_not_an_enum_class(self, value):
        assert value == enum_to_dict(value)

    def test_should_return_dict_when_giving_an_enum_class(self):
        class Disney(enum.Enum):
            MICKEY = 1
            MINNIE = 2

        assert {1: 'MICKEY', 2: 'MINNIE'} == enum_to_dict(Disney)


# noinspection PyArgumentList
class TestEnumFields:
    """Tests all enum fields"""

    @pytest.mark.parametrize(('field_class', 'parent_class'), [
        (ByteEnumField, ByteField),
        (SignedByteEnumField, SignedByteField),
        (ShortEnumField, ShortField),
        (SignedShortEnumField, SignedShortField),
        (IntEnumField, IntField),
        (SignedIntEnumField, SignedIntField),
        (LongEnumField, LongField),
        (SignedLongEnumField, SignedLongField)
    ])
    def test_should_check_enum_field_inherit_the_right_class(self, field_class, parent_class):
        assert issubclass(field_class, parent_class)

    @pytest.mark.parametrize('enumeration', [
        {'hello': 2},
        [(2, 'hello')],
        {2: 3.4}
    ])
    @pytest.mark.parametrize('field_class', [
        ByteEnumField, SignedByteEnumField, ShortEnumField, SignedShortEnumField,
        IntEnumField, SignedIntEnumField, LongEnumField, SignedLongEnumField
    ])
    def test_should_raise_error_when_enumeration_is_not_correct(self, enumeration, field_class):
        with pytest.raises(TypeError):
            field_class('foo', 2, enumeration)

    @pytest.mark.parametrize(('field_class', 'left', 'right'), [
        (ByteEnumField, LEFT_BYTE - 1, RIGHT_BYTE + 1),
        (SignedByteEnumField, LEFT_SIGNED_BYTE - 1, RIGHT_SIGNED_BYTE + 1),
        (ShortEnumField, LEFT_SHORT - 1, RIGHT_SHORT + 1),
        (SignedShortEnumField, LEFT_SIGNED_SHORT - 1, RIGHT_SIGNED_SHORT + 1),
        (IntEnumField, LEFT_INT - 1, RIGHT_INT + 1),
        (SignedIntEnumField, LEFT_SIGNED_INT - 1, RIGHT_SIGNED_INT + 1),
        (LongEnumField, LEFT_LONG - 1, RIGHT_LONG + 1),
        (SignedLongEnumField, LEFT_SIGNED_LONG - 1, RIGHT_SIGNED_LONG + 1)
    ])
    def test_should_raise_error_when_key_value_is_out_of_field_boundaries(self, field_class, left, right):
        for value in [left, right]:
            enumeration = {value: 'hello'}
            with pytest.raises(ValueError) as exc_info:
                field_class('foo', 2, enumeration)

            assert (f'all keys in enumeration attribute must be '
                    f'between {left + 1} and {right - 1}') == str(exc_info.value)

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('enumeration', [
        {1: 'mickey', 2: 'minnie'},
        enum.Enum('Disney', 'mickey minnie')
    ])
    @pytest.mark.parametrize('field_class', [
        ByteEnumField, SignedByteEnumField, ShortEnumField, SignedShortEnumField,
        IntEnumField, SignedIntEnumField, LongEnumField, SignedLongEnumField
    ])
    def test_should_correctly_instantiate_enum_field(self, enumeration, field_class):
        field = field_class('foo', 2, enumeration)
        assert 'foo' == field.name
        assert 2 == field.default == field.value
        assert {1: 'mickey', 2: 'minnie'} == field.enumeration


class TestFixedStringField:
    """Tests class FixedStringField"""

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('value', [b'hello', 4])
    def test_should_raise_error_when_default_attribute_is_not_a_string(self, value):
        with pytest.raises(TypeError) as exc_info:
            FixedStringField('foo', value, 8)

        assert f'default must be a string but you provided {value}' == str(exc_info.value)

    @pytest.mark.parametrize('value', [4.5, '4', -1])
    def test_should_raise_error_when_length_attribute_is_not_a_positive_integer(self, value):
        with pytest.raises(TypeError) as exc_info:
            FixedStringField('foo', 'hello', value)

        assert f'length must be a positive integer but you provided {value}' == str(exc_info.value)

    @pytest.mark.parametrize('value', ['b' * 10, 'b' * 6])
    def test_should_raise_error_if_default_length_is_different_than_specified_length(self, value):
        with pytest.raises(ValueError) as exc_info:
            FixedStringField('foo', value, 8)

        assert 'default length is different from the one given as third argument' == str(exc_info.value)

    def test_should_correctly_instantiate_field(self):
        field = FixedStringField('foo', 'h' * 8, 8)

        assert 'foo' == field.name
        assert 'h' * 8 == field.default == field.value
        assert 8 == field.size
        assert '!8s' == field.struct_format

    # test of raw property

    def test_raw_property_returns_correct_value(self):
        value = 'h' * 8
        field = FixedStringField('foo', value, 8)

        assert value.encode() == field.raw

    # test of value property

    @pytest.mark.parametrize('value', [b'hello', 4])
    def test_should_raise_error_when_setting_value_with_another_one_which_is_not_a_string(self, value):
        field = FixedStringField('foo', 'h' * 8, 8)
        with pytest.raises(TypeError) as exc_info:
            field.value = value

        assert f'{field.name} value must be a string but you provided {value}' == str(exc_info.value)

    @pytest.mark.parametrize('value', ['b' * 10, 'b' * 6])
    def test_should_raise_error_when_giving_value_is_greater_than_length_authorized(self, value):
        field = FixedStringField('foo', 'h' * 8, 8)
        with pytest.raises(ValueError) as exc_info:
            field.value = value

        assert f'the length of {field.name} value must be equal to {field._length}' == str(exc_info.value)

    def test_should_not_raise_error_when_setting_value_with_a_correct_one(self):
        field = FixedStringField('foo', 'h' * 8, 8)
        value = 'b' * 8
        try:
            field.value = value
        except (ValueError, TypeError):
            pytest.fail(f'unexpected error when setting value with {value}')

    # test of compute_value method

    def test_should_correctly_compute_string_and_return_remaining_bytes(self):
        field = FixedStringField('foo', 'h' * 8, 8)
        data = struct.pack('!8sB', b'b' * 8, 2)
        remaining_bytes = field.compute_value(data)

        assert remaining_bytes == struct.pack('!B', 2)
        assert 'b' * 8 == field.value


# noinspection PyTypeChecker
class TestFieldPart:
    """Tests class FieldPart"""

    @pytest.mark.parametrize('name', [b'name', 2])
    def test_should_raise_error_when_name_is_not_a_string(self, name):
        with pytest.raises(TypeError):
            FieldPart(name, 2, 2)

    @pytest.mark.parametrize('default', [4.5, '4'])
    def test_should_raise_error_when_default_is_not_an_integer(self, default):
        with pytest.raises(TypeError):
            FieldPart('part', default, 3)

    @pytest.mark.parametrize('default', [-1, 8])
    def test_should_raise_error_when_default_is_not_in_valid_boundaries(self, default):
        with pytest.raises(ValueError) as exc_info:
            FieldPart('part', default, 3)

        assert f'default must be between 0 and 7 but you provided {default}' == str(exc_info.value)

    @pytest.mark.parametrize('size', [4.5, '4'])
    def test_should_raise_error_when_size_is_not_an_integer(self, size):
        with pytest.raises(TypeError):
            FieldPart('part', 2, size)

    @pytest.mark.parametrize('enumeration', [
        {'hello': 2},
        [(2, 'hello')],
        {2: 3.4}
    ])
    def test_should_raise_error_when_enumeration_is_not_correct(self, enumeration):
        with pytest.raises(TypeError):
            FieldPart('part', 2, 3, enumeration)

    @pytest.mark.parametrize('enumeration', [
        {1: 'MF', 2: 'DF', 4: 'reserved'},
        enum.IntFlag('Flag', 'MF DF reserved')
    ])
    def test_should_correctly_instantiate_byte_part_object(self, enumeration):
        # these are flags present in IPV4 header :D
        # For more information, you can look here: https://en.wikipedia.org/wiki/IPv4
        part = FieldPart('flags', 0b010, 3, enumeration)

        assert 'flags' == part.name
        assert 2 == part.default == part.value
        assert 3 == part.size
        assert {1: 'MF', 2: 'DF', 4: 'reserved'} == part.enumeration

    # test of value property

    @pytest.mark.parametrize('value', [b'value', 4.5])
    def test_should_raise_error_when_value_set_is_not_of_correct_type(self, value):
        part = FieldPart('banana', 2, 3)
        with pytest.raises(TypeError) as exc_info:
            part.value = value

        assert f'{part.name} value must be a positive integer but you provided {value}' == str(exc_info.value)

    @pytest.mark.parametrize('value', [-1, 8])
    def test_should_raise_error_when_value_is_not_valid_boundaries(self, value):
        part = FieldPart('banana', 2, 3)
        with pytest.raises(ValueError) as exc_info:
            part.value = value

        assert f'{part.name} value must be between 0 and 7 but you provided {value}' == str(exc_info.value)

    def test_should_set_field_part_value_when_given_value_is_correct(self):
        part = FieldPart('part', 2, 3)
        given_value = 6
        part.value = given_value

        assert given_value == part.value

    # test of __repr__ method

    @pytest.mark.parametrize(('enumeration', 'representation'), [
        ({1: 'MF', 2: 'DF', 4: 'reserved'}, 'FieldPart(name=flags, default=2, value=DF)'),
        (None, 'FieldPart(name=flags, default=2, value=2)')
    ])
    def test_should_correctly_represent_field_part(self, enumeration, representation):
        part = FieldPart('flags', 0b010, 3, enumeration)

        assert representation == repr(part)

    # test of clone method

    def test_should_return_a_correct_copy_of_field_part_when_calling_clone_method(self):
        part = FieldPart('part', 2, 3)
        cloned_part = part.clone()

        assert cloned_part == part
        assert cloned_part is not part


class TestBitsField:
    """Tests class BitsField"""

    def test_should_prove_class_inherit_base_field_class(self):
        assert issubclass(BitsField, Field)

    @pytest.mark.parametrize(('parts', 'error'), [
        ({'foo': 2}, TypeError),
        ([], ValueError)
    ])
    def test_should_raise_error_when_parts_is_not_correct(self, parts, error):
        with pytest.raises(error) as exc_info:
            BitsField(parts, 'B')

        if error is ValueError:
            assert 'parts must not be an empty list' == str(exc_info.value)

    @pytest.mark.parametrize(('size_1', 'size_2'), [
        (3, 4),
        (4, 5)
    ])
    def test_should_raise_error_when_parts_size_is_not_correct(self, size_1, size_2):
        with pytest.raises(ValueError) as exc_info:
            BitsField(
                parts=[FieldPart('version', 4, size_1), FieldPart('IHL', 5, size_2)],
                format='B'  # 1 byte (8 bits)
            )
        size = size_1 + size_2
        assert (f'the sum in bits of the different FieldPart ({size})'
                f' is different from the field size (8)') == str(exc_info.value)

    @pytest.mark.parametrize('value', [4, b'h', 'h'])
    def test_should_raise_error_when_format_is_not_correct(self, value):
        with pytest.raises(ValueError):
            BitsField([FieldPart('part', 2, 3)], value)

    @staticmethod
    def get_int_from_tuple(size: int, value: Tuple[int, ...]) -> int:
        # if we have a tuple (5, 6), their binary representation is (101, 110)
        # so if each item must fill a size of 4 bits, we need to add extra leading 0 before concatenating the values
        str_value = ''
        for item in value:
            bin_item = bin(item)[2:]
            str_value += '0' * (size - len(bin_item)) + bin_item
        return int(str_value, base=2)

    def test_should_correctly_instantiate_bits_field(self):
        field_parts = [FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)]
        field = BitsField(parts=field_parts, format='B')

        assert field_parts == field.parts
        assert 1 == field.size
        assert '!B' == field.struct_format
        assert self.get_int_from_tuple(4, (4, 5)) == field.default

    def test_should_correctly_represent_bits_field(self):
        field_parts = [FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)]
        field = BitsField(parts=field_parts, format='B')

        assert ('BitsField(FieldPart(name=version, default=4, value=4),'
                ' FieldPart(name=IHL, default=5, value=5))') == repr(field)

    # test of value_as_tuple property

    def test_should_return_correct_value_when_calling_value_as_tuple_property(self):
        field = BitsField(parts=[FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)], format='B')
        assert (4, 5) == field.value_as_tuple

    # test of value property

    def test_should_return_correct_value_when_calling_value_property(self):
        field = BitsField(parts=[FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)], format='B')
        assert int('01000101', base=2) == field.value

    @pytest.mark.parametrize('value', ['4', [3, 5]])
    def test_should_raise_error_when_value_is_not_integer_or_tuple(self, value):
        field = BitsField(parts=[FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)], format='B')
        with pytest.raises(TypeError) as exc_info:
            field.value = value

        assert 'value must be an integer or a tuple of integers' == str(exc_info.value)

    def test_should_raise_error_when_tuple_is_empty(self):
        field = BitsField(parts=[FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)], format='B')
        with pytest.raises(ValueError) as exc_info:
            field.value = ()

        assert 'value must not be an empty tuple' == str(exc_info.value)

    def test_should_raise_error_when_all_items_in_tuple_are_not_integers(self):
        field = BitsField(parts=[FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)], format='B')
        with pytest.raises(ValueError) as exc_info:
            field.value = (2, 3.4)

        assert 'all items in tuple must be integers' == str(exc_info.value)

    def test_should_raise_error_when_tuple_length_is_different_field_parts_length(self):
        field = BitsField(parts=[FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)], format='B')
        with pytest.raises(ValueError) as exc_info:
            field.value = (2, 3, 4)

        assert 'tuple length is different from field parts length' == str(exc_info.value)

    @pytest.mark.parametrize(('size', 'format_', 'value_1', 'value_2'), [
        (4, 'B', -1, 2 ** 4),
        (8, 'H', -1, 2 ** 8),
        (16, 'I', -1, 2 ** 16),
        (32, 'Q', -1, 2 ** 32)
    ])
    def test_should_raise_error_when_items_dont_have_a_correct_value(self, size, format_, value_1, value_2):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        for value in [value_1, value_2]:
            with pytest.raises(ValueError) as exc_info:
                field.value = (value, 4)

            message = f'item version must be between 0 and {2 ** size - 1} according to the field part size'
            assert message == str(exc_info.value)

    @pytest.mark.parametrize(('size', 'format_', 'value_1', 'value_2'), [
        (4, 'B', -1, RIGHT_BYTE + 1),
        (8, 'H', -1, RIGHT_SHORT + 1),
        (16, 'I', -1, RIGHT_INT + 1),
        (32, 'Q', -1, RIGHT_LONG + 1)
    ])
    def test_should_raise_error_when_int_value_is_not_in_valid_boundaries(self, size, format_, value_1, value_2):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        for value in [value_1, value_2]:
            with pytest.raises(ValueError) as exc_info:
                field.value = value

            assert f'integer value must be between 0 and {value_2 - 1}' == str(exc_info.value)

    @size_format_parametrize
    def test_should_not_raise_error_when_setting_a_correct_tuple_value(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        value = (5, 6)
        try:
            field.value = value
        except ValueError:
            pytest.fail(f'unexpected error when setting value with {value}')

        assert value == field.value_as_tuple

    @size_format_parametrize
    def test_should_not_raise_error_when_setting_a_correct_int_value(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        value = (5, 6)
        int_value = self.get_int_from_tuple(size, value)
        try:
            field.value = int_value
        except ValueError:
            pytest.fail(f'unexpected error when setting value with {value}')

        assert value == field.value_as_tuple

    # test of raw property

    @size_format_parametrize
    def test_should_return_byte_value_when_calling_raw_property(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        assert struct.pack(f'!{format_}', field.value) == field.raw

    # test of clone method

    def test_should_return_a_copy_of_the_object_when_calling_clone_method(self):
        field = BitsField(parts=[FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)], format='B')
        cloned_field = field.clone()

        assert cloned_field == field
        assert cloned_field is not field
        # check the parts attribute of cloned field is not a shallow copy
        for i, part in enumerate(cloned_field.parts):
            assert part is not field.parts[i]

    # test of random_value method

    @pytest.mark.parametrize(('size', 'format_', 'right_value'), [
        (4, 'B', RIGHT_BYTE),
        (8, 'H', RIGHT_SHORT),
        (16, 'I', RIGHT_INT),
        (32, 'Q', RIGHT_LONG)
    ])
    def test_should_call_randint_function_with_correct_values(self, mocker, size, format_, right_value):
        randint_mock = mocker.patch('random.randint', return_value=2)
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)

        assert 2 == field.random_value()
        randint_mock.assert_called_once_with(0, right_value)

    # test of compute_value method

    @size_format_parametrize
    def test_should_compute_internal_field_part_value_when_calling_compute_value_method(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        value = (8, 11)
        data = struct.pack(f'!{format_}5s', self.get_int_from_tuple(size, value), b'hello')
        remaining_data = field.compute_value(data)

        assert b'hello' == remaining_data
        assert (8, 11) == field.value_as_tuple

    # test of __getitem__ method

    @size_format_parametrize
    def test_should_raise_error_when_trying_to_access_field_part_giving_a_wrong_name(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        with pytest.raises(KeyError) as exc_info:
            assert field['foo']

        assert f"'no field part was found with name foo'" == str(exc_info.value)

    @size_format_parametrize
    def test_should_return_field_part_given_its_name(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        field_part = field['IHL']

        assert field_part.name == 'IHL'

    # test of get_field_part_value method

    @size_format_parametrize
    def test_should_raise_error_if_name_is_not_present_in_field_parts(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        name = 'hello'
        with pytest.raises(KeyError) as exc_info:
            field.get_field_part_value(name)

        assert f"'no field part was found with name {name}'" == str(exc_info.value)

    @size_format_parametrize
    def test_should_return_field_part_value_when_giving_correct_name(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        assert 4 == field.get_field_part_value('version')

    # test of set_field_part_value

    @size_format_parametrize
    def test_should_raise_error_if_name_is_not_present_in_field_parts_when_setting_value(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        name = 'hello'
        with pytest.raises(KeyError) as exc_info:
            field.set_field_part_value(name, 6)

        assert f"'no field part was found with name {name}'" == str(exc_info.value)

    @size_format_parametrize
    def test_should_set_field_part_value_when_giving_correct_name_and_value(self, size, format_):
        field = BitsField(parts=[FieldPart('version', 4, size), FieldPart('IHL', 5, size)], format=format_)
        field.set_field_part_value('version', 6)

        assert (6, 5) == field.value_as_tuple


class TestSpecializedBitsFields:
    """Tests classes ByteBitsField, ShortBitsField, IntBitsField, LongBitsField"""

    @pytest.mark.parametrize('bit_class', [ByteBitsField, ShortBitsField, IntBitsField, LongBitsField])
    def test_should_check_classes_inherit_from_bits_field(self, bit_class):
        assert issubclass(bit_class, BitsField)

    @pytest.mark.parametrize(('bit_class', 'size', 'format_'), [
        (ByteBitsField, 4, 'B'),
        (ShortBitsField, 8, 'H'),
        (IntBitsField, 16, 'I'),
        (LongBitsField, 32, 'Q')
    ])
    def test_should_correctly_instantiate_object(self, bit_class, size, format_):
        field_parts = [FieldPart('version', 4, size), FieldPart('IHL', 5, size)]
        # Pycharm 2020.3 has an issue related to overriding attributes on a "attrs" class
        # noinspection PyArgumentList
        field = bit_class(field_parts)

        assert size * 2 == field.size * 8
        assert field_parts == field.parts
        assert f'!{format_}' == field.struct_format
        assert (4, 5) == field.value_as_tuple
        assert field.default == field.value
