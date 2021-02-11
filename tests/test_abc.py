from typing import Union

import attr
import pytest

from kifurushi.abc import Field, CommonField, VariableStringField
from kifurushi.utils import random_values


class TestField:
    """Tests field class"""

    @pytest.mark.parametrize('attribute', [
        'size', 'default', 'value', 'raw', 'clone', 'struct_format',
        'random_value', 'compute_value'
    ])
    def test_should_check_field_class_defines_all_common_attributes_and_methods(self, attribute):
        assert getattr(Field, attribute, None) is not None

    def test_should_prove_field_has_a_default_clone_method_implementation(self):
        class FakeField(Field):
            @property
            def size(self) -> int:
                return 0

            @property
            def default(self) -> Union[int, str]:
                return 0

            @property
            def value(self) -> Union[int, str]:
                return 0

            @property
            def struct_format(self) -> str:
                return '!b'

            @property
            def raw(self) -> bytes:
                return b''

            def random_value(self) -> Union[int, str]:
                return 0

            def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
                return b''

            def __repr__(self):
                return 'Field'

        field = FakeField()
        cloned_field = field.clone()

        assert cloned_field == field
        assert cloned_field is not field


@attr.s(repr=False)
class DummyField(CommonField):
    _value: int = attr.ib(init=False, validator=attr.validators.instance_of(int))

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        pass


# noinspection PyArgumentList
class TestCommonField:
    """Tests class CommonField"""

    def test_should_prove_class_inherit_from_base_field_class(self):
        assert issubclass(CommonField, Field)

    def test_should_correctly_instantiate_attributes(self):
        field = DummyField('foo', 2, format='b')

        assert field.name == 'foo'
        assert field.default == field.value == 2
        assert field.size == 1
        assert field.struct_format == '!b'

    @pytest.mark.parametrize('arguments', [
        {'name': 4, 'default': 2},
        {'name': 'foo', 'default': 2, 'format': 4}
    ])
    def test_should_raise_error_for_string_attributes_giving_wrong_values(self, arguments):
        with pytest.raises(TypeError):
            DummyField(**arguments)

    @pytest.mark.parametrize('name', [' hello', 'hello ', 'foo-bar', 'f@o'])
    def test_should_raise_error_when_given_name_is_not_correct(self, name):
        with pytest.raises(ValueError) as exc_info:
            DummyField(name, 2, format='b')

        assert (
            'DummyField name must starts with a letter and follow standard'
            f' rules for declaring a variable in python but you provided {name}'
        ) == str(exc_info.value)

    # tests format attribute

    @pytest.mark.parametrize('_format', ['o', 'xs'])
    def test_should_raise_error_when_format_is_incorrect(self, _format):
        with pytest.raises(ValueError):
            DummyField('foo', 'hello', format=_format)

    @pytest.mark.parametrize('_format', ['b', 'B', 'h', 'H', 'i', 'I', 'q', 'Q', '02s', '12s'])
    def test_should_not_raise_error_when_giving_correct_format(self, _format):
        try:
            DummyField('foo', 'hello', format=_format)
        except ValueError:
            pytest.fail(f'unexpected error when instantiating field with format: {_format}')

    # tests order attribute

    @pytest.mark.parametrize('order', [4, 'foo'])
    def test_should_raise_error_when_order_is_not_correct(self, order):
        with pytest.raises(ValueError):
            DummyField('foo', 2, format='b', order=order)

    @pytest.mark.parametrize('order', ['!', '@', '<', '>', '='])
    def test_should_not_raise_error_when_order_is_a_correct_value(self, order):
        try:
            DummyField('foo', 2, format='b', order=order)
        except ValueError:
            pytest.fail(f'unexpected error when instantiating field with order: {order}')

    # tests value attribute

    def test_should_raise_error_when_setting_bad_value(self):
        field = DummyField('foo', 2, format='b')
        with pytest.raises(TypeError):
            field.value = '3'

    # tests random_value method

    @pytest.mark.parametrize(('_format', 'left', 'right'), [
        ('b', random_values.LEFT_SIGNED_BYTE, random_values.RIGHT_SIGNED_BYTE),
        ('B', random_values.LEFT_BYTE, random_values.RIGHT_BYTE),
        ('h', random_values.LEFT_SIGNED_SHORT, random_values.RIGHT_SIGNED_SHORT),
        ('H', random_values.LEFT_SHORT, random_values.RIGHT_SHORT),
        ('i', random_values.LEFT_SIGNED_INT, random_values.RIGHT_SIGNED_INT),
        ('I', random_values.LEFT_INT, random_values.RIGHT_INT),
        ('q', random_values.LEFT_SIGNED_LONG, random_values.RIGHT_SIGNED_LONG),
        ('Q', random_values.LEFT_LONG, random_values.RIGHT_LONG)
    ])
    def test_should_call_correct_random_function_when_calling_random_value(self, _format, left, right):
        field = DummyField('foo', 2, format=_format)
        value = field.random_value()

        assert left <= value <= right

    def test_should_return_random_string_when_calling_random_value_for_string_field(self):
        field = DummyField('foo', 'hello', format='25s')
        value = field.random_value()

        assert 25 == len(value)
        assert isinstance(value, str)

    # tests field representation

    def test_should_return_correct_field_representation(self):
        field = DummyField('foo', 2, format='b')
        field.value = 3

        assert '<DummyField: name=foo, value=3, default=2>' == repr(field)

    # tests clone method

    def test_should_return_a_comparable_object_when_calling_clone_method(self):
        field = DummyField('foo', 2, format='i')
        field.value = 3
        cloned_field = field.clone()

        assert cloned_field == field
        assert cloned_field is not field

    # tests raw property

    def test_should_return_correct_byte_value_when_calling_raw_property(self):
        field = DummyField('foo', 2, format='i')
        field.value = 4

        assert b'\x00\x00\x00\x04' == field.raw


