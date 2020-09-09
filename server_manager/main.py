"""Module interface with the command line."""

from argparse import ArgumentParser
import logging
from typing import Any, Dict, NoReturn

import click

from .src.backup import create_backup, get_backups_folder
from .src.checks import remove_players_safely
from .src.exceptions import InvalidPlayerError
from .src.files import File
from .src.paths import get_server_path
from .src.player import Player
from .src.players_data import get_mode, get_players_data
from .src.properties_manager import PropertiesManager
from .src.set_mode import set_mode
from .src.utils import str2bool
from .src.whitelist import update_whitelist


def setup_logging():
    """Configure logging."""

    fmt = "[%(asctime)s] %(levelname)s - %(name)s:%(lineno)s - %(message)s"
    filename = get_backups_folder().joinpath("lia-manager.log")
    handlers = [logging.FileHandler(filename, "at", "utf8")]
    logging.basicConfig(level=10, format=fmt, handlers=handlers)


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
    "show-player": "print detailed inventory and ender chest of player",
    "show-player-arg": "player to show",
    "update-whitelist": "update whitelist using csv data",
}


@click.group()
def main():
    setup_logging()


@main.command("backup")
def backup():
    """Makes a backup of the minecraft server folder."""
    create_backup()


@main.group("online-mode")
def online_mode():
    """Manages server's online mode."""


@online_mode.command("get")
def get_online_mode():
    """Prints the current server online-mode."""

    current_servermode = PropertiesManager.get_property("online_mode")
    print(f"server is currently running as {current_servermode}")


@online_mode.command("set")
@click.argument("online-mode", type=bool)
def set_online_mode(online_mode: bool):
    """Sets the server online-mode.

    Args:
        online_mode (bool): new server online-mode
    """

    try:
        set_mode(new_mode=online_mode)
    except Exception as exc:
        raise click.ClickException(", ".join(exc.args))
    print(f"Set online-mode to {online_mode}")


@main.group("players")
def players():
    """Manages players"""


@players.command("list-csv")
def print_players_data():
    """Prints the players data from parsing the csv."""
    players = get_players_data()
    if not players:
        print("<no players found in the csv>")
        return

    for player in players:
        print(" -", player)


@players.command("list-server")
def list_players():
    """Prints all the server's players information."""

    players = Player.generate()
    if not players:
        print("<no players found in the server archives>")
        return

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


@players.command("reset")
@click.option("--force", is_flag=True)
def reset_players(force: bool) -> bool:
    """Removes all the players' data if each player has the ender chest
    and the inventory emtpy."""

    players = Player.generate()
    return remove_players_safely(players, force=force)


@players.command("show")
@click.argument("player-name", type=str)
def show_player(player_name: str):
    """Prints the detailed items in the inventory and ender chest of the player"""

    player_name = player_name.lower()
    players = Player.generate()
    for player in players:
        if player.username.lower() == player_name:
            print("Inventory:")
            print(player.get_detailed_inventory())
            print("\nEnder chest:")
            print(player.get_detailed_ender_chest())
            return

    raise click.ClickException(f"No player named {player_name!r}")


@main.group("debug")
def debug():
    """Debug tools."""


@debug.command("files")
def print_files():
    """Prints all the files containing players data."""

    File.gen_files(get_server_path())
    for key in File.memory:
        for file in File.memory[key]:
            print(file)


@main.command("update-whitelist")
def cli_update_whitelist():
    """Writes an updated whitelist to the whitelist file (`whitelist.json`)."""

    # TODO: test this call and update docstrign
    # ensure_whitelist_on()
    return update_whitelist()


if __name__ == "__main__":
    main()
