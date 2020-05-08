import gzip
import os
import re
from collections import namedtuple
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import nbtlib

from players_uuids import uuid_to_player

ROOT_BACKUPS = Path("D:/Sistema/Desktop/lia-backup")
PENDRIVE_PATH = Path("E:/LIA 2020")
PlayerResult = namedtuple("PlayerResult", "player inventory ender")


def get_last_lia_zip_filename():
    paths = [
        x.as_posix() for x in ROOT_BACKUPS.iterdir() if x.as_posix().endswith(".zip")
    ]
    return Path(max(paths))


def get_zipfile():
    general_zip = get_last_lia_zip_filename()
    print("using path %r" % general_zip.as_posix())
    return ZipFile(general_zip.as_posix())


def get_players_uuids_pendrive():
    uuids = {}
    for root, dirs, files in os.walk(PENDRIVE_PATH):
        for file in files:
            file = Path(root) / file
            if "world/playerdata" in file.as_posix():
                match = re.search(r"playerdata\/([\w-]+)\.dat", file.as_posix())
                if not match:
                    continue
                uuid = match.group(1)
                uuids[uuid] = file.read_bytes()
    return uuids


def get_players_uuids_last_backup():
    uuids = {}
    with get_zipfile() as myzip:
        names = myzip.namelist()
        for name in names:
            if "world/playerdata" in name:
                match = re.search(r"playerdata\/([\w-]+)\.dat", name)
                if not match:
                    continue
                uuid = match.group(1)
                uuids[uuid] = myzip.read(name)

        return uuids


def read_nbt_data(nbt_bytes):
    """Parses nbt data (as bytes) and returns a dict. It is designed to parse
    data from players in a minecraft server (<player-uuid>.dat).

    Args:
        nbt_bytes (bytes): nbt data as bytes.

    Returns:
        dict: nbt data as a dictionary.
    """
    buff = BytesIO(nbt_bytes)
    buff = gzip.GzipFile(fileobj=buff)

    return dict(nbtlib.File.from_buffer(buff, "big"))[""]


def find_non_empty_players(source="backups", only_offline=True):
    assert source in ["backups", "pendrive"]

    if source == "backups":
        data = get_players_uuids_last_backup()
    elif source == "pendrive":
        data = get_players_uuids_pendrive()

    players = []

    for uuid in data:
        nbt = read_nbt_data(data[uuid])

        inventory = nbt["Inventory"]
        ender = nbt["EnderItems"]

        player = uuid_to_player(uuid)

        if not inventory and not ender:
            continue

        if player.online and only_offline:
            continue

        players.append(PlayerResult(player, bool(inventory), bool(ender)))
    return players


if __name__ == "__main__":
    print(find_non_empty_players("pendrive"))
