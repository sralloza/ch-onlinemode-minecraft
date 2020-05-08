import argparse


class Memory:
    parser = None


def bool2str(b):
    return str(b).lower()


def str2bool(v, parser=False):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        if parser:
            raise argparse.ArgumentTypeError("Boolean value expected.")
        else:
            raise ValueError(f"{v!r} is not a valid boolean")
