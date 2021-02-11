import enum

from kifurushi.fields import ByteBitsField, FieldPart, ShortField, ShortEnumField, ShortBitsField
from kifurushi.packet import Packet


class Flags(enum.Enum):
    reserved = 0
    df = 1
    mf = 2


class Identification(enum.Enum):
    lion = 1
    turtle = 5
    python = 7


class MiniIP(Packet):
    # noinspection PyArgumentList
    __fields__ = [
        ByteBitsField([FieldPart('version', 4, 4), FieldPart('ihl', 5, 4)]),
        ShortField('length', 20),
        ShortEnumField('identification', 1, Identification),
        ShortBitsField([FieldPart('flags', 0b010, 3, Flags), FieldPart('offset', 0, 13)], hex=True),
    ]
