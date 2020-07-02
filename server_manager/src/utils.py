"""Useful functions to all the package."""

import argparse


class Memory:
    """Class to store the parser."""

    _parser = None

    @classmethod
    def set_parser(cls, parser):
        cls._parser = parser

    @classmethod
    def get_parser(cls):
        return cls._parser


def bool2str(boolean: bool):
    """Returns a bool as a string (in lowercase, as json).

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
    if string.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if string.lower() in ("no", "false", "f", "n", "0"):
        return False

    if parser:
        raise argparse.ArgumentTypeError("Boolean value expected.")

    raise ValueError(f"{string!r} is not a valid boolean")
