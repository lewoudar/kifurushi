"""
In this example we will implement a DNS packet according to RFC 1035.
There is a client example to show how to use it in real cases.
"""
import enum
import ipaddress
import random
import socket
import string
import struct
from typing import List, Optional, Dict, Any, Union

import attr

from kifurushi import (
    Packet, Field, ShortField, ShortEnumField, IntField, ConditionalField, VariableStringField, rand_string,
    ShortBitsField, FieldPart
)


def check_ip_address(_, _param, address: str) -> bool:
    try:
        ipaddress.ip_address(address)
        return True
    except ipaddress.AddressValueError:
        raise ValueError(f'{address} is not a valid ip address')


@attr.s(slots=True, repr=False)
class IPField(Field):
    _name: str = attr.ib(validator=attr.validators.instance_of(str))
    _default: str = attr.ib(validator=check_ip_address)
    _address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = attr.ib(init=False)

    def __attrs_post_init__(self):
        self._address = ipaddress.ip_address(self._default)

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        return 4 if self._address.version == 4 else 16

    @property
    def default(self) -> str:
        return self._default

    @property
    def value(self) -> str:
        return f'{self._address}'

    @value.setter
    def value(self, value: str) -> None:
        self._address = ipaddress.ip_address(value)

    @property
    def struct_format(self) -> str:
        # not really useful here
        return '!I' if self._address.version == 4 else '!IIII'

    def raw(self, packet: Packet = None) -> bytes:
        return self._address.packed

    def random_value(self) -> str:
        if self._address.version == 4:
            return f'{random.randint(1, 192)}.{random.randint(1, 168)}.0.1'
        else:
            return f'fe80::{random.randint(1, 8)}'

    def compute_value(self, data: bytes, packet: Packet = None) -> Optional[bytes]:
        cursor = 4 if self._address.version == 4 else 16
        self._address = ipaddress.ip_address(data[:cursor])
        return data[cursor:]

    def __repr__(self):
        return f'<{self.__class__.__name__}: default={self._default}, value={self._address}>'


@attr.s(slots=True, repr=False)
class DomainNameField(Field):
    """
    String fields can't be used for the dns name because of its particular way to serialize/deserialize data.
    So we need to create a custom field for that.
    """

    # it is a good idea to validate the given domain name, but I will not do it here
    _default: str = attr.ib(validator=attr.validators.instance_of(str))
    _name: str = attr.ib(default='name', validator=attr.validators.instance_of(str))
    _labels: List[str] = attr.ib(factory=list, init=False)
    _format: str = attr.ib(default='!', validator=attr.validators.in_(['!', '@', '<', '>', '=']))
    # we need the whole DNS packet in order to compute compressed names
    _raw_packet: bytes = attr.ib(default=b'', init=False)
    _pointer_labels: List[str] = attr.ib(factory=list, init=False)
    _pointer_value: int = attr.ib(default=0, init=False)

    def __attrs_post_init__(self):
        self._default = self._default if self._default.endswith('.') else f'{self._default}.'
        self.value = self._default

    @property
    def name(self) -> str:
        return self._name

    @property
    def raw_packet(self) -> bytes:
        return self._raw_packet

    @raw_packet.setter
    def raw_packet(self, data: bytes) -> None:
        self._raw_packet = data

    @property
    def default(self) -> str:
        return self._default

    @property
    def value(self) -> str:
        return '.'.join(label for label in [*self._labels, *self._pointer_labels]) + '.'

    @value.setter
    def value(self, value: str) -> None:
        # you probably want to check the given value but I will not do it here.
        if self._pointer_value:
            return
        value = value.rstrip('.')
        self._labels = value.split('.')

    @property
    def struct_format(self) -> str:
        result = f'{self._format}'
        for label in self._labels:
            result += f'B{len(label)}s'

        if self._pointer_value:
            result += 'H'
        else:
            result += 'B'
        return result

    @property
    def size(self) -> int:
        return struct.calcsize(self.struct_format)

    def raw(self, packet: Packet = None) -> bytes:
        parts = []
        struct_format = f'{self._format}'
        for label in self._labels:
            length = len(label)
            parts.extend([length, label.encode()])
            struct_format += f'B{length}s'

        if self._pointer_value:
            struct_format += 'H'
            parts.append(self._pointer_value)
        else:
            struct_format += 'B'
            parts.append(0)
        return struct.pack(struct_format, *parts)

    @staticmethod
    def _get_bin_value(value: int, size) -> str:
        bin_value = bin(value)[2:]
        if len(bin_value) < size * 8:
            difference = size * 8 - len(bin_value)
            bin_value = '0' * difference + bin_value

        return bin_value

    def _is_pointer(self, value: int) -> bool:
        return '11' == self._get_bin_value(value, 1)[:2]

    def _get_pointer(self, value: int) -> int:
        bin_value = self._get_bin_value(value, 2)
        return int(bin_value[2:], 2)

    def compute_value(self, data: bytes, packet: Packet = None) -> bytes:
        index = 0
        labels: List[str] = []
        pointer_labels: List[str] = []
        end_of_data = False

        while not end_of_data:
            length = data[index]
            if self._is_pointer(length):
                self._pointer_value = struct.unpack(f'{self._format}H', data[index: index + 2])[0]
                pointer = self._get_pointer(self._pointer_value)
                length = self._raw_packet[pointer]
                # once we enter a pointer, we are sure that we can read labels to the end
                while length:
                    pointer += 1
                    label = self._raw_packet[pointer: pointer + length]
                    pointer_labels.append(label.decode())
                    pointer += length
                    length = self._raw_packet[pointer]
                end_of_data = True
            else:
                index += 1
                label = data[index: index + length]
                labels.append(label.decode())
                index += length
                length = data[index]
                if not length:
                    index += 1
                    end_of_data = True

        self._labels = labels
        self._pointer_labels = pointer_labels
        if self._pointer_value:
            index += 2

        return data[index:]

    def random_value(self) -> str:
        tld_list = ['fr', 'com', 'net', 'org', 'edu', 'gov']
        return f'{rand_string(10, string.ascii_lowercase)}.{random.choice(tld_list)}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: value={self.value}, default={self._default}>'


