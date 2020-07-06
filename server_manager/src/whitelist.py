"""Manages server whitelist."""
import json

from .players_data import get_players_data
from .properties_manager import get_server_properties_filepath


def create_whitelist() -> str:
    """Creates a minecraft server whitelist with every user recorded,
    and returns it as a str.

    Returns:
        str: whitelist as str. Must be written to a file named `whitelist.json`.
    """

    players_data = get_players_data()
    whitelist = []

    for player in players_data:
        whitelist.append({"uuid": player.uuid, "name": player.username})

    return json.dumps(whitelist, indent=4, ensure_ascii=False)


def update_whitelist():
    """Writes an updated whitelist to the whitelist file (`whitelist.json`)."""

    whitelist_path = get_server_properties_filepath().with_name("whitelist.json")
    whitelist_path.write_text(create_whitelist())
