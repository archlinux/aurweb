import pytest

from aurweb.templates import register_filter, register_function


@register_filter("func")
def func():
    pass


@register_function("function")
def function():
    pass


def test_register_filter_exists_key_error():
    """ Most instances of register_filter are tested through module
    imports or template renders, so we only test failures here. """
    with pytest.raises(KeyError):
        @register_filter("func")
        def some_func():
            pass


def test_register_function_exists_key_error():
    """ Most instances of register_filter are tested through module
    imports or template renders, so we only test failures here. """
    with pytest.raises(KeyError):
        @register_function("function")
        def some_func():
            pass
