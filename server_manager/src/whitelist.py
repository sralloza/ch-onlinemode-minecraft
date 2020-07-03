"""Manages server whitelist."""
import json

from .dataframe import get_players_data


def create_whitelist() -> str:
    """Creates a minecraft server whitelist with every user present in the
    base64 dataframe, and returns it as a str.

    Returns:
        str: whitelist as str. Must be written to a file named `whitelist.json`.
    """

    players_data = get_players_data()
    whitelist = []

    for player in players_data:
        whitelist.append({"uuid": player.uuid, "name": player.username})

    return json.dumps(whitelist, indent=4, ensure_ascii=False,)
