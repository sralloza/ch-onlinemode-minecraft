import argparse
import sys

from src.dataframe import get_dataframe
from src.set_mode import set_mode
from src.utils import Memory, str2bool


def parse_args() -> dict:
    parser = argparse.ArgumentParser("online-mode-manager")
    subparsers = parser.add_subparsers(dest="command")

    online_mode_parser = subparsers.add_parser("online-mode")
    online_mode_parser.add_argument("online-mode", type=str2bool, nargs="?")

    data_parser = subparsers.add_parser("data")

    whitelist_parser = subparsers.add_parser("whitelist")

    Memory.set_parser(parser)
    return vars(parser.parse_args())


def main():
    args = parse_args()
    command = args["command"]

    if command == "online-mode":
        online_mode = args["online-mode"]
        set_mode(mode=online_mode)
        print(f"Set online-mode to {online_mode}")
        sys.exit()

    if command == "data":
        print(get_dataframe())
        sys.exit()


if __name__ == "__main__":
    main()
