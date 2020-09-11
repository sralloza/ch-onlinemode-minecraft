"""Module interface with the command line."""

import logging

import click
from colorama import init

from . import __version__
from .src.backup import create_backup, get_backups_folder
from .src.checks import remove_players_safely
from .src.files import File
from .src.paths import get_server_path
from .src.player import Player
from .src.players_data import get_mode, get_players_data
from .src.properties_manager import PropertiesManager, set_default_properties
from .src.set_mode import set_mode
from .src.utils import click_handle_exception
from .src.whitelist import update_whitelist


def setup_logging():
    """Configures logging."""

    fmt = "[%(asctime)s] %(levelname)s - %(name)s:%(lineno)s - %(message)s"
    filename = get_backups_folder().joinpath("lia-manager.log")
    handlers = [logging.FileHandler(filename, "at", "utf8")]
    logging.basicConfig(level=10, format=fmt, handlers=handlers)


# pylint: disable=missing-raises-doc,missing-param-doc,missing-type-doc,missing-return-type-doc

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

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="lia")
def main():
    """LIA utils"""
    setup_logging()
    init(autoreset=True)


@main.command("backup", help=helpers["backup"])
def backup():
    """Makes a backup of the minecraft server folder"""
    create_backup()


@main.group("online-mode")
def online_mode_command():
    """Manages server's online mode"""


@online_mode_command.command("get")
@click_handle_exception
def get_online_mode():
    """Prints the current server online-mode"""

    current_servermode = PropertiesManager.get_property("online_mode")
    print(f"server is currently running as {current_servermode}")


@online_mode_command.command("set")
@click.argument("online-mode", type=bool)
@click_handle_exception
def set_online_mode(online_mode: bool):
    """Sets the server online-mode"""

    set_mode(new_mode=online_mode)
    print(f"Set online-mode to {online_mode}")


@main.group("players")
def players():
    """Manages players"""


@players.command("list-csv")
def print_players_data():
    """Prints the players data from parsing the csv"""
    csv_players = get_players_data()
    if not csv_players:
        print("<no players found in the csv>")
        return

    for player in csv_players:
        print(" -", player)


@players.command("list-server")
def list_players():
    """Prints all the server's players information"""

    server_players = Player.generate()
    if not server_players:
        print("<no players found in the server archives>")
        return

    data = []
    data.append(("username", "mode", "uuid", "inventory", "ender-chest"))

    for player in server_players:
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
    and the inventory emtpy"""

    server_players = Player.generate()
    return remove_players_safely(server_players, force=force)


@players.command("show")
@click.argument("player-name", type=str)
def show_player(player_name: str):
    """Prints the detailed items in the inventory and ender chest of the player"""

    player_name = player_name.lower()
    server_players = Player.generate()
    for player in server_players:
        if player.username.lower() == player_name:
            print("\nPlayer position:", player.get_position())
            print("\nInventory:", player.get_detailed_inventory())
            print("\nEnder chest:", player.get_detailed_ender_chest())
            return

    raise click.ClickException(f"No player named {player_name!r}")


@main.group("properties")
@click_handle_exception
def properties():
    """Manage settings of server.properties"""


@properties.command("set-defaults")
@click_handle_exception
def set_defaults():
    """Set default values for all properties"""

    set_default_properties()


@properties.command("list")
@click_handle_exception
def list_properties():
    """Lists all the properties and its values"""

    for propname in PropertiesManager.general_map:
        print(f"{propname}={PropertiesManager.get_property(propname)}")


@properties.command("get")
@click.argument("property_", metavar="PROPERTY")
@click_handle_exception
def get_property(property_):
    """Get a property"""

    value = PropertiesManager.get_property(property_)
    print(f"{property_}={value}")


@properties.command("set")
@click.argument("property_", metavar="PROPERTY")
@click.argument("value")
@click_handle_exception
def set_property(property_, value):
    """Set a property"""

    data = {property_: value}
    return PropertiesManager.set_property(**data)


@main.group("debug")
def debug():
    """Debug tools"""


@debug.command("files")
def print_files():
    """Prints all the files containing players data"""

    File.gen_files(get_server_path())
    for key in File.memory:
        for file in File.memory[key]:
            print(file)


@main.command("update-whitelist")
def cli_update_whitelist():
    """Updates the whitelist using data from the csv"""

    # TODO: test this call and update docstrign
    # ensure_whitelist_on()
    return update_whitelist()


if __name__ == "__main__":
    main()
