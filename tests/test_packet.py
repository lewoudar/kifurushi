import enum
from typing import List

import pytest
from scapy.compat import raw

from kifurushi.abc import Field, VariableStringField
from kifurushi.fields import (
    ByteBitsField, FieldPart, ShortField, ShortEnumField, ShortBitsField, FixedStringField
)
from kifurushi.packet import Packet


class Flags(enum.Enum):
    reserved = 0
    df = 1
    mf = 2


class Identification(enum.Enum):
    lion = 1
    turtle = 5
    python = 7


class CustomStringField(VariableStringField):

    def compute_value(self, data: bytes, packet: 'Packet' = None) -> bytes:
        pass


# noinspection PyArgumentList
@pytest.fixture(scope='module')
def mini_ip_fields() -> List[Field]:
    """Returns list of fields used in various packet tests."""
    return [
        ByteBitsField([FieldPart('version', 4, 4), FieldPart('IHL', 5, 4)]),
        ShortField('length', 20),
        ShortEnumField('identification', 1, Identification),
        ShortBitsField([FieldPart('flags', 0b010, 3, Flags), FieldPart('offset', 0, 13)], hex=True),
    ]


@pytest.fixture(scope='module')
def packet(mini_ip_fields):
    """Returns a default packet used in various tests."""
    return Packet(mini_ip_fields)


