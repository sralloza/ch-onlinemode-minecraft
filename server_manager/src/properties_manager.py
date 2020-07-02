import os
import re
import sys
from pathlib import Path
from typing import Union

from colorama import Fore

from server_manager.__main__ import Parser
from .utils import bool2str, str2bool

ONLINE_MODE_PATTERN: re.Pattern = re.compile(r"(online-mode=)(\w+)", re.IGNORECASE)
DATA_PATH = Path(__file__).parent.joinpath("data/server-path.txt")
os.makedirs(DATA_PATH.parent, exist_ok=True)


def get_server_path() -> Path:
    """Returns the server path. If it not stored, it will ask the user and then
    store the response after validating it.

    Returns:
        Path: root dir of the server (folder which contains `server.properties`).
    """

    if DATA_PATH.exists():
        return Path(DATA_PATH.read_text().strip())

    server_path = input("Write the path of the server: ")
    validate_server_path(server_path)

    DATA_PATH.write_text(Path(server_path).as_posix())
    return Path(server_path)


def validate_server_path(server_path: Union[str, Path]):
    server_path = Path(server_path)
    properties_path = get_server_properties_filepath(server_path)
    if not properties_path.exists():
        message = f"server.properties not found: {properties_path.as_posix()}"
        message = f"{Fore.LIGHTRED_EX}{message}{Fore.RESET}"
        print(message, file=sys.stderr)
        sys.exit(-1)


def get_server_properties_filepath(server_path=None) -> Path:
    if not server_path:
        server_path = get_server_path()
    return Path(server_path).joinpath("server.properties")


def properties_manager(online_mode=None):
    """Manages server property `online-mode`.

    Args:
        online_mode (bool, optional): If not passed or None, it will return the current
            online-mode. Otherwise, the server online-mode will be set to `online-mode`
            and the `online-mode` is returned for consistency reasons. Defaults to None.

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
        Parser.error(f"online-mode is already set to {current_online_mode}")
        sys.exit()

    changed_file_data = ONLINE_MODE_PATTERN.sub(
        r"\1" + bool2str(online_mode), file_data
    )
    server_properties_filepath.write_text(changed_file_data, encoding="utf-8")
    return online_mode


def set_server_mode(online_mode: bool):
    return properties_manager(online_mode=online_mode)


def get_server_mode() -> bool:
    return properties_manager(online_mode=None)
