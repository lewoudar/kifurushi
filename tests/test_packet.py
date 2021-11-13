from typing import List

import pytest

from kifurushi.abc import VariableStringField, Field
from kifurushi.fields import (
    FieldPart, ByteBitsField, ShortField, ShortEnumField, ShortBitsField, FixedStringField, ConditionalField
)
from kifurushi.packet import create_packet_class, extract_layers, Packet
from kifurushi.utils.random_values import RIGHT_SHORT
from tests.helpers import Identification, Flags, MiniIP, MiniBody


class CustomStringField(VariableStringField):

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        pass


# noinspection PyArgumentList
@pytest.fixture(scope='module')
def mini_ip_fields() -> List[Field]:
    """Returns list of fields used in various packet tests."""
    return [
        ByteBitsField([FieldPart('version', 4, 4), FieldPart('ihl', 5, 4)]),
        ShortField('length', 20),
        ShortEnumField('identification', 1, Identification),
        ShortBitsField([FieldPart('flags', 0b010, 3, Flags), FieldPart('offset', 0, 13)], hex=True),
    ]


class TestCreatePacketClass:
    """Tests function create_packet_class"""

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('class_name', [b'Foo', 4])
    def test_should_raise_error_when_class_name_does_not_have_correct_type(self, class_name, mini_ip_fields):
        with pytest.raises(TypeError) as exc_info:
            create_packet_class(class_name, mini_ip_fields)

        assert f'class name must be a string but you provided {class_name}' == str(exc_info.value)

    @pytest.mark.parametrize('fields', [(), []])
    def test_should_raise_error_when_list_field_is_empty(self, fields):
        with pytest.raises(ValueError) as exc_info:
            create_packet_class('MiniIP', fields)

        assert 'the list of fields must not be empty' == str(exc_info.value)

    # noinspection PyTypeChecker,PyArgumentList
    @pytest.mark.parametrize(('fields', 'message'), [
        ('hello', f'each item in the list must be a Field object but you provided h'),
        (
                [ShortField('length', 20), b'fast food'],
                f'each item in the list must be a Field object but you provided {b"fast food"}'
        )
    ])
    def test_should_raise_error_if_an_item_in_the_list_is_not_a_field_object(self, fields, message):
        with pytest.raises(TypeError) as exc_info:
            create_packet_class('MiniIP', fields)

        assert message == str(exc_info.value)

    def test_should_create_class_with_correct_attributes_when_giving_correct_input(self, mini_ip_fields):
        for fields in [mini_ip_fields, tuple(mini_ip_fields)]:
            mini_ip_class = create_packet_class('MiniIP', fields)
            assert issubclass(mini_ip_class, Packet)
            assert mini_ip_class.__fields__ == fields


# noinspection PyArgumentList
class ErrorPacket1(Packet):
    __fields__ = [
        ShortField('hello', 2),
        ByteBitsField([FieldPart('hello', 4, 4), FieldPart('foo', 4, 4)])  # hello field comes in double
    ]


# noinspection PyArgumentList
class ErrorPacket2(Packet):
    __fields__ = [
        ShortField('hello', 2),
        ShortField('potatoes', 3),
        ShortField('players', 2),
        ShortField('hello', 3)  # hello field comes in double
    ]


# noinspection PyArgumentList
class Fruit(Packet):
    __fields__ = [
        ShortField('apples', 2),
        ConditionalField(ShortField('pie', 1), lambda p: p.apples <= 2),
        ConditionalField(ShortField('juice', 1), lambda p: p.apples > 2)
    ]


