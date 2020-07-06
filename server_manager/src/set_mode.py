"""Checkers needed before setting a new mode."""

import logging
import sys
from server_manager.src.checks import check_players

from .exceptions import InvalidServerStateError
from .player import Player
from .players_data import get_username, get_uuid
from .properties_manager import get_server_mode, get_server_path, set_server_mode


def set_mode(mode):
    """Modifies the online mode of the minecraft server.

    Args:
        mode (bool): new online mode to set.

    Raises:
        InvalidServerStateError: if the server is already running with `mode`.
    """

    logger = logging.getLogger(__name__)
    server_path = get_server_path()
    current_servermode = get_server_mode()

    logger.debug(
        "Setting online-mode=%s (current=%s, path=%s)",
        mode,
        current_servermode,
        server_path.as_posix(),
    )

    players = Player.generate(server_path)

    # TODO: separate to "properties_checks" or something like that
    if mode is None:
        logger.info("server is currently running as %s", current_servermode)
        print(f"server is currently running as {current_servermode}")
        sys.exit()

    if current_servermode == mode:
        logger.critical("server is currently running as %s", current_servermode)
        raise InvalidServerStateError(
            f"server is currently running as {current_servermode}"
        )

    check_players(players)

    for player in players:
        new_uuid = get_uuid(get_username(player.uuid), mode)
        player.change_uuid(new_uuid)

    set_server_mode(mode)
