"""Manages plugin SkinRestorer."""

from pathlib import Path

from .exceptions import InvalidPluginStateError
from .paths import get_server_path

PLUGIN_NAME = "SkinsRestorer.jar"
PLUGIN_DISABLED_NAME = "SkinsRestorer.jar.disabled"


def get_plugins_folder() -> Path:
    """Returns the server plugins folder.

    Returns:
        Path: server plugins folder.
    """

    server_path = get_server_path()
    return server_path.joinpath("plugins")


def get_plugin_offline_path() -> Path:
    """Returns the path of the plugin when server is offline.

    Returns:
        Path: offline plugin path.
    """

    plugins_folder = get_plugins_folder()
    return plugins_folder.joinpath(PLUGIN_DISABLED_NAME)


def get_plugin_online_path() -> Path:
    """Returns the path of the plugin when server is online.

    Returns:
        Path: online plugin path.
    """

    plugins_folder = get_plugins_folder()
    return plugins_folder.joinpath(PLUGIN_NAME)


def get_plugin_mode() -> bool:
    """Returns the current plugin mode.

    Raises:
        InvalidPluginStateError: if plugin is neither online nor offline.

    Returns:
        bool: current plugin mode.
    """

    plugin_offline_path = get_plugin_offline_path()
    if plugin_offline_path.is_file():
        return False

    plugin_online_path = get_plugin_online_path()
    if plugin_online_path.is_file():
        return True

    raise InvalidPluginStateError("Plugin is neither online nor offile")


def set_plugin_mode(new_mode: bool):
    """Changes the plugin mode to `new_mode`.

    Args:
        new_mode (bool): new plugin mode to set.
    """

    if new_mode:
        # Now the plugin is enabled, we need to disable it.
        old = get_plugin_offline_path()
        new = get_plugin_online_path()
    else:
        # Now the plugin is disabled, we need to enable it.
        old = get_plugin_online_path()
        new = get_plugin_offline_path()

    old.rename(new)
