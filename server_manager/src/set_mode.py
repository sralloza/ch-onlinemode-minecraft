"""Checkers needed before setting a new mode."""

import logging

from .checks import check_players
from .player import Player
from .player import change_players_mode
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

    # Checks
    check_players(players)

    # Setters
    change_players_mode(players, new_mode)
    set_server_mode(new_mode)


