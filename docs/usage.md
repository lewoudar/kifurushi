# Usage

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
*

The list of all fields can be found[here](api.md#fields)
