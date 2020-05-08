from .dataframe import get_mode, get_username, get_uuid
from .player import Player


def set_mode(path, mode):
    players = Player.generate("D:/Sistema/Desktop/lia-backup/LIA 2020")
    for player in players:
        current_mode = get_mode(player.uuid)

        if current_mode == mode:
            username = get_username(player.uuid)
            msg = (
                f"While setting mode {mode}, found player "
                f"with same mode when it should have mode={not mode}: {username!r}\n"
                f" {player.to_extended_repr()}"
            )

            raise Exception(msg)

        new_uuid = get_uuid(get_username(player.uuid), mode)
        player.change_uuid(new_uuid)


if __name__ == "__main__":
    players = set_mode("D:/Sistema/Desktop/lia-backup/LIA 2020", False)
