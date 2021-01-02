import pytest

from kifurushi import random_values


# noinspection DuplicatedCode
@pytest.mark.parametrize(('func', 'left', 'right'), [
    ('rand_bytes', 0, 2 ** 8 - 1),
    ('rand_signed_bytes', -2 ** 7, 2 ** 7 - 1),
    ('rand_short', 0, 2 ** 16 - 1),
    ('rand_signed_short', -2 ** 15, 2 ** 15 - 1),
    ('rand_int', 0, 2 ** 32 - 1),
    ('rand_signed_int', -2 ** 31, 2 ** 31 - 1),
    ('rand_long', 0, 2 ** 64 - 1),
    ('rand_signed_long', -2 ** 63, 2 ** 63 - 1),
])
def test_should_call_function_with_correct_arguments(mocker, func, left, right):
    randint_mock = mocker.patch('random.randint')
    getattr(random_values, func)()
    randint_mock.assert_called_once_with(left, right)


# noinspection DuplicatedCode
@pytest.mark.parametrize(('func', 'left', 'right'), [
    ('rand_bytes', 0, 2 ** 8 - 1),
    ('rand_signed_bytes', -2 ** 7, 2 ** 7 - 1),
    ('rand_short', 0, 2 ** 16 - 1),
    ('rand_signed_short', -2 ** 15, 2 ** 15 - 1),
    ('rand_int', 0, 2 ** 32 - 1),
    ('rand_signed_int', -2 ** 31, 2 ** 31 - 1),
    ('rand_long', 0, 2 ** 64 - 1),
    ('rand_signed_long', -2 ** 63, 2 ** 63 - 1),
])
def test_should_return_correct_value(func, left, right):
    assert left <= getattr(random_values, func)() <= right


class TestRandString:
    """Tests function rand_string"""

    # noinspection PyTypeChecker
    def test_should_raise_type_error_when_length_is_not_an_integer(self):
        with pytest.raises(TypeError) as exc_info:
            random_values.rand_string(4.5)

        assert 'length must be a positive integer but you provided 4.5' == str(exc_info.value)

    @pytest.mark.parametrize('value', [0, -1])
    def test_should_raise_value_error_when_length_is_less_than_0(self, value):
        with pytest.raises(ValueError) as exc_info:
            random_values.rand_string(value)

        assert f'length must be greater than 0 but you provided {value}' == str(exc_info.value)

    # noinspection PyTypeChecker
    @pytest.mark.parametrize('value', [4, ['a', 'b'], ''])
    def test_should_raise_type_error_when_characters_is_not_a_string_or_is_empty(self, value):
        with pytest.raises(TypeError) as exc_info:
            random_values.rand_string(characters=value)

        assert (f'characters must be a non empty string'
                f' but you provided {value}') == str(exc_info.value)

    def test_should_compute_length_if_not_given(self, mocker):
        randint_mock = mocker.patch('random.randint', return_value=30)
        value = random_values.rand_string()

        assert isinstance(value, str)
        randint_mock.assert_called_once_with(20, 150)

    def test_should_return_compliant_string(self):
        characters = 'ABCDEFGH'
        value = random_values.rand_string(10, characters)

        assert isinstance(value, str)
        assert len(value) == 10
        assert any([character in value for character in characters])
