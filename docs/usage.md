# Usage

## Basics

The usage of kifurushi is pretty straightforward. Forge a protocol consists in many cases in just assembling its fields.
Here is an example:

```python
import enum
from kifurushi import Packet, ShortField, ByteField, IntEnumField


class Mood(enum.Enum):
    happy = 1
    cool = 2
    angry = 4


class Disney(Packet):
    __fields__ = [
        ShortField('mickey', 2),
        ByteField('minnie', 3, hex=True),
        IntEnumField('donald', 1, Mood)
    ]
```

You create a new protocol by inheriting the [Packet](api.md#packet) class. In this example, we have 3 fields:

* A two-bytes integer field called *mickey* whose default value is 2.
* A one byte integer field called *minnie* whose default value is 3. You notice the `hex` keyword set to true. It is to
  tell that we prefer the hexadecimal representation when displaying this field information. We will see above an
  example.
* The last field is a four-byte field. It is slightly different from the first two (notice the *Enum* in the class name)
  . It takes a third **mandatory** argument which is an enum, or a dict mapping values to a literal representation
  easier to remember for the user.

The list of all fields can be found [here](api.md#fields).

Now let's see an example usage of this protocol.

```python
>>> d = Disney(mickey=1)
>>> d.show()
mickey: ShortField = 1(2)
minnie: ByteField = 0x3(0x3)
donald: IntEnumField = 1(1)
>>> d.donald = Mood.cool
# this has the same effect as the previous line
>>> d.donald = 'cool'
# this also as the same effect as the two previous lines
>>> d.donald = Mood.cool.value  # int value 2
>>> d.raw
b'\x00\x01\x03\x00\x00\x00\x02'
>>> Disney.from_bytes(_)
<Disney: mickey = 1, minnie = 0x3, donald = 2>
```

Notes:

* The first statement instantiates a `Disney` object with value `mickey` attribute set to 1.
  
* The second statement uses the `show` method to print a detailed state of the object. Each line represents an attribute
  with its **name**, its **type**, its **current value** and its **default value** between the parenthesis. Notice that
  *minnie* values are represented in hexadecimal thanks to the `hex` attribute set to `True` on field object.
  
* The next three statements set the `donald` attribute with value 2. As you can see, we can use the enumeration
  `Mood.cool`, its name or its value. kifurushi knows how to handle these cases.
  
* The penultimate statement is the `raw` property which computes the raw bytes from the protocol fields. This is useful
  when you want to send data over the network.
  
* The last statement shows how you can convert data received over the network to a protocol instance.

You can also dynamically implement a protocol using the [create_packet_class](api.md#create_packet_class) helper
function.

```python
from kifurushi import create_packet_class, ShortField, ByteField, IntField

fields = [
  ShortField('mickey', 2),
  ByteField('minnie', 3, hex=True),
  IntField('donald', 1)
]

disney_class = create_packet_class('Disney', fields)
d = disney_class(mickey=1)
print(d)  # <Disney: mickey=1, minnie=0x3, donald=1>
```


## Implement a custom field

Sometimes, you will feel that the default [fields](api.md#fields) implemented by kifurushi are not enough for your use
case. In this case you will need to implement a custom type by inheriting the [Field](api.md#field) class. Let's see an
example with a field representing an IP value. Many protocols like 
[ICMP](https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol) or 
[DNS](https://en.wikipedia.org/wiki/Domain_Name_System) needs this type of field.
I will use [attrs](https://www.attrs.org/en/stable/) to define the field class, but it is not an obligation, you can the
classic style to implement your class.


```python
import ipaddress
import random
from typing import Union, Optional

import attr
from kifurushi import Field, Packet

def check_ip_address(_, _param, address: str) -> None:
    try:
        ipaddress.ip_address(address)
    except ipaddress.AddressValueError:
        raise ValueError(f'{address} is not a valid ip address')

@attr.s(slots=True, repr=False)
class IPField(Field):
    # it is important to define the name attribute
    _name: str = attr.ib(validator=attr.validators.instance_of(str))
    _default: str = attr.ib(validator=check_ip_address)
    _address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = attr.ib(init=False)

    def __attrs_post_init__(self):
        # the internal value of the fields defaults to the default attribute
        self._address = ipaddress.ip_address(self._default)

    @property
    def name(self) -> str:
        # the name of the field
        return self._name

    @property
    def size(self) -> int:
        # the size is in bytes
        return 4 if self._address.version == 4 else 16

    @property
    def default(self) -> str:
        return self._default

    @property
    def value(self) -> str:
        # returns the internal value of the field
        return f'{self._address}'

    @value.setter
    def value(self, value: str) -> None:
        # sets the internal value of the field
        self._address = ipaddress.ip_address(value)

    @property
    def struct_format(self) -> str:
        # not really useful here, but the idea is to use this value in combination with `struct.pack` 
        # or `struct.unpack` method to serialize or deserialize the field
        return '!I' if self._address.version == 4 else '!IIII'

    def raw(self, packet: Packet = None) -> bytes:
        # returns the bytes corresponding to this field
        return self._address.packed

    def random_value(self) -> str:
        # A random value for this field. This is useful when the `Packet.rand_packet` class method is used
        # to create a packet with random values.
        if self._address.version == 4:
            return f'{random.randint(1, 192)}.{random.randint(1, 168)}.0.1'
        else:
            return f'fe80::{random.randint(1, 8)}'

    def compute_value(self, data: bytes, packet: Packet = None) -> Optional[bytes]:
        # data represent the remaining bytes to parse by the packet instance passed as second argument
        # packet can be useful in some circumstances where field value depends on previous fields already parsed
        self._address = ipaddress.ip_address(data[:self.size])
        # it is important to return the remaining bytes after those representing this field so that other fields
        # can also process their value
        return data[self.size:]

    def __repr__(self):
        return f'<{self.__class__.__name__}: default={self._default}, value={self._address}>'
```

Notes:

* The `Field` class defines an interface with common methods that all fields must implement and this is what is done in
  the previous example.
  
* The `name` attribute is important to define. It is used by the packet where the field will belong to set an attribute
  using the value of the `name` attribute. The reason why this attribute is not in the `Field` interface is the
  [BitsField](api.md#bitsfield) and its descendants. We will talk about this field later in the documentation.
  
* The code should be simple to understand, just about the `compute_field` method, this is what is called for every field
  of a packet when the `Packet.from_bytes` method is used. The first argument is the remaining bytes to parse from input
  data, and the second argument is the packet currently processing the data. This second argument is useful when the
  value of the current field depends on fields already parsed. We can then retrieved them via the packet object. It is
  also important to return remaining bytes after removing those corresponding to the field. This way, other fields will
  also be able to process their value.

## Customize a packet class

Sometimes the default implementation of the [Packet](api.md#packet) class is not sufficient for your needs, it comes in
handy to adjust some methods as you wish. `Packet` is a python class, so you can inherit it and override the methods
you want, lets show an example by representing the [IPV4](https://en.wikipedia.org/wiki/IPv4) protocol.
It will also be the occasion to show the use of a [BitsField](api.md#bitsfield).

We will not take in account `options` field to keep it simple.

```python
from kifurushi import (
    Packet, ByteBitsField, ByteField, FieldPart, ShortField, IntField, ShortBitsField,
    checksum
)


class IPv4(Packet):
    __fields__ = [
        ByteBitsField([FieldPart('version', 4, 4), FieldPart('ihl', 5, 4)]),
        ByteBitsField([FieldPart('dscp', 0, 6), FieldPart('ecn', 0, 2)]),
        ShortField('length', 0),
        ShortField('identification', 0),
        ShortBitsField([FieldPart('flags', 0, 3), FieldPart('offset', 0, 13)]),
        ByteField('ttl', 12),
        ByteField('protocol', 1),
        ShortField('checksum', 0),
        # you can replace with the IPField created in the previous section
        # the following line will result to IPField('src', '127.0.0.1')
        IntField('src', 2130706433),
        IntField('dest', 2130706433)
    ]

    def __init__(self, **kwargs):
        # if we don't write the following line, we will have an issue when trying to instantiate self.payload
        self._field_mapping = []
        self.payload = b''
        # here we take in account another keyword attribute in addition to those defined in fields.
        # It represents the upper layers transported by the IP packet, check the raw method to see
        # why we need it.
        payload = kwargs.pop('payload', None)
        if payload is not None:
            self.payload = payload
        super().__init__(**kwargs)

    def raw(self) -> bytes:
        # the default checksum value is 0 meaning that it is not computed. The value depends on other
        # fields and the payload carried by the IPv4 protocol. For more information you can have a
        # look here:
        # https://en.wikipedia.org/wiki/IPv4_header_checksum
        # kifurushi provides a helper function "checksum" to calculate checksum for various fields.
        if not self.checksum:
            data = b''.join(field.raw(self) for field in self._fields) + self.payload
            self.checksum = checksum(data)
        return b''.join(field.raw(self) for field in self._fields) + self.payload

ip = IPv4(dscp=1, length=20)
print(ip)
# <IPv4: version=4, ihl=5, dscp=1, ecn=0, length=20, identification=0, flags=0, offset=0,
# ttl=12, protocol=1, checksum=0, src=2130706433, dest=2130706433>
```

Notes:

* Here we have some usages of `BitsField` more specifically [ByteBitsField](api.md#bytebitsfield) and
[ShortBitsField](api.md#shortbitsfield). These fields represent different information that cannot be contained in 
multiples of bytes but rather part of a byte (or several bytes). It is the case for the first two information of an
IPv4 packet, `version` and `ihl`, both hold in 4 bits. This is where `BitsField` class and its descendants come in
handy. For the first two, they hold in a **byte**, this is why we use a `ByteBitsField`. For `flags` and `offset`
information, they hold in **2 bytes**, so we use the `ShortBitsField`.
  
* These `BitsField` are composed of [FieldPart](api.md#fieldpart) objects taken a name representing an information, a
default value and the size in **bits** the information takes. Notice that it is the field name which is used as an
attribute for the IPv4 packet as shown in the previous example with `dscp`.
  
* We update slightly the default `Packet.__init__` method to take in account the `payload` information. It represents
the upper data carried by the IPv4 packet. It may be
[ICMP](https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol) or a combination
[UDP](https://en.wikipedia.org/wiki/User_Datagram_Protocol) + [DNS](https://en.wikipedia.org/wiki/Domain_Name_System).
This additional data will be used to compute the `checksum` field which depends on the current IPv4 fields and the
payload.
  
* The `Packet.raw` method is overloaded to compute the `checksum` field if it is not already computed before returning
raw bytes to send on the wire.
  
!!! warning
    Take care to the names given to the fields of a packet. There are some reserved names that cannot be used because
    they are attributes of the [Packet](api.md#packet) class like `raw`, `fields`, `compute_value`, `hexdump`,
    `random_packet` and `from_bytes`.

!!! note
    Don't hesitate to look at the [examples](https://github.com/lewoudar/kifurushi/tree/main/examples) folder to see 
    more examples of protocol implementations with kifurushi. You will see usage of the 
    [ConditionalField](api.md#conditionalfield) which comes in handy when the presence of a field in a packet depends on
    other fields.

## Miscellaneous

### Network helpers

Kifurushi provides some helper functions like [hexdump](api.md#hexdump) to print wireshark-like hexadecimal
representation of a packet which may be useful for debugging purposes.

```python
from kifurushi import create_packet_class, ShortField, ByteField, IntField, hexdump

fields = [
  ShortField('mickey', 2),
  ByteField('minnie', 3, hex=True),
  IntField('donald', 1)
]

disney_class = create_packet_class('Disney', fields)
d = disney_class(mickey=1)
print(hexdump(d.raw))  # '0000  00 01 03 00 00 00 01                             .......'

# a Packet object has a property hexdump which internally calls the hexdump function
print(d.hexdump)  # '0000  00 01 03 00 00 00 01                             .......'
```

There is also the [checksum](api.md#checksum) function to compute some packet checksums. Look the previous section for
an example with the IPv4 protocol.

Finally, there is the [extract_layers](api.md#extract_layers) function to help you dissect many protocols from raw data.
For example, let's consider again the `IPv4` protocol we implemented earlier. If you combined it with an `ICMP` protocol
(we assume we have also implemented this protocol), you will probably end with a code like the following to send it over
the wire: `socket.sendto(ICMP(type=8).raw + IPv4().raw, address)`.

Now if you want to receive the ICMP response from the wire, what will you do? `ICMP.from_bytes(data)` ? This will not
work because you send **ICMP** + **IPv4** data over the wire and you will receive also the two data structures from the
wire. So to get these layers, you can write a code like the following

```python
from kifurushi import extract_layers
data, _ = socket.recvfrom(4096)

icmp, ip = extract_layers(data, ICMP, IPv4)
```

So, you pass to `extract_layers` the data and the list of layers (order is important) you expect to receive from 
the network. In response, you will get layer *instances* corresponding to the different classes passed to the
function.

### random helpers

Kifurushi carries also some constants and random [helpers](api.md#random-values) useful when you want to implement
custom fields.

```python
from kifurushi import LEFT_BYTE, RIGHT_BYTE, rand_bytes

assert LEFT_BYTE < rand_bytes() < RIGHT_BYTE  # this will never raises an error
```