"""Manages server whitelist."""
import json

from .dataframe import get_dataframe


def create_whitelist() -> str:
    """Creates a minecraft server whitelist with every user present in the
    base64 dataframe, and returns it as a str.

    Returns:
        str: whitelist as str. Must be written to a file named `whitelist.json`.
    """
    dataframe = get_dataframe()
    whitelist = []
    for uuid, player in dataframe.iterrows():
        whitelist.append({"uuid": uuid, "name": player.username})

    return json.dumps(whitelist, indent=4, ensure_ascii=False,)
