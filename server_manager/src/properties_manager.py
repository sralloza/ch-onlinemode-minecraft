"""Manages the properties of the minecraft server (`server.properties`)."""

from enum import Enum
from functools import lru_cache
import logging
from pathlib import Path
import re
import sys
from typing import Any, Union

from colorama import Fore

from .exceptions import PropertyError
from .paths import get_server_path
from .utils import Validators
from .utils import bool2str, str2bool

PropertiesLike = Union["Properties", str]
logger = logging.getLogger(__name__)


class Properties(Enum):
    """List of properties managed by PropertiesManager."""

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

    @classmethod
    def get(cls, value: PropertiesLike) -> "Properties":
        """Properties validator.

        Args:
            value (PropertiesLike): input value.

        Returns:
            Properties: properties.
        """

        if isinstance(value, Properties):
            return value

        try:
            return cls[value]
        except KeyError:
            return cls(value)


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
    """Manages settings of file `server.properties`."""

    getters_map = {}
    setters_map = {}

    @classmethod
    @lru_cache(maxsize=10)
    def get_property(cls, request: PropertiesLike) -> Any:
        """Returs a property's current value.

        Args:
            request (PropertiesLike): property to find.

        Returns:
            Any: the property's current value.
        """

        request = Properties.get(request)
        return cls.getters_map[request]()

    @classmethod
    def set_property(cls, **kwargs: Any):
        """Sets a property's value.

        Args:
            kwargs (Any): just one property to set, and its new value.

        Raises:
            ValueError: if no valid property names are passed in kwargs.
        """

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
    def register_property(cls, property_class: "BaseProperty", property_name: str):
        """Registers a property (setter, getter and name).

        Args:
            property_class (BaseProperty): property class.
            property_name (str): property name.
        """

        cls.getters_map[Properties(property_name)] = property_class.get
        cls.setters_map[Properties(property_name)] = property_class.set


class MetaProperty(type):
    """Metaclass to automatically register new properties."""

    # pylint: disable=missing-param-doc,missing-type-doc
    def __new__(cls, name, bases, attrs):
        property_name = attrs.get("property_name")
        if not property_name and "Base" not in name:
            raise ValueError("Must set property name")

        new_cls = super().__new__(cls, name, bases, attrs)
        if "Base" not in name:
            PropertiesManager.register_property(new_cls, property_name)

        return new_cls


class BaseProperty(metaclass=MetaProperty):
    """Base class for Properties."""

    property_name = None
    str_to_value = lambda x: str2bool(x, parser=False)
    value_to_str = bool2str
    validator = Validators.bool

    @classmethod
    def get_pattern(cls):
        """Returns the regex pattern to parse the `server.properties` file."""

        return re.compile(rf"({cls.property_name}=)(\w*)", re.IGNORECASE)

    @classmethod
    def get(cls):
        """Returns the property's current value."""

        file_data = PropertiesManager.get_properties_raw()
        return cls.str_to_value(cls.get_pattern().search(file_data).group(2))

    @classmethod
    def validate(cls, value: Any):
        """Validates a value.

        Args:
            value (Any): input value.

        Raises:
            ValueError: if the value is not valid.
        """

        if cls.validator(value) is False:
            msg = f"Validator 'Validators.{cls.validator.__name__}' rejected value {value!r}"
            raise ValueError(msg)

    @classmethod
    def set(cls, property_value: Any):
        """Sets a new property value.

        Args:
            property_value (Any): property value to set.
        """

        cls.validate(property_value)
        cls.check_same_property(property_value)

        file_data = PropertiesManager.get_properties_raw()
        sub = r"\g<1>" + cls.value_to_str(property_value)
        file_data = cls.get_pattern().sub(sub, file_data)
        PropertiesManager.write_properties_raw(file_data)

    @classmethod
    def check_same_property(cls, new_property: Any):
        """Checks if the property's current value is the same as `new_property`.

        Args:
            new_property (Any): new property value.

        Raises:
            PropertyError: if the property's current value is the
                same as `new_property`.
        """

        current_property = cls.get()
        if new_property == current_property:
            logger.critical(
                "Tried to set %s to %r (same value)", cls.property_name, new_property
            )
            raise PropertyError(
                f"{cls.property_name} is already set to {current_property}"
            )


class AllowNetherProperty(BaseProperty):
    """Manages property 'allow-nether'."""

    property_name = "allow-nether"


class BroadcastRconToOpsProperty(BaseProperty):
    """Manages property 'broadcast-rcon-to-ops'."""

    property_name = "broadcast-rcon-to-ops"


class DifficultyProperty(BaseProperty):
    """Manages property 'difficulty'."""

    property_name = "difficulty"
    value_to_str = str
    validator = Validators.difficulty

    @classmethod
    def str_to_value(cls, string: str) -> str:
        """Returns the string representation of a difficulty.

        Args:
            string (str): input difficulty.

        Raises:
            ValueError: if `string` is not a valid difficulty.

        Returns:
            str: string representation of a difficulty.
        """

        if not cls.validator(string):
            raise ValueError(f"Invalid difficulty: {string!r}")
        return string


class EnableRconProperty(BaseProperty):
    """Manges property 'enable-rcon'."""

    property_name = "enable-rcon"


class EnableStatusProperty(BaseProperty):
    """"Manages property 'enable-status'."""

    property_name = "enable-status"


class MaxPlayersProperty(BaseProperty):
    """Manages property 'max-players'."""

    property_name = "max-players"
    value_to_str = str
    str_to_value = int
    validator = Validators.int


class OnlineModeProperty(BaseProperty):
    """Manages property 'online-mode'."""

    property_name = "online-mode"


class RconPasswordProperty(BaseProperty):
    """Manages property 'rcon.password'."""

    property_name = "rcon.password"
    value_to_str = str
    str_to_value = str
    validator = Validators.str


class RconPortProperty(BaseProperty):
    """Manages property 'rcon.port'."""

    property_name = "rcon.port"
    value_to_str = str
    str_to_value = int
    validator = Validators.int


class WhitelistProperty(BaseProperty):
    """Manages properties 'white-list' and 'enforce-whitelist'."""

    property_name = "whitelist"
    pattern_1 = re.compile(r"(white-list=)(\w+)", re.IGNORECASE)
    pattern_2 = re.compile(r"(enforce-whitelist=)(\w+)", re.IGNORECASE)

    @classmethod
    def get(cls) -> bool:
        """Returns the current whitelist status.

        Raises:
            PropertyError: if 'white-list' and 'enforce-whitelist' are unsynced.

        Returns:
            bool: current whitelist status.
        """

        file_data = PropertiesManager.get_properties_raw()
        state1 = str2bool(cls.pattern_1.search(file_data).group(2), parser=False)
        state2 = str2bool(cls.pattern_2.search(file_data).group(2), parser=False)

        if state1 != state2:
            msg = "Properties white-list (%s) and enforce-whitelist (%s) can't be different"
            logger.critical(msg, state1, state2)
            raise PropertyError(msg % (state1, state2))
        return state1

    @classmethod
    def set(cls, whl_state: bool):  # pylint: disable=arguments-differ
        """Sets a new whitelist status.

        Args:
            whl_state (bool): new whitelist status.
        """

        cls.validate(whl_state)
        cls.check_same_property(whl_state)

        file_data = PropertiesManager.get_properties_raw()
        file_data = cls.pattern_1.sub(r"\1" + bool2str(whl_state), file_data)
        file_data = cls.pattern_2.sub(r"\1" + bool2str(whl_state), file_data)
        PropertiesManager.write_properties_raw(file_data)