class TxtField(VariableStringField):

    def compute_value(self, data: bytes, packet: Packet = None) -> Optional[bytes]:
        self._value = data[:packet.rdlength].decode()
        return data[packet.rdlength:]


class DNSTypes(enum.Enum):
    A = 1
    AAAA = 28
    CNAME = 5
    TXT = 16
    SPF = 99
    NS = 2
    PTR = 12


class DNSClasses(enum.Enum):
    IN = 1
    CS = 2
    CH = 3
    HS = 4
    ANY = 255


# noinspection PyArgumentList
class ResourceRecord(Packet):
    __fields__ = [
        DomainNameField('kifurushi.rtd.io'),
        ShortEnumField('type', 1, DNSTypes),
        ShortEnumField('rrclass', 1, DNSClasses),
        IntField('ttl', 0),
        ShortField('rdlength', 0),
        ConditionalField(IPField('a', '127.0.0.1'), lambda p: p.type == DNSTypes.A.value),
        ConditionalField(IPField('aaaa', '::1'), lambda p: p.type == DNSTypes.AAAA.value),
        ConditionalField(DomainNameField('kifurushi.io', 'cname'), lambda p: p.type == DNSTypes.CNAME.value),
        ConditionalField(DomainNameField('kifurushi.io', 'ns'), lambda p: p.type == DNSTypes.NS.value),
        ConditionalField(DomainNameField('1.0.0.127.in-addr.arpa', 'ptr'), lambda p: p.type == DNSTypes.PTR.value),
        ConditionalField(TxtField('txt', 'kifurushi'), lambda p: p.type == DNSTypes.TXT.value),
        ConditionalField(TxtField('spf', 'kifurushi'), lambda p: p.type == DNSTypes.SPF.value)
    ]

    @classmethod
    def from_bytes(cls, data: bytes, raw_packet: bytes = b'') -> Packet:
        packet = cls()
        for field in packet._fields:
            if isinstance(field, DomainNameField):
                field.raw_packet = raw_packet
            data = field.compute_value(data, packet)
            cls._set_packet_attribute(field, packet)

        return packet