class DummyStringField(VariableStringField):

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        pass


class TestVariableStringField:
    """Tests class VariableStringField"""

    def test_should_prove_class_inherit_from_base_field_class(self):
        assert issubclass(VariableStringField, Field)

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('name', [b'hello', 4.3])
    def test_should_raise_error_when_name_is_not_a_string(self, name):
        with pytest.raises(TypeError):
            DummyStringField(name)

    @pytest.mark.parametrize('name', [' hello', 'hello ', 'foo-bar', 'f@o'])
    def test_should_raise_error_when_giving_name_is_not_correct(self, name):
        with pytest.raises(ValueError) as exc_info:
            DummyStringField(name)

        assert (
            'DummyStringField name must starts with a letter and follow standard'
            f' rules for declaring a variable in python but you provided {name}'
        ) == str(exc_info.value)

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('default', [b'hello', 4.3])
    def test_should_raise_error_when_default_is_not_a_string(self, default):
        with pytest.raises(TypeError):
            DummyStringField('foo', default)

    def test_should_return_kifurushi_when_no_default_value_is_given(self):
        field = DummyStringField('foo')
        assert 'kifurushi' == field.default

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('max_length', [4.5, '4'])
    def test_should_raise_error_when_max_length_is_not_an_integer(self, max_length):
        with pytest.raises(TypeError):
            DummyStringField('foo', 'bar', max_length)

    def test_should_raise_error_when_default_length_is_greater_than_max_length(self):
        with pytest.raises(ValueError) as exc_info:
            DummyStringField('foo', default='hell yeah', max_length=6)

        assert f'default must be less or equal than maximum length (6)' == str(exc_info.value)

    @pytest.mark.parametrize('order', [4, '<='])
    def test_should_raise_error_when_order_does_not_have_a_correct_value(self, order):
        with pytest.raises(ValueError):
            DummyStringField('foo', order=order)

    def test_should_correctly_instantiate_field(self):
        field = DummyStringField('fruit', 'apple')

        assert 'fruit' == field.name
        assert 'apple' == field.default == field.value
        assert field.max_length is None

    # test field representation

    def test_should_returns_correct_representation_when_calling_repr_function(self):
        field = DummyStringField('fruit', 'apple', 50)

        assert (
                   f'<{field.__class__.__name__}: name={field.name}, value={field.value},'
                   f' default={field.default}, max_length={field.max_length}>'
               ) == repr(field)

    # test value setting

    @pytest.mark.parametrize('value', [b'hello', 4])
    def test_should_raise_error_when_giving_value_is_not_a_string(self, value):
        field = DummyStringField('apple')
        with pytest.raises(TypeError) as exc_info:
            field.value = value

        assert f'{field.name} value must be a string but you provided {value}' == str(exc_info.value)

    def test_should_raise_error_when_giving_value_has_a_length_greater_than_max_length_if_given(self):
        field = DummyStringField('fruit', max_length=20)
        with pytest.raises(ValueError) as exc_info:
            field.value = 'b' * 21

        assert f'{field.name} value must be less or equal than maximum length (20)' == str(exc_info.value)

    def test_should_set_value_when_giving_correct_input(self):
        field = DummyStringField('fruit', max_length=20)
        given_value = 'b' * 20
        field.value = given_value

        assert given_value == field.value

    # tests of raw property

    def test_raw_property_returns_correct_value(self):
        field = DummyStringField('fruit')
        field.value = 'banana'

        assert b'banana' == field.raw

    # test of struct_format property

    def test_struct_format_returns_correct_value(self):
        default = 'banana'
        field = DummyStringField('fruit', default)
        assert f'{field._order}{len(default)}' == field.struct_format

        value = 'hello'
        field.value = value
        assert f'{field._order}{len(value)}' == field.struct_format

    # test of size property

    def test_size_property_returns_correct_value(self):
        value = 'banana'
        field = DummyStringField('fruit', 'hello')
        field.value = value

        assert len(value) == field.size

    # test of clone method

    def test_should_return_a_copy_of_the_field_when_calling_clone_method(self):
        field = DummyStringField('fruit')
        cloned_field = field.clone()

        assert cloned_field == field
        assert cloned_field is not field

    # test of random_value method

    @pytest.mark.parametrize(('arguments', 'length'), [
        ({'default': 'hellboy'}, 7),
        ({'max_length': 30}, 30)
    ])
    def test_should_return_a_correct_random_string_when_calling_random_value(self, arguments, length):
        field = DummyStringField('foo', **arguments)
        random_string = field.random_value()

        assert isinstance(random_string, str)
        assert length == len(random_string)
