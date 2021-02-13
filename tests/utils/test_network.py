import pytest

from kifurushi.utils.network import smart_ord, hexdump, check_endian_transform, checksum
from ..helpers import MiniIP


class TestSmartOrd:
    """Tests function smart_ord."""

    @pytest.mark.parametrize(('argument', 'value'), [
        (65, 65),
        (b'A', 65)
    ])
    def test_should_return_correct_value_when_giving_correct_input(self, argument, value):
        assert value == smart_ord(argument)


class TestHexdump:
    """Tests function hexdump."""

    def test_should_return_correct_hexadecimal_wireshark_view_when_calling_hexdump(self, custom_ip, mini_ip_hexdump):
        assert mini_ip_hexdump == hexdump(custom_ip.raw)


class TestCheckEndianTransform:
    """tests function check_endian_transform."""

    def test_should_return_given_data_when_native_byte_order_is_big_endian(self, mocker):
        mocker.patch('struct.pack', return_value=b'\x00\x01')
        assert 2 == check_endian_transform(2)

    def test_should_return_correct_checksum_when_giving_integer_as_input(self):
        assert 5120 == check_endian_transform(20)


class TestChecksum:
    """Tests function checksum."""

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('data', [2, MiniIP()])
    def test_should_raise_error_when_giving_data_is_nor_bytes_neither_packet_instance(self, data):
        with pytest.raises(TypeError) as exc_info:
            checksum(data)

        assert f'data must be bytes but you provided {data}' == str(exc_info.value)

    def test_should_return_correct_checksum_when_calling_checksum_with_valid_argument(self, mini_ip_checksum):
        assert mini_ip_checksum == checksum(MiniIP().raw)
