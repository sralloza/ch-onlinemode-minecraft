from collections import defaultdict
from itertools import groupby
from pathlib import Path
from typing import List

from src.dataframe import get_mode, get_username

from .files import AdvancementsFile, File, PlayerDataFile, StatsFile


class Player:
    player_data_file: File
    stats_file: File
    advancements_file: File
    uuid: str
    username: str

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

    def to_extended_repr(self):
        return (
            f"Player({self.username} - {self.uuid!r}, "
            f"player_data_file={self.player_data_file.as_posix()!r}, "
            f"stats_file={self.stats_file.as_posix()!r}, "
            f"advancements_file={self.advancements_file.as_posix()!r})"
        )

    def change_uuid(self, new_uuid: str):
        self.player_data_file.change_uuid(new_uuid)
        self.stats_file.change_uuid(new_uuid)
        self.advancements_file.change_uuid(new_uuid)

    @classmethod
    def generate(cls, root_path: Path, check=True) -> List["Player"]:
        File.gen_files(root_path)

        files_map = defaultdict(list)

        for file_group in File.memory.values():
            for file in file_group:
                match = File.uuid_pattern.search(file.path.as_posix())
                if not match:
                    raise ValueError(
                        f"{file} is not a valid file (it doesn't contain a UUID"
                    )

                uuid = match.group()
                files_map[uuid].append(file)
        players = [Player(uuid, *files_map[uuid]) for uuid in files_map]
        players.sort(key=lambda x: x.username)

        if not check:
            return players

        # Checking that players can only have one online mode
        invalids = {}
        for username, players_ in groupby(players, lambda x: x.username):
            nplayers = len(players_)
            if nplayers > 1:
                invalids[username] = nplayers

        if invalids:
            raise ValueError(
                f"These players have more than one online mode: {invalids}"
            )

        return players