# noinspection PyArgumentList
class TestPacket:
    """Tests Packet class"""

    @pytest.mark.parametrize('fields', [
        {'foo': 2},
        [ShortField('foo', 2), 4]
    ])
    def test_should_raise_error_when_fields_attribute_is_incorrect(self, fields):
        with pytest.raises(TypeError):
            Packet(fields)

    def test_should_correctly_instantiate_packet(self, packet, mini_ip_fields):
        assert packet._fields == mini_ip_fields
        assert {
                   'version': mini_ip_fields[0],
                   'IHL': mini_ip_fields[0],
                   'length': mini_ip_fields[1],
                   'identification': mini_ip_fields[2],
                   'flags': mini_ip_fields[3],
                   'offset': mini_ip_fields[3]
               } == packet._field_mapping

    # test of __getattr__ implementation

    def test_should_raise_error_when_accessing_attribute_which_name_does_not_exist_in_field_mapping(self, packet):
        with pytest.raises(AttributeError) as exc_info:
            assert packet.foo

        assert 'Packet has no attribute foo' == str(exc_info.value)

    def test_should_return_correct_value_when_accessing_attribute_with_field_name(self, packet):
        assert 4 == packet.version
        assert 2 == packet.flags
        assert 1 == packet.identification

    # test of __setattr__ implementation

    def test_should_raise_error_when_setting_attribute_which_name_does_not_exist_in_field_mapping(self, packet):
        with pytest.raises(AttributeError) as exc_info:
            packet.foo = 2

        assert 'Packet has no attribute foo' == str(exc_info.value)

    @pytest.mark.parametrize(('field', 'value', 'error'), [
        (FixedStringField('game', 'pacman', 6), 'super mario bros', ValueError),
        (ShortEnumField('identification', 1, Identification), 'youkoulele', ValueError),
        (ShortField('length', 3), 4.5, TypeError),
        (ShortBitsField([FieldPart('flags', 0b010, 3, Flags), FieldPart('offset', 0, 13)]), 'foo', ValueError),
    ])
    def test_should_raise_error_when_given_value_is_not_correct(self, field, value, error):
        packet = Packet([field])
        name = 'flags' if isinstance(field, ShortBitsField) else field.name
        with pytest.raises(error):
            setattr(packet, name, value)

    @pytest.mark.parametrize(('field', 'value'), [
        (FixedStringField('game', 'pacman', 6), 'foobar'),
        (CustomStringField('fruit', 'apple'), 'pineapple'),
        (ShortField('length', 3), 10),
    ])
    def test_should_set_field_value_when_giving_correct_name_and_value(self, field, value):
        packet = Packet([field])
        setattr(packet, field.name, value)
        assert value == getattr(packet, field.name)

    @pytest.mark.parametrize(('field', 'given_value', 'expected_value'), [
        (ShortEnumField('identification', 1, Identification), 3, 3),
        (ShortEnumField('identification', 1, Identification), Identification.lion.name, Identification.lion.value),
        (ShortEnumField('identification', 1, Identification), Identification.lion, Identification.lion.value)
    ])
    def test_should_set_enum_field_value_when_giving_correct_name_and_value(self, field, given_value, expected_value):
        packet = Packet([field])
        setattr(packet, field.name, given_value)
        assert expected_value == getattr(packet, field.name)

    @pytest.mark.parametrize(('given_value', 'expected_value'), [
        (Flags.df.value, Flags.df.value),
        (Flags.df.name, Flags.df.value),
        (Flags.df, Flags.df.value)
    ])
    def test_should_set_bits_field_value_when_giving_correct_name_and_value(self, given_value, expected_value):
        packet = Packet([ShortBitsField([FieldPart('flags', 0b010, 3, Flags), FieldPart('offset', 0, 13)])])
        packet.flags = given_value
        assert expected_value == packet.flags

    # test of raw property

    def test_should_correctly_compute_packet_byte_value_when_calling_raw_property(self, mini_ip_fields, raw_mini_ip):
        packet = Packet(mini_ip_fields)
        assert raw_mini_ip == packet.raw

    # test of __bytes__ method

    def test_should_return_byte_value_when_calling_bytes_builtin_function(self, mini_ip_fields):
        packet = Packet(mini_ip_fields)
        assert packet.raw == bytes(packet)

    # test of _smart_ord method

    @pytest.mark.parametrize(('argument', 'value'), [
        (65, 65),
        ('A', 65)
    ])
    def test_should_return_correct_value_when_giving_correct_input(self, mini_ip_fields, argument, value):
        packet = Packet(mini_ip_fields)
        assert value == packet._smart_ord(argument)

    # test of hexdump property

    def test_should_return_correct_hexadecimal_wireshark_view_when_calling_hexdump(
            self, mini_ip_fields, mini_ip_hexdump
    ):
        packet = Packet(mini_ip_fields)
        assert mini_ip_hexdump == packet.hexdump

    # test of clone method

    def test_should_return_a_copy_of_packet_object_when_calling_clone_method(self, mini_ip_fields):
        packet = Packet(mini_ip_fields)
        cloned_packet = packet.clone()

        assert cloned_packet == packet
        assert cloned_packet is not packet

    # test of get_packet_from_bytes method

    def test_should_return_a_packet_object_when_giving_raw_bytes_as_input(self, mini_ip, mini_ip_fields):
        mini_ip.identification = 5
        mini_ip.length = 18
        mini_ip.flags = 1
        packet = Packet(mini_ip_fields)
        another_packet = packet.get_packet_from_bytes(raw(mini_ip))

        assert isinstance(another_packet, Packet)
        assert another_packet.identification == 5
        assert another_packet.length == 18
        assert another_packet.flags == 1

    # test of __repr__ method

    @pytest.mark.parametrize(('value', 'hexadecimal'), [
        (20, False),
        ('0x14', True)
    ])
    def test_should_return_correct_packet_representation_when_calling_repr_function(
            self, mini_ip_fields, value, hexadecimal
    ):
        packet = Packet(mini_ip_fields)
        mini_ip_fields[1]._hex = hexadecimal
        assert f'<Packet: version=4, IHL=5, length={value}, identification=1, flags=0x2, offset=0x0>' == repr(packet)

    # test of show method

    @pytest.mark.parametrize(('value_1', 'value_2', 'hexadecimal'), [
        (18, 20, False),
        ('0x12', '0x14', True)
    ])
    def test_should_print_correct_packet_representation_when_calling_show_method(
            self, capsys, mini_ip_fields, value_1, value_2, hexadecimal
    ):
        packet = Packet(mini_ip_fields)
        mini_ip_fields[1]._hex = hexadecimal
        packet.length = 18
        packet.IHL = 6
        packet.show()
        captured = capsys.readouterr()
        output = (
            'version        : FieldPart of ByteBitsField = 4 (4)\n'
            'IHL            : FieldPart of ByteBitsField = 6 (5)\n'
            f'length         : ShortField = {value_1} ({value_2})\n'
            'identification : ShortEnumField = 1 (1)\n'
            'flags          : FieldPart of ShortBitsField = 0x2 (0x2)\n'
            'offset         : FieldPart of ShortBitsField = 0x0 (0x0)\n'
        )

        assert captured.out == output
