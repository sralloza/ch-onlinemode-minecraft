import logging
import sys
from itertools import groupby
from typing import List

from .dataframe import get_mode, get_username, get_uuid
from .exceptions import InvalidPlayerDataStateError, InvalidStateError
from .player import Player
from .properties_manager import get_server_mode, get_server_path, set_server_mode


def group_players(iterable, key=None):
    if not key:
        key = lambda x: x.username
    return [(x, list(y)) for x, y in groupby(iterable, key)]


def fix_players(players):
    current_server_mode = get_server_mode()

    for username, subplayers in group_players(players):
        print(username, subplayers)
    sys.exit()


def check_players(players: List[Player]):
    """It checks the current files are ok.

    Args:
        players (List[Player]): list of players detected.
    """

    logger = logging.getLogger(__name__)

    # Checking that players can only have one online mode
    logger.debug("Checking players integrity")

    current_server_mode = get_server_mode()

    invalid_modes = []
    for player in players:
        if player.online != current_server_mode:
            invalid_modes.append(player)

    if invalid_modes:
        logger.error(
            "These players are using a different mode than the server (%s!=%s): %s",
            invalid_modes[0].online,
            current_server_mode,
            invalid_modes,
        )
        fix_players(players)

    duplicates = {}
    for username, players_ in group_players(players):
        nplayers = len(players_)
        if nplayers > 1:
            duplicates[username] = nplayers

    if duplicates:
        logger.error(
            "Check result negative: these players "
            "have more than one online mode: %s",
            duplicates,
        )
        fix_players(players)

    logger.debug("Player checks passed")
    return players


def set_mode(mode=None):
    logger = logging.getLogger(__name__)
    server_path = get_server_path()
    current_servermode = get_server_mode()

    logger.debug(
        "Setting online-mode=%s (current=%s, path=%s)",
        mode,
        current_servermode,
        server_path.as_posix(),
    )

    # TODO: question: if player data is wrong (multiple user data) and mode is None,
    # error needs to be raised?

    players = Player.generate(server_path)
    check_players(players)

    if mode is None:
        logger.info("server is currently running as %s", current_servermode)
        print(f"server is currently running as {current_servermode}")
        sys.exit()

    if current_servermode == mode:
        logger.critical("server is currently running as %s", current_servermode)
        raise InvalidServerStateError(
            f"server is currently running as {current_servermode}"
        )

    for player in players:
        current_player_mode = get_mode(player.uuid)

        if current_player_mode == mode:
            username = get_username(player.uuid)
            msg = (
                "While setting mode %s, found player with same mode"
                " when it should have mode=%s: %r\n %s"
            )
            args = (mode, not mode, username, player.to_extended_repr())

            logger.critical(msg, *args)
            # TODO: more meaningful name for exception
            raise InvalidPlayerDataStateError(msg % args)

        new_uuid = get_uuid(get_username(player.uuid), mode)
        player.change_uuid(new_uuid)

    set_server_mode(mode)
