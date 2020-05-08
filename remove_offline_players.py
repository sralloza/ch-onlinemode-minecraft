import os
from pathlib import Path

from main import PENDRIVE_PATH, find_non_empty_players
from players_uuids import df, uuid_to_player


def remove_offline_players(force=False):
    filled_players = find_non_empty_players("pendrive")
    if filled_players and not force:
        for player in filled_players:
            print(player)
        print("ERROR")
        return

    offline_players = df[df.online == False]

    search = set()
    for uuid in offline_players.index:
        for root, dirs, files in os.walk(PENDRIVE_PATH):
            for file in files:
                file = Path(root) / file
                if uuid in file.as_posix():
                    file.unlink()
                    print(file)
                    search.add(uuid)

    for uuid in search:
        print(uuid_to_player(uuid))


if __name__ == "__main__":
    remove_offline_players(force=True)
