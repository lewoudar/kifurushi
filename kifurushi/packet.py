"""This module defines the base Packet class and helper functions."""
import enum
import inspect
from copy import copy
from typing import Iterable, Dict, Union, Any, Callable, List, Type

from kifurushi.utils.network import hexdump
from .abc import Field, CommonField
from .fields import BitsField, FieldPart, ConditionalField


class Packet:
    __fields__: Iterable[Field] = None

    def __init__(self, **kwargs):
        self._fields = [field.clone() for field in self.__fields__]
        self._field_mapping = self._create_field_mapping(self._fields)
        self._check_arguments(kwargs)
        value_mapping = {**self._get_default_values(), **kwargs}
        for name, value in value_mapping.items():
            setattr(self, name, value)

    @staticmethod
    def _create_field_mapping(fields: List[Field]) -> Dict[str, Field]:
        error_message = 'you already have a field with name {name}'
        field_mapping = {}

        for field in fields:
            if isinstance(field, BitsField):
                for field_part in field.parts:
                    if field_part.name in field_mapping:
                        raise AttributeError(error_message.format(name=field_part.name))
                    field_mapping[field_part.name] = field
            else:
                if field.name in field_mapping:
                    raise AttributeError(error_message.format(name=field.name))
                field_mapping[field.name] = field

        return field_mapping

    def _check_arguments(self, arguments: Dict[str, Any]) -> None:
        for argument in arguments:
            if argument not in self._field_mapping:
                raise AttributeError(f'there is no attribute with name {argument}')

    def _get_default_values(self) -> Dict[str, Union[str, int]]:
        result = {}
        for name, field in self._field_mapping.items():
            if isinstance(field, BitsField):
                result[name] = field[name].value
            else:
                result[name] = field.value

        return result

    @staticmethod
    def _set_packet_attributes(packet: 'Packet') -> None:
        for name, field in packet._field_mapping.items():
            value = field[name].value if isinstance(field, BitsField) else field.value
            setattr(packet, name, value)

    @staticmethod
    def _set_packet_attribute(field: Field, packet: 'Packet') -> None:
        if isinstance(field, BitsField):
            for field_part in field.parts:
                setattr(packet, field_part.name, field_part.value)
        else:
            setattr(packet, field.name, field.value)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Packet':
        """
        Creates a packet from bytes and returns it.

        **Parameters:**

        **data:** The raw bytes used to construct a packet object.
        """
        packet = cls()
        for field in packet._fields:
            data = field.compute_value(data, packet)
            # we need to set directly the field after it is parsed, so that next fields depending on
            # previous fields can check whether or not they need to parse data
            cls._set_packet_attribute(field, packet)

        return packet

    @classmethod
    def random_packet(cls) -> 'Packet':
        """Returns a packet with fields having random values."""
        packet = cls()
        for field in packet._fields:
            field.value = field.random_value()

        cls._set_packet_attributes(packet)
        return packet

    @property
    def fields(self) -> List[Field]:
        """Returns a copy of the list of fields composing the packet object."""
        return [field.clone() for field in self._fields]

    @staticmethod
    def _set_enum_field(
            field: Union[CommonField, FieldPart],
            value: Union[int, str, enum.Enum],
            set_attr: Callable[[str, Any], None]
    ) -> None:
        if isinstance(value, str):
            found = False
            if field.enumeration is not None:
                for key, name in field.enumeration.items():
                    if name == value:
                        field.value = key
                        found = True
                        break
            if not found:
                raise ValueError(f'{field.name} has no value represented by {value}')

        elif isinstance(value, enum.Enum):
            field.value = value.value
        else:
            field.value = value

        set_attr(field.name, field.value)

    def __setattr__(self, name: str, value: Union[int, str, enum.Enum]):
        super_set_attr = super().__setattr__
        # if name does not represent a field, we directly call the parent __setattr__ method without
        # further processing
        if name in ['_fields', '_field_mapping'] or name not in self._field_mapping:
            super_set_attr(name, value)
            return

        field = self._field_mapping[name]
        if isinstance(field, BitsField):
            self._set_enum_field(field[name], value, super_set_attr)

        elif isinstance(field, CommonField) and hasattr(field, '_enumeration'):
            self._set_enum_field(field, value, super_set_attr)
        else:
            field.value = value
            super_set_attr(name, value)

    @property
    def raw(self) -> bytes:
        """Returns bytes corresponding to what will be sent on the network."""
        return b''.join(field.raw(self) for field in self._fields)

    def __bytes__(self):
        return self.raw

    @property
    def hexdump(self) -> str:
        """Returns tcpdump / wireshark like hexadecimal view of the packet."""
        return hexdump(self.raw)

    @property
    def all_fields_are_computed(self) -> bool:
        """Returns True if all packet fields have been computed using from_bytes class method, False otherwise."""
        for field in self._fields:
            if not field.value_was_computed:
                if isinstance(field, ConditionalField) and not field.condition(self):
                    continue
                else:
                    return False
        return True

    def __eq__(self, other: Any):
        if not isinstance(other, self.__class__):
            raise NotImplementedError
        return self.raw == other.raw

    def __ne__(self, other: Any):
        return not self.__eq__(other)

    def clone(self) -> 'Packet':
        """Returns a copy of the packet."""
        cloned_packet = copy(self)
        cloned_fields = self.fields
        cloned_packet._fields = cloned_fields
        cloned_packet._field_mapping = self._create_field_mapping(cloned_fields)

        return cloned_packet

    def evolve(self, **kwargs) -> 'Packet':
        """
        Returns a new packet with attributes updated by arguments passed as input.

        **Parameters:**

        **kwargs:** keyword-only arguments representing packet attributes with the value to set on them.
        """
        self._check_arguments(kwargs)
        cloned_packet = self.clone()
        for field, value in kwargs.items():
            setattr(cloned_packet, field, value)

        return cloned_packet

    def __repr__(self):
        representation = f'<{self.__class__.__name__}: '
        template = '{name}={value}, '

        for field in self._fields:
            # we don't represent fields where condition is not true
            if isinstance(field, ConditionalField) and not field.condition(self):
                continue

            if isinstance(field, BitsField):
                for field_part in field.parts:
                    value = hex(field_part.value) if field_part.hex else field_part.value
                    representation += template.format(name=field_part.name, value=value)
            else:
                value = hex(field.value) if (hasattr(field, 'hex') and field.hex) else field.value
                representation += template.format(name=field.name, value=value)

        representation = representation[:-2]
        return f'{representation}>'

    def show(self) -> None:
        """Prints a clarified state of packet with type, current and default values of every field."""
        representation = ''
        template = '{name} : {type} = {value} ({default})\n'
        names = sorted(self._field_mapping.keys(), key=len)
        max_length = len(names[-1])

        for field in self._fields:
            # we don't represent fields where condition is not true
            if isinstance(field, ConditionalField) and not field.condition(self):
                continue

            if isinstance(field, ConditionalField):
                class_name = getattr(field, '_field').__class__.__name__
            else:
                class_name = field.__class__.__name__

            if isinstance(field, BitsField):
                for field_part in field.parts:
                    value = hex(field_part.value) if field_part.hex else field_part.value
                    default = hex(field_part.default) if field_part.hex else field_part.default
                    representation += template.format(
                        name=field_part.name.ljust(max_length),
                        type=f'{field_part.__class__.__name__} of {class_name}',
                        value=value,
                        default=default
                    )
            else:
                value = hex(field.value) if field.hex else field.value
                default = hex(field.default) if field.hex else field.default
                representation += template.format(
                    name=field.name.ljust(max_length), type=class_name, value=value, default=default
                )
        print(representation, end='')


