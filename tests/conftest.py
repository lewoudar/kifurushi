import pytest
from scapy.all import *


@pytest.fixture(scope='session')
def mini_ip():
    """Returns a scapy packet used to check validity of kifurushi packet."""

    class MiniIP(Packet):
        name = 'mini ip'
        fields_desc = [
            BitField('version', 4, 4),
            BitField('IHL', 5, 4),
            ShortField('length', 20),
            ShortEnumField('identification', 1, {1: 'lion', 5: 'turtle', 7: 'python'}),
            FlagsField('flags', 2, 3, ['MF', 'DF', 'evil']),
            BitField('frag', 0, 13),
        ]

    return MiniIP()


@pytest.fixture(scope='session')
def raw_mini_ip(mini_ip):
    """Returns bytes corresponding to the raw value of mini_ip packet."""
    return raw(mini_ip)


@pytest.fixture(scope='session')
def mini_ip_hexdump(mini_ip):
    """Returns tcpdump like hexadecimal view of mini_ip packet."""
    return hexdump(mini_ip, dump=True)
