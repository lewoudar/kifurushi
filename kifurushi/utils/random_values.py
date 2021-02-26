"""Module which contains different random functions and constants useful when handling field values."""
import random
import string

LEFT_BYTE = LEFT_SHORT = LEFT_INT = LEFT_LONG = 0
RIGHT_BYTE = 2 ** 8 - 1
RIGHT_SHORT = 2 ** 16 - 1
RIGHT_INT = 2 ** 32 - 1
RIGHT_LONG = 2 ** 64 - 1
LEFT_SIGNED_BYTE = -2 ** 7
LEFT_SIGNED_SHORT = -2 ** 15
LEFT_SIGNED_INT = -2 ** 31
LEFT_SIGNED_LONG = -2 ** 63
RIGHT_SIGNED_BYTE = 2 ** 7 - 1
RIGHT_SIGNED_SHORT = 2 ** 15 - 1
RIGHT_SIGNED_INT = 2 ** 31 - 1
RIGHT_SIGNED_LONG = 2 ** 63 - 1

# bandit raises B311 warnings because it thinks we use random module for security/cryptographic purposes
# since it is not the case here, we can disable this error with confidence
# more about the error here: https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b311-random


def rand_bytes():
    """Returns an unsigned random byte value."""
    return random.randint(LEFT_BYTE, RIGHT_BYTE)  # nosec


def rand_signed_bytes():
    """Returns a signed random byte value."""
    return random.randint(LEFT_SIGNED_BYTE, RIGHT_SIGNED_BYTE)  # nosec


def rand_short():
    """Returns an unsigned random short value."""
    return random.randint(LEFT_SHORT, RIGHT_SHORT)  # nosec


def rand_signed_short():
    """Returns a signed random short value."""
    return random.randint(LEFT_SIGNED_SHORT, RIGHT_SIGNED_SHORT)  # nosec


def rand_int():
    """Returns an unsigned random int value."""
    return random.randint(LEFT_INT, RIGHT_INT)  # nosec


def rand_signed_int():
    """Returns a signed random int value."""
    return random.randint(LEFT_SIGNED_INT, RIGHT_SIGNED_INT)  # nosec


def rand_long():
    """Returns an unsigned random long value."""
    return random.randint(LEFT_LONG, RIGHT_LONG)  # nosec


def rand_signed_long():
    """Returns a signed random int value."""
    return random.randint(LEFT_SIGNED_LONG, RIGHT_SIGNED_LONG)  # nosec


def rand_string(length: int = None, characters: str = None) -> str:
    """
    Returns a random string given.

    **Parameters:**

    * **length:** The length of the desired random string. If not given a random value will be
    computed using `random.randint(20, 150)`.
    * **characters:** A string with characters that will be used to form the random
    string. If not given, defaults to `string.ascii_letters`.
    """
    if length is not None:
        if not isinstance(length, int):
            raise TypeError(f'length must be a positive integer but you provided {length}')

        if length <= 0:
            raise ValueError(f'length must be greater than 0 but you provided {length}')

    if characters is not None and (not isinstance(characters, str) or not characters):
        raise TypeError(f'characters must be a non empty string but you provided {characters}')

    length = length if length else random.randint(20, 150)  # nosec
    characters = characters if characters else string.ascii_letters
    return ''.join([random.choice(characters) for _ in range(length)])  # nosec
