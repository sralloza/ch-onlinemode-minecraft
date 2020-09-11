"""Useful functions to all the package."""

from functools import wraps
from hashlib import sha256
from typing import Any
from typing import Type

import click

from .paths import get_server_path

_def = bytes(1)
_Ex = Type[Exception]


def bool2str(boolean: bool):
    """Returns a bool as a string (in lowercase, as json).

    Ussage:
        >>> bool2str(True)
        'true'
        >>> bool2str(False)
        'false'

    Args:
        boolean (bool): input bool.

    Returns:
        str: string representation of the input bool.
    """

    return str(boolean).lower()


def str2bool(string: str, click_enabled=True):
    """Transforms a string to bool.

    Usage:
        >>> str2bool("True")
        True
        >>> str2bool("False")
        False
        >>> str2bool("Invalid", click_enabled=False)
        ValueError("'Invalid' is not a valid boolean")


    Args:
        string (str): input string.
        click_enabled (bool, optional): If True, in case of error it will raise
            a click Exception. Defaults to False.

    Raises:
        argparse.ArgumentTypeError: if the string is not valid and parser is True.
        ValueError: if the string is not valid and parser is False.

    Returns:
        bool: boolean value of the string.
    """

    if isinstance(string, bool):
        return string

    string = str(string)
    if string.lower() in ("yes", "true", "t", "on", "y", "1", "sí", "si", "s"):
        return True
    if string.lower() in ("no", "false", "f", "off", "n", "0"):
        return False

    exc = ValueError(f"{string!r} is not a valid boolean")
    if click_enabled:

        def dummy_function():
            raise exc

        # pylint: disable=no-value-for-parameter
        return click_handle_exception(_func=dummy_function)()
    raise exc


class Validators:
    """Common variable types validators."""

    @staticmethod
    def bool(value: Any):
        """Checks for bool values.

        Args:
            value (Any): input.

        Returns:
            bool: whether it's bool or not.
        """

        if isinstance(value, bool):
            return True
        return False

    @staticmethod
    def difficulty(value: Any):
        """Checks for valid difficulty values.

        Args:
            value (Any): input.

        Returns:
            bool: whether it's a valid difficulty or not.
        """

        if value not in ["peaceful", "easy", "normal", "hard"]:
            return False
        return True

    @staticmethod
    def int(value: Any):
        """Checks for int values.

        Args:
            value (Any): input.

        Returns:
            bool: whether it's int or not.
        """

        if Validators.bool(value):
            return False
        if isinstance(value, int):
            return True
        return False

    @staticmethod
    def str(value: Any):
        """Checks for str values.

        Args:
            value (Any): input.

        Returns:
            bool: whether it's str or not.
        """

        if isinstance(value, str):
            return True
        return False

    @staticmethod
    def float(value: Any):
        """Checks for float values.

        Args:
            value (Any): input.

        Returns:
            bool: whether it's float or not.
        """

        if isinstance(value, float):
            return True
        return False


def gen_hash() -> str:
    """Generates a 256-bit hash identifying the server.

    Returns:
        str: 256-bit hash.
    """

    data = get_server_path().as_posix().encode()
    return sha256(data).hexdigest()


def click_handle_exception(
    _func=_def, *, exc_type: _Ex = None
):  # pylint:disable=W9015,W9016,W9011,W9012
    """Handles an exception during click execution. Works as a decorator.

    Raises:
        ValueError: if the decorator is misused.

    Args:
        exc_type (_Ex, optional): exception type. If None,
            every exception will be catched. Defaults to None.
    """

    is_def = _func is _def
    is_call = callable(_func)
    try:
        is_exc = issubclass(_func, BaseException)
    except TypeError:
        is_exc = False

    if not is_def and not is_call or is_exc and is_call:
        raise ValueError(
            "Use keyword arguments in the click_handle_exception decorator"
        )

    def outer_wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException as exc:
                if exc_type and not isinstance(exc, exc_type):
                    raise
                excname = exc.__class__.__name__
                error_msg = f"{excname}: {', '.join([str(x) for x in exc.args])}"
                raise click.ClickException(error_msg)

        return inner_wrapper

    if _func is _def:
        return outer_wrapper
    return outer_wrapper(_func)
