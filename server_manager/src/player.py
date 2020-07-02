"""Contains player related code."""

from collections import defaultdict
import logging
from pathlib import Path
from typing import List

from .dataframe import get_mode, get_username
from .exceptions import InvalidPlayerError
from .files import AdvancementsFile, File, PlayerDataFile, StatsFile
from .properties_manager import get_server_path


class Player:
    """Represents a player."""

    required_files = ["player_data_file", "stats_file", "advancements_file"]
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, uuid: str, *files):
        """Represents a player.

        Args:
            uuid (str): uuid of the player.
            *files: must be three instances of File, one for each subtype
                (PlayerDataFile, StatsFile, AdvacementsFile).

        Raises:
            TypeError: if one file is of an invalid file.
            InvalidPlayerError: if not all of the required files are passed.
        """

        self.uuid = uuid
        self.username = get_username(self.uuid)
        self.online = get_mode(self.uuid)

        for file in files:
            if isinstance(file, PlayerDataFile):
                self.player_data_file = file
            elif isinstance(file, StatsFile):
                self.stats_file = file
            elif isinstance(file, AdvancementsFile):
                self.advancements_file = file
            else:
                raise TypeError(f"files can't be {type(type).__name__!r}")

        for file in self.required_files:
            if not hasattr(self, file):
                file = file.replace("file", "").replace("_", " ")
                raise InvalidPlayerError(
                    f"Can't create Player {self.username!r} without {file}"
                )

    def __repr__(self):
        return f"Player({self.username}|{self.online} - {self.uuid})"

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_extended_repr(self) -> str:
        """Returns the extended representation string of the Player.

        Returns:
            str: extended repr.
        """

        return (
            f"Player({self.username}|{self.online} - {self.uuid}, "
            f"player_data_file={self.player_data_file.as_posix()!r}, "
            f"stats_file={self.stats_file.as_posix()!r}, "
            f"advancements_file={self.advancements_file.as_posix()!r})"
        )

    def change_uuid(self, new_uuid: str):
        """Changes the uuid of the player.

        Args:
            new_uuid (str): new uuid.
        """

        self.logger.debug("Changing uuid of user %s to %s", self.username, new_uuid)
        self.player_data_file.change_uuid(new_uuid)
        self.stats_file.change_uuid(new_uuid)
        self.advancements_file.change_uuid(new_uuid)

    @classmethod
    def generate(cls, root_path: Path = None) -> List["Player"]:
        """Scans the root path and returns the list of players found in the
        minecraft server files.

        Returns:
            List[Player]: list of players found.
        """

        if not root_path:
            root_path = get_server_path()

        cls.logger.debug("Grouping files by username")
        File.gen_files(root_path)

        files_map = defaultdict(list)

        for file_group in File.memory.values():
            for file in file_group:
                # match must be always true, trust File.memory
                match = File.uuid_pattern.search(file.path.as_posix())
                uuid = match.group()
                files_map[uuid].append(file)
        players = [Player(uuid, *files_map[uuid]) for uuid in files_map]
        players.sort(key=lambda x: x.username)
        cls.logger.debug("Files grouped by username")

        return players
