"""Module interface with the command line."""

import sys
from argparse import ArgumentParser
from typing import Dict, NoReturn

from .src.dataframe import get_dataframe, get_mode
from .src.files import File
from .src.player import Player
from .src.set_mode import set_mode
from .src.utils import str2bool


class Parser:
    """Command line argument parser."""
    parser = ArgumentParser("default")

    @classmethod
    def error(cls, msg) -> NoReturn:
        """Prints the error to the stderr as well as the program usage."""
        return cls.parser.error(msg)

    @classmethod
    def parse_args(cls) -> Dict[str, str]:
        """Parses the command line arguments using `argparse`.

        Returns:
            Dict[str, str]: arguments parsed.
        """

        parser = ArgumentParser("online-mode-manager")
        subparsers = parser.add_subparsers(dest="command")

        online_mode_parser = subparsers.add_parser("online-mode")
        online_mode_parser.add_argument("online-mode", type=str2bool, nargs="?")

        subparsers.add_parser("list")
        subparsers.add_parser("debug-files")
        subparsers.add_parser("data")
        subparsers.add_parser("whitelist")

        cls._parser = parser
        return vars(parser.parse_args())


def main():
    """Main function."""

    args = Parser.parse_args()
    command = args["command"]

    if command == "online-mode":
        online_mode = args["online-mode"]
        set_mode(mode=online_mode)
        print(f"Set online-mode to {online_mode}")
        sys.exit()

    if command == "data":
        print(get_dataframe())
        sys.exit()

    if command == "list":
        players = Player.generate()
        data = []
        for player in players:
            mode = "online" if get_mode(player.uuid) else "offine"
            data.append((player.username, mode, player.uuid))

        lengths = [max([len(k[x]) for k in data]) for x in range(len(data[0]))]

        for row in data:
            format_data = tuple([x for y in zip(lengths, row) for x in y])
            print(" - %-*s - %-*s - %*s" % format_data)

        sys.exit()

    if command == "debug-files":
        Player.generate()
        for key in File.memory:
            for file in File.memory[key]:
                print(file)


if __name__ == "__main__":
    main()
