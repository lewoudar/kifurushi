import attr
import pytest

from kifurushi.abc import Field
from kifurushi import random_values


@attr.s(repr=False)
class DummyField(Field):
    _value: int = attr.ib(init=False, validator=attr.validators.instance_of(int))

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        pass


# noinspection PyArgumentList
class TestFieldClass:

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

        assert field.clone() == field

    # tests raw property

    def test_should_return_correct_byte_value_when_calling_raw_property(self):
        field = DummyField('foo', 2, format='i')
        field.value = 4

        assert b'\x00\x00\x00\x04' == field.raw
