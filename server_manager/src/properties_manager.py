"""Manages the properties of the minecraft server (`server.properties`)."""

from enum import Enum
from functools import lru_cache
from pathlib import Path
import re
import sys

from colorama import Fore

from .exceptions import InvalidServerStateError
from .paths import get_server_path
from .utils import bool2str, str2bool


class Patterns:
    online_mode = re.compile(r"(online-mode=)(\w+)", re.IGNORECASE)
    whitelist_1 = re.compile(r"(enforce-whitelist=)(\w+)", re.IGNORECASE)
    whitelist_2 = re.compile(r"(white-list=)(\w+)", re.IGNORECASE)


class Properties(Enum):
    online_mode = "online-mode"
    whitelist = "whitelist"


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


class PropertiesManager:
    @classmethod
    @lru_cache(maxsize=10)
    def get_property(cls, request: Properties) -> bool:
        return cls.getters_map[request]()

    @classmethod
    def set_property(cls, **kwargs) -> bool:
        for property_ in cls.setters_map:
            if kwargs.get(property_.name):
                cls.setters_map[property_](kwargs.get(property_.name))
                break
        else:
            raise ValueError("Must set one argument")

    @classmethod
    @lru_cache(maxsize=10)
    def get_properties_raw(cls) -> str:
        """Returns the content of `server.properties` as utf-8 text.

        Returns:
            str: contents of `server.properties`.
        """

        server_properties_filepath = get_server_properties_filepath()
        return server_properties_filepath.read_text(encoding="utf-8")

    @classmethod
    def write_properties_raw(cls, raw_properties: str):
        """Writes `raw_properties` into the server properties file (`server.properties`).

        Args:
            raw_properties (str): contents of `server.properties` to save.
        """

        server_properties_filepath = get_server_properties_filepath()
        server_properties_filepath.write_text(raw_properties, encoding="utf-8")

    @classmethod
    def get_current_online_mode(cls) -> bool:
        file_data = cls.get_properties_raw()
        return str2bool(Patterns.online_mode.search(file_data).group(2), parser=False)

    @classmethod
    def get_current_whitelist_state(cls) -> bool:
        file_data = cls.get_properties_raw()
        state1 = str2bool(Patterns.whitelist_1.search(file_data).group(2), parser=False)
        state2 = str2bool(Patterns.whitelist_2.search(file_data).group(2), parser=False)

        if state1 != state2:
            # TODO: improve exception name and log exception
            msg = "Properties white-list (%s) and enforce-whitelist (%s) can't be different"
            raise Exception(msg)
        return state1

    @classmethod
    def set_online_mode(cls, online_mode: bool) -> bool:
        """Sets a new online-mode for the server itself (server.properties).

        Args:
            online_mode (bool): new online_mode to set.

        Raises:
            InvalidServerStateError: if `online_mode` is the current server mode.

        Returns:
            bool: new server online mode.
        """

        current_online_mode = cls.get_current_online_mode()
        if online_mode == current_online_mode:
            # TODO: log exception?
            raise InvalidServerStateError(
                f"online-mode is already set to {current_online_mode}"
            )

        file_data = cls.get_properties_raw()
        file_data = Patterns.online_mode.sub(r"\1" + bool2str(online_mode), file_data)
        cls.write_properties_raw(file_data)
        return online_mode

    @classmethod
    def set_whitelist_state(cls, whl_state: bool) -> bool:
        current_whitelist_state = cls.get_current_whitelist_state()
        if whl_state == current_whitelist_state:
            # TODO: log exception?
            # TODO: improve exception name
            raise InvalidServerStateError(
                f"online-mode is already set to {current_whitelist_state}"
            )

        file_data = cls.get_properties_raw()
        file_data = Patterns.whitelist_1.sub(r"\1" + bool2str(whl_state), file_data)
        file_data = Patterns.whitelist_2.sub(r"\1" + bool2str(whl_state), file_data)
        cls.write_properties_raw(file_data)
        return whl_state

    # After defining getters, define getters map
    getters_map = {
        Properties.online_mode: get_current_online_mode,
        Properties.whitelist: get_current_whitelist_state,
    }

    setters_map = {
        Properties.online_mode: set_online_mode,
        Properties.whitelist: set_whitelist_state,
    }


@lru_cache(maxsize=10)
def get_server_mode() -> bool:
    """Returns the current server mode.

    Returns:
        bool: current server mode.
    """

    return PropertiesManager.get_property(Properties.online_mode)


def set_server_mode(online_mode: bool) -> bool:
    """Sets the server mode to `online_mode`.

    Args:
        online_mode (bool): new online mode to set.

    Returns:
        bool: current online mode after change.
    """

    return PropertiesManager.set_property(online_mode=online_mode)


@lru_cache(maxsize=10)
def get_whitelist_state() -> bool:
    return PropertiesManager.get_property(Properties.whitelist)


def set_whitelist_state(whitelist_state: bool):
    return PropertiesManager.set_property(whitelist=whitelist_state)