def create_packet_class(name: str, fields: Iterable[Field]) -> type(Packet):
    """
    Creates and returns a packet class.

    **Parameters:**

    **name:** The name of the class to create.
    **fields:** An iterable of fields that compose the packet.
    """
    if not isinstance(name, str):
        raise TypeError(f'class name must be a string but you provided {name}')

    if not fields:
        raise ValueError('the list of fields must not be empty')

    for field in fields:
        if not isinstance(field, Field):
            raise TypeError(f'each item in the list must be a Field object but you provided {field}')

    return type(name, (Packet,), {'__fields__': fields})


def extract_layers(data: bytes, *args: Type[Packet]) -> List[Packet]:
    """
    Extract various packet from raw binary data.

    For example, imagine you want to send an [ICMP](https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol)
    ping request. You will probably need to create two Packet classes, ICMP and IP and send the sum of them over
    the network i.e something like `socket.sendto(ICMP(...).raw + IP(...).raw, address)`.

    Now you want to get the ICMP reply, how to get it? You can't use `ICMP.from_bytes` because you will have IP and
    ICMP returned all at once! The solution is to use *extract_layers* with code like the following:
    `icmp, ip = extract_layers(socket.recvfrom(1024)[0], ICMP, IP)`

    ** Parameters: **

    * **data:** The raw bytes to parse.
    * **args:** A list of Packet layers used to reconstruct the expected layers. You must provide at least one
    class, if not, you will get an error.
    """
    if not isinstance(data, bytes):
        raise TypeError(f'data must be bytes but you provided {data}')

    if not args:
        raise ValueError('you must provide at least one Packet subclass to use for layer extraction')

    for packet_class in args:
        if not inspect.isclass(packet_class) or not issubclass(packet_class, Packet):
            raise TypeError(
                f'all arguments following the given data must be subclasses'
                f' of Packet class but you provided {packet_class}'
            )

    packets = []
    cursor = 0
    for packet_class in args:
        packet = packet_class.from_bytes(data[cursor:])
        cursor = len(packet.raw)
        packets.append(packet)
    return packets
