# Usage

## Basics

The usage of kifurushi is pretty straightforward. Forge a protocol consists in many cases in just assembling its fields.
Here is an example

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

you create a new protocol by inheriting the [Packet](api.md#packet) class. In many cases the protocol implementation
only consists of declaring fields belonging to that protocol. In this example, we have 3 fields:

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
  with its **name**, its **type**, its **current value** and its **default value** between the parenthesis.
* The next three statements set the `donald` attribute with value 2. As you can see, we can use the enumeration
  `Mood.cool`, its name or its value. `kifurushi` knows how to handle these cases.
* The penultimate statement is the `raw` property which computes the raw bytes from the protocol fields. This is useful
  when you want to send data over the network.
* The last statement shows how you can convert data received over the wire to a protocol instance.