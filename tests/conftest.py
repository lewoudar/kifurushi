import pytest
from scapy.compat import raw
from scapy.fields import BitField, ShortField, ShortEnumField, FlagsField, ByteField
from scapy.packet import Packet
from scapy.utils import hexdump, checksum

from .helpers import MiniIP


@pytest.fixture(scope='session')
def mini_ip():
    """Returns a scapy packet used to check validity of kifurushi packet."""

    class ScapyMiniIP(Packet):
        name = 'mini ip'
        fields_desc = [
            BitField('version', 4, 4),
            BitField('IHL', 5, 4),
            ShortField('length', 20),
            ShortEnumField('identification', 1, {1: 'lion', 5: 'turtle', 7: 'python'}),
            FlagsField('flags', 2, 3, ['MF', 'DF', 'evil']),
            BitField('frag', 0, 13),
        ]

    return ScapyMiniIP()


@pytest.fixture(scope='session')
def mini_body():
    """Returns a scapy packet used to test data extraction via extract_layers function"""

    class ScapyMiniBody(Packet):
        name = 'mini body'
        fields_desc = [
            ShortField('arms', 2),
            ByteField('head', 1),
            ShortField('foot', 2),
            ShortField('teeth', 32),
            ByteField('nose', 1)
        ]

    return ScapyMiniBody()


@pytest.fixture(scope='session')
def raw_mini_ip(mini_ip):
    """Returns bytes corresponding to the raw value of mini_ip packet."""
    return raw(mini_ip)


@pytest.fixture(scope='session')
def raw_mini_body(mini_body):
    """Returns bytes corresponding to the raw value of mini_body packet."""
    return raw(mini_body)


@pytest.fixture(scope='session')
def mini_ip_hexdump(mini_ip):
    """Returns tcpdump like hexadecimal view of mini_ip packet."""
    return hexdump(mini_ip, dump=True)


@pytest.fixture(scope='session')
def mini_ip_checksum(raw_mini_ip):
    """Returns mini_ip checksum."""
    return checksum(raw_mini_ip)


@pytest.fixture()
def custom_ip():
    """An instance of our custom MiniIP class used to validate Packet class implementation."""
    return MiniIP()