# noinspection PyArgumentList
class TestPacketClass:
    """Tests Packet class implementation through the use of custom MiniIP class"""

    @pytest.mark.parametrize('packet_class', [ErrorPacket1, ErrorPacket2])
    def test_should_raise_error_when_a_field_name_is_defined_more_than_once(self, packet_class):
        with pytest.raises(AttributeError) as exc_info:
            packet_class()

        assert 'you already have a field with name hello' == str(exc_info.value)

    def test_should_raise_error_when_given_attribute_is_not_a_valid_field_name(self):
        with pytest.raises(AttributeError) as exc_info:
            MiniIP(version=5, foo=4, ihl=6)

        assert 'there is no attribute with name foo' == str(exc_info.value)

    def test_should_correctly_instantiate_packet_when_giving_no_arguments(self):
        mini_ip = MiniIP()
        assert mini_ip.version == 4
        assert mini_ip.ihl == 5
        assert mini_ip.length == 20
        assert mini_ip.identification == 1
        assert mini_ip.flags == 2
        assert mini_ip.offset == 0

        assert mini_ip.fields == mini_ip._fields == mini_ip.__fields__
        assert mini_ip.fields is not mini_ip.__fields__
        assert mini_ip.fields is not mini_ip._fields

    @pytest.mark.parametrize(('arguments', 'version', 'offset'), [
        ({'version': 5}, 5, 0),
        ({'version': 5, 'offset': 12}, 5, 12)
    ])
    def test_should_correctly_instantiate_packet_when_giving_correct_arguments(self, arguments, version, offset):
        mini_ip = MiniIP(**arguments)
        assert mini_ip.version == version
        assert mini_ip.length == 20
        assert mini_ip.identification == 1
        assert mini_ip.flags == 2
        assert mini_ip.offset == offset
        assert mini_ip.__fields__ != mini_ip.fields

    # test of __setattr__ method

    def test_should_respect_default_setattr_behaviour_when_given_name_is_not_a_field_name(self, custom_ip):
        custom_ip.foo = 'bar'
        assert custom_ip.foo == 'bar'

    @pytest.mark.parametrize(('field', 'value', 'error'), [
        (FixedStringField('game', 'pacman', 6, decode=True), 'super mario bros', ValueError),
        (ShortEnumField('identification', 1, Identification), 'youkoulele', ValueError),
        (ShortField('length', 3), 4.5, TypeError),
        (ShortBitsField([FieldPart('flags', 0b010, 3, Flags), FieldPart('offset', 0, 13)]), 'foo', ValueError),
    ])
    def test_should_raise_error_when_given_value_is_not_correct(self, field, value, error):
        custom_class = create_packet_class('Custom', [field])
        instance = custom_class()
        name = 'flags' if isinstance(field, ShortBitsField) else field.name
        with pytest.raises(error) as exc_info:
            setattr(instance, name, value)

        if name == 'identification':
            assert f'{name} has no value represented by {value}' == str(exc_info.value)

    @pytest.mark.parametrize(('field', 'value'), [
        (FixedStringField('game', 'pacman', 6, decode=True), 'foobar'),
        (CustomStringField('fruit', 'apple', decode=True), 'pineapple'),
        (ShortField('length', 3), 10),
    ])
    def test_should_set_field_value_when_giving_correct_name_and_value(self, field, value):
        custom_class = create_packet_class('Custom', [field])
        instance = custom_class()
        setattr(instance, field.name, value)
        assert getattr(instance, field.name) == value

    @pytest.mark.parametrize(('field', 'given_value', 'expected_value'), [
        (ShortEnumField('identification', 1, Identification), 3, 3),
        (ShortEnumField('identification', 1, Identification), Identification.lion.name, Identification.lion.value),
        (ShortEnumField('identification', 1, Identification), Identification.lion, Identification.lion.value)
    ])
    def test_should_set_enum_field_value_when_giving_correct_name_and_value(self, field, given_value, expected_value):
        custom_class = create_packet_class('Custom', [field])
        instance = custom_class()
        setattr(instance, field.name, given_value)
        assert getattr(instance, field.name) == expected_value

    @pytest.mark.parametrize(('given_value', 'expected_value'), [
        (Flags.df.value, Flags.df.value),
        (Flags.df.name, Flags.df.value),
        (Flags.df, Flags.df.value)
    ])
    def test_should_set_bits_field_value_when_giving_correct_name_and_value(self, given_value, expected_value):
        fields = [ShortBitsField([FieldPart('flags', 0b010, 3, Flags), FieldPart('offset', 0, 13)])]
        bit_class = create_packet_class('Bits', fields)
        instance = bit_class()
        instance.flags = given_value

        assert instance.flags == expected_value

    # test of raw property

    def test_should_correctly_compute_packet_byte_value_when_calling_raw_property(self, custom_ip, raw_mini_ip):
        assert raw_mini_ip == custom_ip.raw

    @pytest.mark.parametrize(('apples', 'pie', 'juice', 'data'), [
        (1, 1, 0, b'\x00\x01\x00\x01'),
        (8, 0, 3, b'\x00\x08\x00\x03')
    ])
    def test_should_compute_packet_byte_value_taking_in_account_conditional_fields(self, apples, pie, juice, data):
        fruit = Fruit(apples=apples, pie=pie, juice=juice)
        assert data == fruit.raw

    # test of __bytes__ method

    def test_should_return_byte_value_when_calling_bytes_builtin_function(self, custom_ip):
        assert bytes(custom_ip) == custom_ip.raw

    # test of hexdump property

    def test_should_return_correct_hexadecimal_wireshark_view_when_calling_hexdump(self, custom_ip, mini_ip_hexdump):
        assert mini_ip_hexdump == custom_ip.hexdump

    # test of __eq__ method

    @pytest.mark.parametrize('value', [b'E\x00\x14\x00\x01@\x00', 4])
    def test_should_raise_error_when_comparing_packet_to_a_non_packet_object(self, custom_ip, value):
        with pytest.raises(NotImplementedError):
            custom_ip.__eq__(value)

    @pytest.mark.parametrize(('packet_1', 'packet_2', 'boolean'), [
        (MiniIP(), MiniIP(), True),
        (MiniIP(version=5), MiniIP(version=5), True),
        (MiniIP(version=5), MiniIP(), False)
    ])
    def test_should_correctly_compare_two_packets(self, packet_1, packet_2, boolean):
        result = packet_1 == packet_2
        assert result is boolean

    # test of __ne__ method

    @pytest.mark.parametrize('value', [b'E\x00\x14\x00\x01@\x00', 4])
    def test_should_raise_error_when_comparing_difference_between_packet_and_a_non_packet(self, custom_ip, value):
        with pytest.raises(NotImplementedError):
            custom_ip.__ne__(value)

    @pytest.mark.parametrize(('packet_1', 'packet_2', 'boolean'), [
        (MiniIP(), MiniIP(), False),
        (MiniIP(version=5), MiniIP(version=5), False),
        (MiniIP(version=5), MiniIP(), True)
    ])
    def test_should_correctly_compare_opposition_of_two_packets(self, packet_1, packet_2, boolean):
        result = packet_1 != packet_2
        assert result is boolean

    # test of clone method

    def test_should_return_a_copy_of_packet_when_calling_clone_method(self, custom_ip):
        cloned_ip = custom_ip.clone()

        assert isinstance(cloned_ip, MiniIP)
        assert cloned_ip == custom_ip
        assert cloned_ip is not custom_ip
        assert cloned_ip._fields is not custom_ip._fields
        assert cloned_ip._field_mapping is not custom_ip._field_mapping

    # test of from_bytes class method

    def test_should_create_packet_when_calling_from_bytes_method_with_raw_bytes(self):
        mini_ip = MiniIP(version=5, length=18)
        new_ip = MiniIP.from_bytes(mini_ip.raw)

        assert isinstance(new_ip, MiniIP)
        assert 5 == new_ip.version
        assert 18 == new_ip.length

    @pytest.mark.parametrize(('apples', 'pie', 'juice', 'data'), [
        (2, 2, 1, b'\x00\x02\x00\x02'),
        (4, 1, 2, b'\x00\x04\x00\x02')
    ])
    def test_should_create_packet_taking_in_account_conditional_field(self, apples, pie, juice, data):
        fruit = Fruit.from_bytes(data)

        assert fruit.apples == apples
        assert fruit.pie == pie
        assert fruit.juice == juice

    # test of random_packet class method

    def test_should_create_a_packet_with_random_values_when_calling_random_packet_method(self):
        mini_ip = MiniIP.random_packet()

        assert isinstance(mini_ip, MiniIP)
        assert 0 <= mini_ip.version <= 2 ** 4 - 1
        assert 0 <= mini_ip.ihl <= 2 ** 4 - 1
        assert 0 <= mini_ip.length <= RIGHT_SHORT
        assert 0 <= mini_ip.identification <= RIGHT_SHORT
        assert 0 <= mini_ip.flags <= 2 ** 3 - 1
        assert 0 <= mini_ip.offset <= 2 ** 13 - 1

    # test of evolve method

    def test_should_raise_error_when_calling_evolve_method_with_unknown_attributes(self, custom_ip):
        with pytest.raises(AttributeError) as exc_info:
            custom_ip.evolve(ihl=7, foo='bar')

        assert 'there is no attribute with name foo' == str(exc_info.value)

    def test_should_raise_error_when_calling_evolve_with_bad_value_for_an_attribute(self, custom_ip):
        with pytest.raises(ValueError) as exc_info:
            custom_ip.evolve(ihl='foo')

        assert 'ihl has no value represented by foo' == str(exc_info.value)

    def test_should_return_a_new_packet_with_updated_attributes_when_calling_evolve_method(self, custom_ip):
        new_ip = custom_ip.evolve(ihl=6)

        assert isinstance(new_ip, MiniIP)
        assert new_ip is not custom_ip
        assert 4 == new_ip.version
        assert 6 == new_ip.ihl
        assert 5 == custom_ip.ihl

    # test of __repr__ method

    @pytest.mark.parametrize(('value', 'hexadecimal'), [
        (20, False),
        ('0x14', True)
    ])
    def test_should_return_correct_packet_representation_when_calling_repr_function(
            self, custom_ip, value, hexadecimal
    ):
        custom_ip._fields[1]._hex = hexadecimal
        representation = f'<MiniIP: version=4, ihl=5, length={value}, identification=1, flags=0x2, offset=0x0>'
        assert representation == repr(custom_ip)

    @pytest.mark.parametrize(('apples', 'representation'), [
        (2, '<Fruit: apples=2, pie=1>'),
        (4, '<Fruit: apples=4, juice=1>')
    ])
    def test_should_represent_packet_taking_in_account_conditional_fields(self, apples, representation):
        fruit = Fruit(apples=apples)
        assert representation == repr(fruit)

    # test of show method

    @pytest.mark.parametrize(('value_1', 'value_2', 'hexadecimal'), [
        (18, 20, False),
        ('0x12', '0x14', True)
    ])
    def test_should_print_correct_packet_representation_when_calling_show_method(
            self, capsys, custom_ip, value_1, value_2, hexadecimal
    ):
        custom_ip._fields[1]._hex = hexadecimal
        custom_ip.length = 18
        custom_ip.ihl = 6
        custom_ip.show()
        captured = capsys.readouterr()
        output = (
            'version        : FieldPart of ByteBitsField = 4 (4)\n'
            'ihl            : FieldPart of ByteBitsField = 6 (5)\n'
            f'length         : ShortField = {value_1} ({value_2})\n'
            'identification : ShortEnumField = 1 (1)\n'
            'flags          : FieldPart of ShortBitsField = 0x2 (0x2)\n'
            'offset         : FieldPart of ShortBitsField = 0x0 (0x0)\n'
        )

        assert captured.out == output

    @pytest.mark.parametrize(('apples', 'representation'), [
        (2, 'apples : ShortField = 2 (2)\npie    : ShortField = 1 (1)\n'),
        (4, 'apples : ShortField = 4 (2)\njuice  : ShortField = 1 (1)\n')
    ])
    def test_should_print_packet_representation_taking_in_account_conditional_field(
            self, capsys, apples, representation
    ):
        fruit = Fruit(apples=apples)
        fruit.show()
        captured = capsys.readouterr()

        assert captured.out == representation


