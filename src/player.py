from collections import defaultdict
from typing import List

from files import AdvancementsFile, File, PlayerDataFile, StatsFile


class Player:
    player_data_file: File
    stats_file: File
    advancements_file: File

    def __init__(self, uuid, *files):
        self.uuid = uuid

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
        self.player_data_file
        self.stats_file
        self.advancements_file
        return f"Player({self.uuid!r})"

    def to_extended_repr(self):
        return (
            f"Player({self.uuid!r}, "
            f"player_data_file={self.player_data_file.as_posix()!r}, "
            f"stats_file={self.stats_file.as_posix()!r}, "
            f"advancements_file={self.advancements_file.as_posix()!r})"
        )

    def change_uuid(self, new_uuid: str):
        self.player_data_file.change_uuid(new_uuid)
        self.stats_file.change_uuid(new_uuid)
        self.advancements_file.change_uuid(new_uuid)

    @classmethod
    def generate(cls, root_path: str):
        File.gen_files(root_path)

        files_map = defaultdict(lambda: list())

        for file_type, file_group in File.memory.items():
            for file in file_group:
                uuid = File.uuid_pattern.search(file.path.as_posix()).group()
                files_map[uuid].append(file)
        return [Player(uuid, *files_map[uuid]) for uuid in files_map]


if __name__ == "__main__":
    players = Player.generate("D:/Sistema/Desktop/lia-backup/LIA 2020")
    for player in players:
        print(player)
