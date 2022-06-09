# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.5.0] - 2021-21-16

## Added

- possibility to set `bytearray` value to `VariableStringField` and `FixedStringField` objects.

## [0.4.0] - 2021-12-08

## Added

- property `value_was_computed` on `Field` class so that all fields inherit it.
- added property `all_fields_are_computed` on Packet class to know if a packet has been correctly parsed using
  `from_bytes` class method.


## [0.3.1] - 2021-11-14

## Changed

- Type annotation of FixedStringField `default` parameter. It is now `AnyStr` instead of `str`.

## [0.3.0] - 2021-11-14

## Added

- New boolean parameter `decode` to class `FixedStringField`. It defaults to `False` meaning the internal value is
  considered as bytes, if `True`, it will be considered as a string.
- Support for python 3.10.

## Changed

- Replace `is_bytes` parameter on class VariableStringField to `decode`. The meaning now changes. If `decode` is `False`
  which is the default case, the internal value is considered as bytes, if `True`, it is considered as a string. - (#4)

## [0.2.0] - 2021-08-18

## Changed

- The class `VariableStringField` now accepts a keyword-only parameter `is_bytes` to tell if we are dealing with text
  data or raw bytes.

### Added

- Tests are now passed on pypy3 in github actions.

## [0.1.0] - 2021-03-03

### Added

- First version of the package.
