"""This module defines the base Packet class and helper functions."""
import enum
from typing import List, Dict, Union

import attr

from .abc import Field, CommonField
from .fields import BitsField, FieldPart


# TODO: implement name verification in the field module (no "-" or space)


@attr.s(repr=False)
class Packet:
    _fields: List[Field] = attr.ib(validator=attr.validators.deep_iterable(
        member_validator=attr.validators.instance_of(Field)
    ))
    _field_mapping: Dict[str, Field] = attr.ib(init=False, factory=dict)
    _attribute_error: str = attr.ib(init=False, default='{packet} has no attribute {attribute}')

    def __attrs_post_init__(self):
        self._field_mapping = self._create_field_mapping(self._fields)

    @staticmethod
    def _create_field_mapping(fields: List[Field]) -> Dict[str, Field]:
        field_mapping = {}
        for field in fields:
            if isinstance(field, BitsField):
                for field_part in field.parts:
                    field_mapping[field_part.name] = field
            else:
                field_mapping[field.name] = field
        return field_mapping

    def __getattr__(self, item: str):
        if item not in self._field_mapping:
            raise AttributeError(self._attribute_error.format(packet=self.__class__.__name__, attribute=item))

        field = self._field_mapping[item]
        if isinstance(field, BitsField):
            return field.get_field_part_value(item)
        else:
            return field.value

    @staticmethod
    def _set_enum_field(field: Union[CommonField, FieldPart], value: Union[int, str, enum.Enum]):
        if isinstance(value, str):
            found = False
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

    def __setattr__(self, name: str, value: Union[int, str, enum.Enum]):
        if name in ['_fields', '_field_mapping', '_attribute_error']:
            return super().__setattr__(name, value)

        if name not in self._field_mapping:
            raise AttributeError(self._attribute_error.format(packet=self.__class__.__name__, attribute=name))

        field = self._field_mapping[name]
        if isinstance(field, BitsField):
            self._set_enum_field(field[name], value)

        elif isinstance(field, CommonField) and hasattr(field, '_enumeration'):
            self._set_enum_field(field, value)
        else:
            field.value = value

    @property
    def raw(self) -> bytes:
        """Returns bytes corresponding to what will be sent on the network."""
        return b''.join(field.raw for field in self._fields)

    def __bytes__(self):
        return self.raw

    @staticmethod
    def _smart_ord(value: Union[int, str]) -> int:
        if isinstance(value, int):
            return value
        return ord(value)

    def _sane_value(self, value: Union[int, str]) -> str:
        result = ''
        for i in value:
            j = self._smart_ord(i)
            if (j < 32) or (j >= 127):
                result += '.'
            else:
                result += chr(j)
        return result

    @property
    def hexdump(self) -> str:
        """Returns tcpdump / wireshark like hexadecimal view of the packet."""
        result = ''
        raw = self.raw
        raw_length = len(raw)
        i = 0

        while i < raw_length:
            result += '%04x  ' % i
            for j in range(16):
                if i + j < raw_length:
                    result += '%02X ' % self._smart_ord(raw[i + j])
                else:
                    result += '   '
            result += ' %s\n' % self._sane_value(raw[i:i + 16])
            i += 16
        # remove trailing \n
        result = result[:-1] if result.endswith('\n') else result
        return result

    def clone(self) -> 'Packet':
        """Returns a copy of the packet."""
        cloned_packet = attr.evolve(self)
        fields = [field.clone() for field in self._fields]
        cloned_packet._fields = fields
        cloned_packet._field_mapping = self._create_field_mapping(fields)
        return cloned_packet

    def get_packet_from_bytes(self, data: bytes) -> 'Packet':
        """Parses raw bytes object and returns a Packet instance corresponding to the given bytes."""
        cloned_packet = self.clone()
        for field in cloned_packet._fields:
            data = field.compute_value(data, self)
        return cloned_packet

    def __repr__(self):
        representation = '<Packet: '
        template = '{name}={value}, '
        for field in self._fields:
            if isinstance(field, BitsField):
                for field_part in field.parts:
                    representation += template.format(name=field_part.name, value=field_part.value)
            else:
                representation += template.format(name=field.name, value=field.value)
        representation = representation[:-2]
        return f'{representation}>'

    def show(self):
        """Prints a clarified state of packet with type, current and default values of every field."""
        representation = ''
        template = '{name} : {type} = {value} ({default})\n'
        names = sorted(self._field_mapping.keys(), key=len)
        max_length = len(names[-1])
        for field in self._fields:
            class_name = field.__class__.__name__
            if isinstance(field, BitsField):
                for field_part in field.parts:
                    representation += template.format(
                        name=field_part.name.ljust(max_length),
                        type=f'{field_part.__class__.__name__} of {class_name}',
                        value=field_part.value,
                        default=field_part.default
                    )
            else:
                representation += template.format(
                    name=field.name.ljust(max_length), type=class_name, value=field.value, default=field.default
                )
        print(representation, end='')
