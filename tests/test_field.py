import enum
import struct

import pytest

from kifurushi.fields import (
    ByteField, SignedByteField, ShortField, SignedShortField, IntField, SignedIntField, LongField, SignedLongField,
    enum_to_dict, ByteEnumField, SignedByteEnumField, ShortEnumField, SignedShortEnumField, IntEnumField,
    SignedIntEnumField, LongEnumField, SignedLongEnumField
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

            assert f'default attribute must be between {left + 1} and {right - 1}' == str(exc_info.value)

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

            assert f'value attribute must be between {left + 1} and {right - 1}' == str(exc_info.value)

    @pytest.mark.parametrize(('field_class', 'value'), WITHIN_BOUNDARIES)
    def test_should_not_raise_error_when_value_attribute_is_correct(self, field_class, value):
        field = field_class('foo', 2)
        try:
            field.value = value
        except ValueError:
            pytest.fail(f'unexpected error when setting value attribute with value {value}')

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

    @pytest.mark.parametrize(('field_class', '_format', 'value'), [
        (ByteField, 'B', 6),
        (SignedByteField, 'b', -6),
        (ShortField, 'H', 6),
        (SignedShortField, 'h', -6),
        (IntField, 'I', 6),
        (SignedIntField, 'i', -6),
        (LongField, 'Q', 6),
        (SignedLongField, 'q', -6)
    ])
    def test_should_correctly_compute_value_and_return_remaining_bytes(self, field_class, _format, value):
        field = field_class('foo', 2)
        data = struct.pack(f'!{_format}5s', value, b'hello')
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
class TestEnumByteField:

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
    def test_should_not_raise_error_when_enumeration_is_correct(self, enumeration, field_class):
        try:
            field_class('foo', 2, enumeration)
        except TypeError:
            pytest.fail(f'unexpected error when instantiating class with enumeration: {enumeration}')
