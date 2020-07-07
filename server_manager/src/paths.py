"""Manages paths."""

from functools import lru_cache
import os
from pathlib import Path


DATA_PATH = Path(__file__).parent.joinpath("data/server-path.txt")
os.makedirs(DATA_PATH.parent, exist_ok=True)


@lru_cache(maxsize=10)
def get_server_path() -> Path:
    """Returns the server path. If it not stored, it will ask the user and then
    store the response after validating it.

    Returns:
        Path: root dir of the server (folder which contains `server.properties`).
    """

    if DATA_PATH.is_file():
        return Path(DATA_PATH.read_text().strip())

    from .properties_manager import validate_server_path

    server_path = input("Write the path of the server: ").strip()
    validate_server_path(server_path)

    DATA_PATH.write_text(Path(server_path).as_posix())
    return Path(server_path)
