"""Checkers needed before setting a new mode."""

import logging
from typing import List

from .checks import check_players
from .player import Player
from .players_data import get_username, get_uuid
from .properties_manager import get_server_mode, get_server_path, set_server_mode


def set_mode(new_mode):
    """Modifies the online mode of the minecraft server.

    Args:
        new_mode (bool): new online mode to set.

    Raises:
        ValueError: if the server is already running with `new_mode`.
        CheckError: if some checks do not pass.
    """

    logger = logging.getLogger(__name__)
    server_path = get_server_path()
    current_servermode = get_server_mode()

    logger.debug(
        "Setting online-mode=%s (current=%s, path=%s)",
        new_mode,
        current_servermode,
        server_path.as_posix(),
    )

    if current_servermode == new_mode:
        msg = "server is already running with online-mode=%s"
        logger.critical(msg, current_servermode)
        raise ValueError(msg % current_servermode)

    players = Player.generate(server_path)
    check_players(players)
    change_players_mode(players, new_mode)

    set_server_mode(new_mode)


def change_players_mode(players: List[Player], new_mode: bool):
    """Changes the online-mode for all `players`.

    Args:
        players (List[Player]): list of players to change online-mode.
        new_mode (bool): new online-mode to set.
    """

    for player in players:
        new_uuid = get_uuid(get_username(player.uuid), new_mode)
        player.change_uuid(new_uuid)
