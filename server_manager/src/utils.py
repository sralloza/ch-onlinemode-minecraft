"""Useful functions to all the package."""

import argparse
from hashlib import sha256
from typing import Any, NoReturn

import click

from .paths import get_server_path


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


def str2bool(string: str, parser=False):
    """Transforms a string to bool.

    Usage:
        >>> str2bool("True")
        True
        >>> str2bool("False")
        False
        >>> str2bool("Invalid", False)
        ValueError("'Invalid' is not a valid boolean")


    Args:
        string (str): input string.
        parser (bool, optional): If True, in case of error it will raise
            argparse.ArgumentTypeError instead of ValueError. If it is used
            inside parse_args, it whould be True. Defaults to False.

    Raises:
        argparse.ArgumentTypeError: if the string is not valid and parser is True.
        ValueError: if the string is not valid and parser is False.

    Returns:
        bool: boolean value of the string.
    """

    if isinstance(string, bool):
        return string

    string = str(string)
    if string.lower() in ("yes", "true", "t", "y", "1", "sí", "si", "s"):
        return True
    if string.lower() in ("no", "false", "f", "n", "0"):
        return False

    if parser:
        raise argparse.ArgumentTypeError("Boolean value expected.")

    raise ValueError(f"{string!r} is not a valid boolean")


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


def click_handle_exception(exc: Exception) -> NoReturn:
    """Handles an exception during click execution.

    Args:
        exc (Exception): exception to handle

    Raises:
        click.ClickException: click exception raised.
    """

    excname = exc.__class__.__name__
    error_msg = f"{excname}: {', '.join([str(x) for x in exc.args])}"
    raise click.ClickException(error_msg)
