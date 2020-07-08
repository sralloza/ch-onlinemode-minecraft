"""Module interface with the command line."""

from argparse import ArgumentParser
import logging
from typing import Any, Dict, NoReturn

from .src.backup import create_backup, get_backups_folder
from .src.checks import remove_players_safely
from .src.files import File
from .src.player import Player
from .src.players_data import get_mode, get_players_data
from .src.properties_manager import get_server_mode
from .src.set_mode import set_mode
from .src.utils import str2bool
from .src.whitelist import update_whitelist


def setup_logging():
    """Configure logging."""

    fmt = "[%(asctime)s] %(levelname)s - %(name)s:%(lineno)s - %(message)s"
    filename = get_backups_folder().joinpath("lia-manager.log")
    handlers = [logging.FileHandler(filename, "at", "utf8")]
    logging.basicConfig(level=10, format=fmt, handlers=handlers)


class Parser:
    """Command line argument parser."""

    parser = ArgumentParser("default")

    @classmethod
    def error(cls, msg) -> NoReturn:
        """Prints the error to the stderr as well as the program usage.

        Arguments:
            msg (str): message to show.

        Returns:
            NoReturn: this function does not return.

        """
        return cls.parser.error(msg)

    @classmethod
    def parse_args(cls) -> Dict[str, Any]:
        """Parses the command line arguments using `argparse`.

        Returns:
            Dict[str, Any]: arguments parsed.
        """

        parser = ArgumentParser("lia")
        subparsers = parser.add_subparsers(dest="command")

        subparsers.add_parser("backup", help="backup server")
        subparsers.add_parser(
            "debug-files", help="list all files containing player data in server"
        )
        subparsers.add_parser("get-online-mode", help="print current online-mode")
        subparsers.add_parser("list-csv-players", help="show players registered in csv")
        subparsers.add_parser(
            "list-server-players", help="show players found in server"
        )
        subparsers.add_parser("reset-players", help="remove all players safely")

        online_mode_parser = subparsers.add_parser("set-online-mode")
        online_mode_parser.add_argument(
            "online-mode", type=str2bool, help="new online-mode to set"
        )

        subparsers.add_parser(
            "update-whitelist", help="update whitelist using csv data"
        )

        cls.parser = parser
        return vars(parser.parse_args())


def main():  # pylint: disable=too-many-return-statements, inconsistent-return-statements
    """Main function."""

    args = Parser.parse_args()
    setup_logging()
    command = args["command"]

    if command == "backup":
        return Commands.backup()

    if command == "list-csv-players":
        return Commands.print_players_data()

    if command == "debug-files":
        return Commands.print_files()

    if command == "get-online-mode":
        return Commands.get_online_mode()

    if command == "list-server-players":
        return Commands.list_players()

    if command == "reset-players":
        return Commands.reset_players()

    if command == "set-online-mode":
        return Commands.set_online_mode(args["online-mode"])

    if command == "update-whitelist":
        return Commands.update_whitelist()

    return Parser.error("Must select command")


class Commands:
    """All possible commands executed via command line."""

    @classmethod
    def backup(cls):
        """Makes a backup of the minecraft server folder."""
        create_backup()

    @classmethod
    def get_online_mode(cls):
        """Prints the current server online-mode."""

        current_servermode = get_server_mode()
        print(f"server is currently running as {current_servermode}")

    @classmethod
    def set_online_mode(cls, online_mode: bool):
        """Sets the server online-mode.

        Args:
            online_mode (bool): new server online-mode
        """

        set_mode(new_mode=online_mode)
        print(f"Set online-mode to {online_mode}")

    @classmethod
    def print_players_data(cls):
        """Prints the players data from parsing the csv."""

        for player in get_players_data():
            print(" -", player)

    @classmethod
    def list_players(cls):
        """Prints all the server's players information."""

        players = Player.generate()
        data = []
        for player in players:
            mode = "online" if get_mode(player.uuid) else "offline"
            data.append((player.username, mode, player.uuid))

        lengths = [max([len(k[x]) for k in data]) for x in range(len(data[0]))]

        for row in data:
            format_data = tuple([x for y in zip(lengths, row) for x in y])
            print(" - %-*s - %-*s - %*s" % format_data)

    @classmethod
    def print_files(cls):
        """Prints all the files containing players data."""

        Player.generate()
        for key in File.memory:
            for file in File.memory[key]:
                print(file)

    @classmethod
    def update_whitelist(cls):
        """Writes an updated whitelist to the whitelist file (`whitelist.json`)."""

        return update_whitelist()

    @classmethod
    def reset_players(cls):
        """Removes all the players data if each player has the ender chest
        and the inventory emtpy.

        """

        players = Player.generate()
        return remove_players_safely(players)
