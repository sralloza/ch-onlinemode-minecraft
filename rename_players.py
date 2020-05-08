import os
from pathlib import Path

from main import PENDRIVE_PATH, find_non_empty_players
from players_uuids import df, uuid_to_player


def ensure_mode(online):
    selected_mode_players = df[df.online == online]
    other_mode_players = df[df.online != online]

    selected_mode_players_found = set()
    other_mode_players_found = set()

    for uuid in selected_mode_players.index:
        for root, dirs, files in os.walk(PENDRIVE_PATH):
            for file in files:
                file = Path(root) / file
                if uuid in file.as_posix():
                    selected_mode_players_found.add(uuid)

    for uuid in other_mode_players.index:
        for root, dirs, files in os.walk(PENDRIVE_PATH):
            for file in files:
                file = Path(root) / file
                if uuid in file.as_posix():
                    other_mode_players_found.add(uuid)

    if other_mode_players_found:
        msg = (
            f"Invalid state: should be online={online} but this players"
            f" have online={not online}: {other_mode_players_found}"
        )
        raise ValueError(msg)



def set_onlinemode(online_mode):
    # ensure_mode(not online_mode)
    mode_players = df[df.online == online_mode]


    for uuid in mode_players.index:
        for root, dirs, files in os.walk(PENDRIVE_PATH):
            for file in files:
                file = Path(root) / file
                if uuid in file.as_posix():
                    username = df.loc[uuid, "username"]

                    other_mode_uuid = df.loc[(df.username == username) & (df.online == online_mode)].index[0]
                    print(uuid, other_mode_uuid, username)
                    # new_name = file.as_poxis().replace(uuid, )
                    print(file)


if __name__ == "__main__":
    set_onlinemode(True)
