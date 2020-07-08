"""Checks to make before changing anything."""

from itertools import groupby
import logging
import sys
from typing import List, Tuple

from colorama.ansi import Fore

from .exceptions import CheckError
from .player import Player
from .plugin import get_plugin_mode
from .properties_manager import get_server_mode


def check_players(players: List[Player]) -> bool:
    """Checks the current files are ok.

    Args:
        players (List[Player]): list of players detected.

    Raises:
        CheckError: if online mode check fails.
        CheckError: if duplicates check fails.

    Returns:
        bool: True for success, False otherwise.
    """

    logger = logging.getLogger(__name__)

    logger.debug("Checking players")

    result = PlayerChecks.check_online_mode(players)
    if not result:
        logger.critical("Online mode check failed")
        raise CheckError("Online mode check failed")

    result = PlayerChecks.check_duplicates(players)
    if not result:
        logger.critical("Duplicates check failed")
        raise CheckError("Duplicates check failed")

    logger.debug("Player checks passed")
    return True


class PlayerChecks:
    """Checks applied to players."""

    @classmethod
    def check_online_mode(cls, players: List[Player]):
        """Checks that all players have the same online-mode, and it matches
        the current server mode.

        Args:
            players (List[Player]): players to check.

        Returns:
            bool: True for success, False otherwise.
        """

        current_server_mode = get_server_mode()
        invalid_modes = []
        for player in players:
            if player.online != current_server_mode:
                invalid_modes.append(player)

        if invalid_modes:
            logger = logging.getLogger(__name__)
            logger.error(
                "These players are using a different mode than the server (%s!=%s): %s",
                invalid_modes[0].online,
                current_server_mode,
                invalid_modes,
            )

            return remove_players_safely(players)
        return True

    @classmethod
    def check_duplicates(cls, players):
        """Checks that there are no players with the same username.

        Args:
            players (List[Player]): players to check.

        Returns:
            bool: True for success, False otherwise.
        """

        duplicates = {}
        for username, players_ in group_players(players):
            nplayers = len(players_)
            if nplayers > 1:
                duplicates[username] = nplayers

        if duplicates:
            logger = logging.getLogger(__name__)
            logger.error(
                "Check result negative: these players "
                "have more than one online mode: %s",
                duplicates,
            )
            return remove_players_safely(players)
        return True


def check_plugin() -> bool:
    """Checks that the current server mode is not the same as the current
    plugin mode, because when the server is running with online-mode=True,
    the plugin is disabled and viceversa.

    Raises:
        CheckError: if the check fails.

    Returns:
        bool: True for sucess.
    """

    logger = logging.getLogger(__name__)
    current_server_mode = get_server_mode()
    plugin_mode = get_plugin_mode()
    if plugin_mode == current_server_mode:
        msg = "Plugin check failed [server-mode=%s, plugin-mode=%s]"
        logger.critical(msg, current_server_mode, plugin_mode)
        raise CheckError(msg % (current_server_mode, plugin_mode))
    return True


def group_players(iterable: List[Player], key=None) -> List[Tuple[str, List[Player]]]:
    """Groups player.

    Args:
        iterable (List[Player]): list of players to group.
        key (callable, optional): function to group the players by. Defaults
            to None, which means that the players will be grouped by username.

    Returns:
        List[Tuple[str, List[Player]]]: list of pairs usermane - users with same username.
    """

    if not key:
        key = lambda x: x.username
    return [(x, list(y)) for x, y in groupby(iterable, key)]


def remove_players_safely(players: List[Player]) -> bool:
    """If some player has an data file with an invalid id, that file
    will be removed if its inventory and its ender chest is empty.

    Args:
        players (List[Players]): list of players to fix?

    Returns:
        bool: True if all players were able to be removed, False otherwise.
    """

    logger = logging.getLogger(__name__)
    error = False

    for player in players:
        logger.debug("Analysing player %s [%s]", player.username, player.online)
        ender_chest = player.get_ender_chest()
        inventory = player.get_inventory()

        if ender_chest or inventory:
            ender_chest = len(ender_chest)
            inventory = len(inventory)
            msg = "Can't remove player %s\nItems: ender_chest=%d, inventory=%d"
            args = (player.to_extended_repr(), ender_chest, inventory)
            logger.error(msg, *args)
            print(Fore.LIGHTRED_EX + msg % args + Fore.RESET, file=sys.stderr)
            error = True
            continue

        player.remove()
        logger.info("Removed player %s [%s]", player.username, player.online)

    return error
