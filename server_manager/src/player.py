import logging
from collections import defaultdict
from pathlib import Path
from typing import List

from .dataframe import get_mode, get_username
from .properties_manager import get_server_path

from .files import AdvancementsFile, File, PlayerDataFile, StatsFile


class Player:
    player_data_file: File
    stats_file: File
    advancements_file: File
    uuid: str
    username: str
    logger: logging.Logger = logging.getLogger(__name__)

    def __init__(self, uuid, *files):
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

        assert self.player_data_file
        assert self.stats_file
        assert self.advancements_file

    def __repr__(self):
        return f"Player({self.username}|{self.online} - {self.uuid!r})"

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_extended_repr(self):
        return (
            f"Player({self.username} - {self.uuid!r}, "
            f"player_data_file={self.player_data_file.as_posix()!r}, "
            f"stats_file={self.stats_file.as_posix()!r}, "
            f"advancements_file={self.advancements_file.as_posix()!r})"
        )

    def change_uuid(self, new_uuid: str):
        self.logger.debug("Changing uuid of user %s to %s", self.username, new_uuid)
        self.player_data_file.change_uuid(new_uuid)
        self.stats_file.change_uuid(new_uuid)
        self.advancements_file.change_uuid(new_uuid)

    @classmethod
    def generate(cls, root_path: Path = None) -> List["Player"]:
        # FIXME: right now, both Player.generate and set_mode (who calls the first one) generate
        # the root_path. Player.generate needs it, but set_mode just logs it. Think this.
        if not root_path:
            root_path = get_server_path()

        cls.logger.debug("Grouping files by username")
        File.gen_files(root_path)

        files_map = defaultdict(list)

        for file_group in File.memory.values():
            for file in file_group:
                match = File.uuid_pattern.search(file.path.as_posix())
                if not match:
                    cls.logger.critical(
                        "%s is not a valid file (it doesn't contain a UUID)", file
                    )
                    raise ValueError(
                        f"{file} is not a valid file (it doesn't contain a UUID)"
                    )

                uuid = match.group()
                files_map[uuid].append(file)
        players = [Player(uuid, *files_map[uuid]) for uuid in files_map]
        players.sort(key=lambda x: x.username)
        cls.logger.debug("Files grouped by username")

        return players