# noinspection PyArgumentList
class Question(Packet):
    __fields__ = [
        DomainNameField('kifurushi.io', 'qname'),
        ShortEnumField('qtype', 1, DNSTypes),
        ShortEnumField('qclass', 1, DNSClasses)
    ]

    @classmethod
    def from_bytes(cls, data: bytes, raw_packet: bytes = b'') -> Packet:
        packet = cls()
        for field in packet._fields:
            if isinstance(field, DomainNameField):
                field.raw_packet = raw_packet
            data = field.compute_value(data, packet)
            cls._set_packet_attribute(field, packet)

        return packet


# noinspection PyArgumentList
class DNS(Packet):
    __fields__ = [
        ShortField('id', 0),
        ShortBitsField([
            FieldPart('qr', 0, 1),
            FieldPart('opcode', 0, 4),
            FieldPart('aa', 0, 1),
            FieldPart('tc', 0, 1),
            FieldPart('rd', 0, 1),
            FieldPart('ra', 0, 1),
            FieldPart('z', 0, 1),
            # AD and CD bits were defined in RFC 2535 and updated in RFC 4035
            FieldPart('ac', 0, 1),
            FieldPart('cd', 0, 1),
            FieldPart('rcode', 0, 4)
        ]),
        ShortField('qdcount', 0),
        ShortField('ancount', 0),
        ShortField('nscount', 0),
        ShortField('arcount', 0)
    ]

    def __init__(self, **kwargs):
        self._field_mapping = []  # if we don't do this, we have an issue whe trying to instantiate self.questions
        self.questions: List[Question] = []
        self.answers: List[ResourceRecord] = []
        self.authority_answers: List[ResourceRecord] = []
        self.additional_answers: List[ResourceRecord] = []
        self._init_questions(kwargs)
        self._init_answers(kwargs)
        super().__init__(**kwargs)

    def _init_questions(self, kwargs: Dict[str, Any]) -> None:
        questions = kwargs.pop('questions', None)
        if questions is None:
            return

        if not all(isinstance(question, Question) for question in questions):
            raise TypeError('questions must be a list of Question objects')

        self.questions = questions

    def _init_answers(self, kwargs: Dict[str, Any]) -> None:
        for item in ['answers', 'authority_answers', 'additional_answers']:
            answers = kwargs.pop(item, None)
            if answers is None:
                continue

            if not all(isinstance(answer, ResourceRecord) for answer in answers):
                raise TypeError(f'{item} must be a list of ResourceRecord objects')

            setattr(self, item, answers)

    @property
    def raw(self) -> bytes:
        data = b''.join(field.raw(self) for field in self._fields)
        data += b''.join(question.raw for question in self.questions)
        data += b''.join(answer.raw for answer in [*self.answers, *self.authority_answers, *self.additional_answers])

        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> 'DNS':
        packet = cls()
        cloned_data = (data + b'.')[:-1]

        for field in packet._fields:
            data = field.compute_value(data, packet)
            cls._set_packet_attribute(field, packet)

        cursor = 0
        # questions
        questions = []
        for _ in range(packet.qdcount):
            question = Question.from_bytes(data[cursor:], cloned_data)
            cursor += len(question.raw)
            questions.append(question)
        packet.questions = questions

        # answers
        for item, count in [
            ('answers', 'ancount'), ('authority_answers', 'nscount'), ('additional_answers', 'arcount')
        ]:
            answers = []
            for _ in range(getattr(packet, count)):
                answer = ResourceRecord.from_bytes(data[cursor:], cloned_data)
                cursor += len(answer.raw)
                answers.append(answer)
            setattr(packet, item, answers)

        return packet


if __name__ == '__main__':
    # dns compression is not implemented, so if you change to google dns and see awkward responses
    # it is absolutely normal
    CLOUDFARE = '1.1.1.1'
    domain = 'openclassrooms.com'
    questions = [
        Question(qname=domain, qtype=DNSTypes.A.value),
    ]
    dns = DNS(questions=questions, qdcount=len(questions), rd=1)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(2)
        print(f'sending dns A queries to cloudfare for domain {domain}')
        sock.sendto(dns.raw, (CLOUDFARE, 53))

        answers = []
        truncated = True
        while truncated:
            data, _ = sock.recvfrom(1024)
            dns = DNS.from_bytes(data)
            answers.extend([*dns.answers, *dns.authority_answers, *dns.additional_answers])

            truncated = False if dns.tc == 0 else True

        print('== responses from cloudfare ==')
        for answer in answers:
            print(answer)
