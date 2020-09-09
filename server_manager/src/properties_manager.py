"""Manages the properties of the minecraft server (`server.properties`)."""

from enum import Enum
from functools import lru_cache
import logging
from pathlib import Path
import re
import sys
from typing import Union

from colorama import Fore

from server_manager.src.utils import Validators

from .exceptions import PropertyError
from .paths import get_server_path
from .utils import bool2str, str2bool

PropertiesLike = Union["Properties", str]
logger = logging.getLogger(__name__)


class Properties(Enum):
    allow_nether = "allow-nether"
    broadcast_rcon_to_ops = "broadcast-rcon-to-ops"
    difficulty = "difficulty"
    enable_rcon = "enable-rcon"
    enable_status = "enable-status"
    max_players = "max-players"
    online_mode = "online-mode"
    rcon_password = "rcon.password"
    rcon_port = "rcon.port"
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
    getters_map = {}
    setters_map = {}

    @classmethod
    @lru_cache(maxsize=10)
    def get_property(cls, request: PropertiesLike):
        request = Properties(request)
        return cls.getters_map[request]()

    @classmethod
    def set_property(cls, **kwargs):
        for property_ in cls.setters_map:
            if kwargs.get(property_.name) is not None:
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

        # Reset cache
        cls.get_properties_raw.cache_clear()
        cls.get_property.cache_clear()

    @classmethod
    def register_property(cls, property_class, property_name):
        cls.getters_map[Properties(property_name)] = property_class.get
        cls.setters_map[Properties(property_name)] = property_class.set


class MetaProperty(type):
    def __new__(mcs, name, bases, attrs, **kwargs):
        property_name = attrs.get("property_name")
        if not property_name and "Base" not in name:
            raise ValueError("Must set property name")

        cls = super().__new__(mcs, name, bases, attrs)
        if "Base" not in name:
            PropertiesManager.register_property(cls, property_name)

        return cls


class BaseProperty(metaclass=MetaProperty):
    property_name = None
    str_to_value = lambda x: str2bool(x, parser=False)
    value_to_str = bool2str

    @classmethod
    def get_pattern(cls):
        return re.compile(rf"({cls.property_name}=)(\w+)", re.IGNORECASE)

    @classmethod
    def get(cls):
        file_data = PropertiesManager.get_properties_raw()
        return cls.str_to_value(cls.get_pattern().search(file_data).group(2))

    @classmethod
    def set(cls, property_value):
        cls.check_same_property(property_value)
        file_data = PropertiesManager.get_properties_raw()
        sub = r"\g<1>" + cls.value_to_str(property_value)
        file_data = cls.get_pattern().sub(sub, file_data)
        PropertiesManager.write_properties_raw(file_data)

    @classmethod
    def check_same_property(cls, new_property):
        current_property = cls.get()
        if new_property == current_property:
            # TODO: log exception?
            raise InvalidServerStateError(
                f"{cls.property_name} is already set to {current_property}"
            )


class AllowNetherProperty(BaseProperty):
    property_name = "allow-nether"


class BroadcastRconToOps(BaseProperty):
    property_name = "broadcast-rcon-to-ops"


class DifficultyProperty(BaseProperty):
    property_name = "difficulty"

    @classmethod
    def value_to_str(cls, difficulty: str) -> str:
        return difficulty

    @classmethod
    def str_to_value(cls, string: str) -> str:
        if string not in ["peaceful", "easy", "normal", "hard"]:
            raise ValueError(f"Invalid difficulty: {string!r}")
        return string


class EnableRconProperty(BaseProperty):
    property_name = "enable-rcon"


class EnableStatusProperty(BaseProperty):
    property_name = "enable-status"


class MaxPlayersProperty(BaseProperty):
    property_name = "max-players"
    value_to_str = str
    str_to_value = int


class OnlineModeProperty(BaseProperty):
    property_name = "online-mode"


class RconPassword(BaseProperty):
    property_name = "rcon.password"
    value_to_str = str
    str_to_value = str


class RconPort(BaseProperty):
    property_name = "rcon.port"
    value_to_str = str
    str_to_value = int


class WhitelistProperty(BaseProperty):
    property_name = "whitelist"
    pattern_1 = re.compile(r"(enforce-whitelist=)(\w+)", re.IGNORECASE)
    pattern_2 = re.compile(r"(white-list=)(\w+)", re.IGNORECASE)

    @classmethod
    def get(cls) -> bool:
        file_data = PropertiesManager.get_properties_raw()
        state1 = str2bool(cls.pattern_1.search(file_data).group(2), parser=False)
        state2 = str2bool(cls.pattern_2.search(file_data).group(2), parser=False)

        if state1 != state2:
            # TODO: improve exception name and log exception
            msg = "Properties white-list (%s) and enforce-whitelist (%s) can't be different"
            raise Exception(msg)
        return state1

    @classmethod
    def set(cls, whl_state: bool):
        cls.check_same_property(whl_state)

        file_data = PropertiesManager.get_properties_raw()
        file_data = cls.pattern_1.sub(r"\1" + bool2str(whl_state), file_data)
        file_data = cls.pattern_2.sub(r"\1" + bool2str(whl_state), file_data)
        PropertiesManager.write_properties_raw(file_data)


@lru_cache(maxsize=10)
def get_server_mode() -> bool:
    """Returns the current server mode.

    Returns:
        bool: current server mode.
    """

    return PropertiesManager.get_property(Properties.online_mode)


def set_server_mode(online_mode: bool):
    return PropertiesManager.set_property(online_mode=online_mode)


@lru_cache(maxsize=10)
def get_whitelist_state() -> bool:
    return PropertiesManager.get_property(Properties.whitelist)


def set_whitelist_state(whitelist_state: bool):
    return PropertiesManager.set_property(whitelist=whitelist_state)
