# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.3.0] - 2021-11-14

## Added

- New boolean parameter `decode` to class `FixedStringField`. It defaults to `False` meaning the internal value is
  considered as bytes, if `True`, it will be considered as a string. - (#4)
- Support for python 3.10. - (#4)

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