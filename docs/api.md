# API

## abc

All the abstract classes that you can rely on when you want to implement your own fields.

### Field

::: kifurushi.abc.Field
    :docstring:
    :members:

### CommonField

::: kifurushi.abc.CommonField
    :docstring:
    :members:

### VariableStringField

::: kifurushi.abc.VariableStringField
    :docstring:
    :members:

## packet

Classes and helper functions to deal with protocols.

### Packet

::: kifurushi.packet.Packet
    :docstring:
    :members:

### create_packet_class

::: kifurushi.packet.create_packet_class
    :docstring:

### extract_layers

::: kifurushi.packet.extract_layers
    :docstring:

## fields

Here is the list of all fields (except the mixins) defined in the project.

### HexMixin

::: kifurushi.fields.HexMixin
    :docstring:
    :members:

### EnumMixin

::: kifurushi.fields.EnumMixin
    :docstring:
    :members:

### NumericField

::: kifurushi.fields.NumericField
    :docstring:
    :members:

### ByteField

::: kifurushi.fields.ByteField
    :docstring:
    :members:

### ByteEnumField

::: kifurushi.fields.ByteEnumField
    :docstring:
    :members:

### SignedByteField

::: kifurushi.fields.SignedByteField
    :docstring:
    :members:

### SignedByteEnumField

::: kifurushi.fields.SignedByteEnumField
    :docstring:
    :members:

### ShortField

::: kifurushi.fields.ShortField
    :docstring:
    :members:

### ShortEnumField

::: kifurushi.fields.ShortEnumField
    :docstring:
    :members:

### SignedShortField

::: kifurushi.fields.SignedShortField
    :docstring:
    :members:

### SignedShortEnumField

::: kifurushi.fields.SignedShortEnumField
    :docstring:
    :members:

### IntField

::: kifurushi.fields.IntField
    :docstring:
    :members:

### IntEnumField

::: kifurushi.fields.IntEnumField
    :docstring:
    :members:

### SignedIntField

::: kifurushi.fields.SignedIntField
    :docstring:
    :members:

### SignedIntEnumField

::: kifurushi.fields.SignedIntEnumField
    :docstring:
    :members:

### LongField

::: kifurushi.fields.LongField
    :docstring:
    :members:

### LongEnumField

::: kifurushi.fields.LongEnumField
    :docstring:
    :members:

### SignedLongField

::: kifurushi.fields.SignedLongField
    :docstring:
    :members:

### SignedLongEnumField

::: kifurushi.fields.SignedLongEnumField
    :docstring:
    :members:

### FixedStringField

::: kifurushi.fields.FixedStringField
    :docstring:
    :members:

### FieldPart

::: kifurushi.fields.FieldPart
    :docstring:
    :members:

### BitsField

::: kifurushi.fields.BitsField
    :docstring:
    :members:

### ByteBitsField

::: kifurushi.fields.ByteBitsField
    :docstring:
    :members:

### ShortBitsField

::: kifurushi.fields.ShortBitsField
    :docstring:
    :members:

### IntBitsField

::: kifurushi.fields.IntBitsField
    :docstring:
    :members:

### LongBitsField

::: kifurushi.fields.LongBitsField
    :docstring:
    :members:

### ConditionalField

::: kifurushi.fields.ConditionalField
    :docstring:
    :members:

## random values

There are some utility functions to help you get a random but correct value for the field type you choose.

### rand_bytes

::: kifurushi.utils.random_values.rand_bytes
    :docstring:

### rand_signed_bytes

::: kifurushi.utils.random_values.rand_signed_bytes
    :docstring:

### rand_short

::: kifurushi.utils.random_values.rand_short
    :docstring:

### rand_signed_short

::: kifurushi.utils.random_values.rand_signed_short
    :docstring:

### rand_int

::: kifurushi.utils.random_values.rand_int
    :docstring:

### rand_signed_int

::: kifurushi.utils.random_values.rand_signed_int
    :docstring:

### rand_long

::: kifurushi.utils.random_values.rand_long
    :docstring:

### rand_signed_long

::: kifurushi.utils.random_values.rand_signed_long
    :docstring:

### rand_string

::: kifurushi.utils.random_values.rand_string
    :docstring:

There are also constants if you need to check some numeric values or implement custom fields.

* `LEFT_BYTE` the lower limit of a [ByteField](#bytefield) field.
* `RIGHT_BYTE` the upper limit of a [ByteField](#bytefield) field.
* `LEFT_SHORT` the lower limit of a [ShortField](#shortfield) field.
* `RIGHT_SHORT` the upper limit of a [ShortField](#shortfield) field.
* `LEFT_INT` the lower limit of an [IntField](#intfield) field.
* `RIGHT_INT` the upper limit of an [IntField](#intfield) field.
* `LEFT_LONG` the lower limit of a [LongField](#longfield) field.
* `RIGHT_LONG` the upper limit of a [LongField](#longfield) field.
* `LEFT_SIGNED_BYTE` the lower limit of a [SignedByteField](#signedbytefield) field.
* `RIGHT_SIGNED_BYTE` the upper limit of a [SignedByteField](#signedbytefield) field.
* `LEFT_SIGNED_SHORT` the lower limit of a [SignedShortField](#signedshortfield) field.
* `RIGHT_SIGNED_SHORT` the upper limit of a [SignedShortField](#signedshortfield) field.
* `LEFT_SIGNED_INT` the lower limit of a [SignedIntField](#signedintfield) field.
* `RIGHT_SIGNED_INT` the upper limit of a [SignedIntField](#signedintfield) field.
* `LEFT_SIGNED_LONG` the lower limit of a [SignedLongField](#signedlongfield) field.
* `RIGHT_SIGNED_LONG` the upper limit of a [SignedLongField](#signedlongfield) field.

## network helpers

### checksum

::: kifurushi.utils.network.checksum
    :docstring:

### hexdump

::: kifurushi.utils.network.hexdump
    :docstring:
