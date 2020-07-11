"""Manages the properties of the minecraft server (`server.properties`),
especially `online-mode`.
"""

from functools import lru_cache
from pathlib import Path
import re
import sys

from colorama import Fore

from .exceptions import InvalidServerStateError
from .paths import get_server_path
from .utils import bool2str, str2bool

ONLINE_MODE_PATTERN: re.Pattern = re.compile(r"(online-mode=)(\w+)", re.IGNORECASE)


def validate_server_path(server_path: str):
    """Validates the `server_path`, ensuring that the server.properties file
    does exist inside the `server_path`.

    Args:
        server_path (Union[str, Path]): server path.
    """

    properties_path = get_server_properties_filepath(server_path)
    if not properties_path.is_file():
        message = f"server.properties not found: {properties_path.as_posix()!r}"
        message = f"{Fore.LIGHTRED_EX}{message}{Fore.RESET}"
        print(message, file=sys.stderr)
        sys.exit(-1)


@lru_cache(maxsize=10)
def get_server_properties_filepath(server_path: str = None) -> Path:
    """Returns the path of the server properties file (`server.properties`).

    Args:
        server_path (str, optional): server path. If None, the server path will
            be obtained by get_server_path(). Defaults to None.

    Returns:
        Path: server properties file path.
    """

    real_server_path = server_path or get_server_path()
    return Path(real_server_path).joinpath("server.properties")


def properties_manager(online_mode=None):
    """Manages server property `online-mode`.

    Args:
        online_mode (bool, optional): If not passed or None, it will return the current
            online-mode. Otherwise, the server online-mode will be set to `online-mode`
            and the `online-mode` is returned for consistency reasons. Defaults to None.

    Raises:
        InvalidServerStateError: if `online_mode` is equal to the current online mode.

    Returns:
        bool: server new online mode.
    """

    server_properties_filepath = get_server_properties_filepath()
    file_data = server_properties_filepath.read_text(encoding="utf-8")
    current_online_mode = str2bool(
        ONLINE_MODE_PATTERN.search(file_data).group(2), parser=False
    )

    if online_mode is None:
        return current_online_mode

    if online_mode == current_online_mode:
        raise InvalidServerStateError(
            f"online-mode is already set to {current_online_mode}"
        )

    changed_file_data = ONLINE_MODE_PATTERN.sub(
        r"\1" + bool2str(online_mode), file_data
    )
    server_properties_filepath.write_text(changed_file_data, encoding="utf-8")
    return online_mode


def set_server_mode(online_mode: bool):
    """Sets the server mode to `online_mode`.

    Args:
        online_mode (bool): new online mode to set.

    Returns:
        bool: current online mode after change.
    """

    return properties_manager(online_mode=online_mode)


@lru_cache(maxsize=10)
def get_server_mode() -> bool:
    """Returns the current server mode.

    Returns:
        bool: current server mode.
    """

    return properties_manager(online_mode=None)
