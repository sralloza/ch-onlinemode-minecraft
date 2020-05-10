import argparse


class Memory:
    _parser = None

    @classmethod
    def set_parser(cls, parser):
        cls._parser = parser

    @classmethod
    def get_parser(cls):
        return cls._parser


def bool2str(boolean):
    return str(boolean).lower()


def str2bool(string, parser=False):
    if isinstance(string, bool):
        return string
    if string.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if string.lower() in ("no", "false", "f", "n", "0"):
        return False

    if parser:
        raise argparse.ArgumentTypeError("Boolean value expected.")

    raise ValueError(f"{string!r} is not a valid boolean")
