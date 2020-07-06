"""Module interface with the command line."""

from argparse import ArgumentParser
from typing import Dict, NoReturn

from server_manager.src.properties_manager import get_server_mode
from .src.files import File
from .src.player import Player
from .src.players_data import get_mode, get_players_data
from .src.set_mode import set_mode
from .src.utils import str2bool
from .src.whitelist import update_whitelist


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

        parser = ArgumentParser("server-manager")
        subparsers = parser.add_subparsers(dest="command")

        online_mode_parser = subparsers.add_parser("set-online-mode")
        online_mode_parser.add_argument("online-mode", type=str2bool)

        subparsers.add_parser("get-online-mode")
        subparsers.add_parser("list")
        subparsers.add_parser("debug-files")
        subparsers.add_parser("data")
        subparsers.add_parser("whitelist")

        cls.parser = parser
        return vars(parser.parse_args())


def main():  # pylint: disable=too-many-return-statements, inconsistent-return-statements
    """Main function."""

    args = Parser.parse_args()
    command = args["command"]

    if command == "get-online-mode":
        current_servermode = get_server_mode()
        print(f"server is currently running as {current_servermode}")
        return

    if command == "set-online-mode":
        online_mode = args["online-mode"]
        set_mode(mode=online_mode)

        print(f"Set online-mode to {online_mode}")
        return

    if command == "data":
        for player in get_players_data():
            print(" -", player)
        return

    if command == "list":
        players = Player.generate()
        data = []
        for player in players:
            mode = "online" if get_mode(player.uuid) else "offline"
            data.append((player.username, mode, player.uuid))

        lengths = [max([len(k[x]) for k in data]) for x in range(len(data[0]))]

        for row in data:
            format_data = tuple([x for y in zip(lengths, row) for x in y])
            print(" - %-*s - %-*s - %*s" % format_data)

        return

    if command == "debug-files":
        Player.generate()
        for key in File.memory:
            for file in File.memory[key]:
                print(file)
        return

    if command == "whitelist":
        return update_whitelist()

    return Parser.error("Must select command")
