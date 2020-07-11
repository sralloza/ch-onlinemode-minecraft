"""Module interface with the command line."""

from argparse import ArgumentParser
import logging
from typing import Any, Dict, NoReturn

from .src.backup import create_backup, get_backups_folder
from .src.checks import remove_players_safely
from .src.files import File
from .src.paths import get_server_path
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
    def print_help(cls):
        """Prints the Parser's help."""
        cls.parser.print_help()

    @classmethod
    def parse_args(cls) -> Dict[str, Any]:
        """Parses the command line arguments using `argparse`.

        Returns:
            Dict[str, Any]: arguments parsed.
        """

        helpers = {
            "backup": "backup server",
            "debug-files": "list all files containing player data in server",
            "get-online-mode": "print current online-mode",
            "list-csv-players": "show players registered in csv",
            "list-server-players": "show players found in server",
            "reset-players": "remove all players safely",
            "reset-players-force": "forces removal of players",
            "set-online-mode": "set a new online-mode",
            "set-online-mode-arg": "new online-mode to set",
            "update-whitelist": "update whitelist using csv data",
        }

        parser = ArgumentParser("lia")
        subparsers = parser.add_subparsers(dest="command")

        subparsers.add_parser("backup", help=helpers["backup"])
        subparsers.add_parser("debug-files", help=helpers["debug-files"])
        subparsers.add_parser("get-online-mode", help=helpers["get-online-mode"])
        subparsers.add_parser("list-csv-players", help=helpers["list-csv-players"])
        subparsers.add_parser(
            "list-server-players", help=helpers["list-server-players"]
        )
        reset_parser = subparsers.add_parser(
            "reset-players", help=helpers["reset-players"]
        )
        reset_parser.add_argument(
            "--force", action="store_true", help=helpers["reset-players-force"]
        )

        online_mode_parser = subparsers.add_parser(
            "set-online-mode", help=helpers["set-online-mode"]
        )
        online_mode_parser.add_argument(
            "online-mode", type=str2bool, help=helpers["set-online-mode-arg"]
        )

        subparsers.add_parser("update-whitelist", help=helpers["update-whitelist"])

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
        return Commands.reset_players(args["force"])

    if command == "set-online-mode":
        return Commands.set_online_mode(args["online-mode"])

    if command == "update-whitelist":
        return Commands.update_whitelist()

    return Parser.print_help()


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
        data.append(("username", "mode", "uuid", "inventory", "ender-chest"))

        for player in players:
            mode = "online" if get_mode(player.uuid) else "offline"
            inventory = str(len(player.get_inventory()))
            ender_chest = str(len(player.get_ender_chest()))
            data.append((player.username, mode, player.uuid, inventory, ender_chest))

        lengths = [max([len(k[x]) for k in data]) for x in range(len(data[0]))]

        for row in data:
            format_data = tuple([x for y in zip(row, lengths) for x in y])
            output_str = " | {:{}} - {:^{}} - {:^{}} - {:^{}} - {:^{}} |"
            print(output_str.format(*format_data))

    @classmethod
    def print_files(cls):
        """Prints all the files containing players data."""

        File.gen_files(get_server_path())
        for key in File.memory:
            for file in File.memory[key]:
                print(file)

    @classmethod
    def update_whitelist(cls):
        """Writes an updated whitelist to the whitelist file (`whitelist.json`)."""

        return update_whitelist()

    @classmethod
    def reset_players(cls, force: bool) -> bool:
        """Removes all the players data if each player has the ender chest
        and the inventory emtpy.

        Args:
            force (bool): if True, inventory and ender chest checkers
                will be ignored.

        Returns:
            bool: True if all players were able to be removed, False otherwise.
        """

        players = Player.generate()
        return remove_players_safely(players, force=force)
