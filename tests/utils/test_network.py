import pytest

from kifurushi.utils.network import smart_ord, hexdump


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