class TestExtractLayers:
    """Tests function extract_layers"""

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('data', ['foo', 4])
    def test_should_raise_error_if_data_is_not_of_type_bytes(self, data):
        with pytest.raises(TypeError) as exc_info:
            extract_layers(data, MiniIP)

        assert f'data must be bytes but you provided {data}' == str(exc_info.value)

    def test_should_raise_error_if_no_packet_class_is_provided(self):
        with pytest.raises(ValueError) as exc_info:
            extract_layers(b'foo')

        assert 'you must provide at least one Packet subclass to use for layer extraction' == str(exc_info.value)

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('wrong_value', ['foo', b'foo', 4])
    def test_should_raise_error_if_an_item_is_not_a_subclass_of_packet_class(self, wrong_value):
        with pytest.raises(TypeError) as exc_info:
            extract_layers(b'hello', MiniIP, wrong_value)

        message = (
            f'all arguments following the given data must be subclasses '
            f'of Packet class but you provided {wrong_value}'
        )
        assert message == str(exc_info.value)

    def test_should_extract_layers_when_giving_correct_input(self, raw_mini_ip, raw_mini_body):
        body, ip = extract_layers(raw_mini_body + raw_mini_ip, MiniBody, MiniIP)
        assert isinstance(body, MiniBody)
        assert isinstance(ip, MiniIP)

        assert body.arms == 2
        assert body.head == 1
        assert body.foot == 2
        assert body.teeth == 32
        assert body.nose == 1
        assert ip.version == 4
        assert ip.ihl == 5
        assert ip.identification
        assert ip.length == 20
