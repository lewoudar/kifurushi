import random
import string


def rand_bytes():
    """Returns an unsigned random byte value"""
    return random.randint(0, 2 ** 8 - 1)


def rand_signed_bytes():
    """Returns a signed random byte value"""
    return random.randint(-2 ** 7, 2 ** 7 - 1)


def rand_short():
    """Returns an unsigned random short value"""
    return random.randint(0, 2 ** 16 - 1)


def rand_signed_short():
    """Returns a signed random short value"""
    return random.randint(-2 ** 15, 2 ** 15 - 1)


def rand_int():
    """Returns an unsigned random int value"""
    return random.randint(0, 2 ** 32 - 1)


def rand_signed_int():
    """Returns a signed random int value"""
    return random.randint(-2 ** 31, 2 ** 31 - 1)


def rand_long():
    """Returns an unsigned random long value"""
    return random.randint(0, 2 ** 64 - 1)


def rand_signed_long():
    """Returns a signed random int value"""
    return random.randint(-2 ** 63, 2 ** 63 - 1)


def rand_string(length: int = None, characters: str = None) -> str:
    """
    Returns a random string given.

    **Parameters:**

    **length:** The length of the desired random string. If not given a random value will be
    computed using `random.randint(20, 150)`.
    **characters:** A string with characters that will be used to form the random
    string. If not given, defaults to `string.ascii_letters`.
    """
    if length is not None:
        if not isinstance(length, int):
            raise TypeError(f'length must be a positive integer but you provided {length}')

        if length <= 0:
            raise ValueError(f'length must be greater than 0 but you provided {length}')

    if characters is not None and (not isinstance(characters, str) or not characters):
        raise TypeError(f'characters must be a non empty string but you provided {characters}')

    length = length if length else random.randint(20, 150)
    characters = characters if characters else string.ascii_letters
    return ''.join([random.choice(characters) for _ in range(length)])
