from src.properties_manager import get_server_path

from .dataframe import get_mode, get_username, get_uuid
from .player import Player
from .properties_manager import get_server_mode, set_server_mode


def set_mode(mode=None):
    server_path = get_server_path()
    current_servermode = get_server_mode()


    players = Player.generate(server_path)
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

    set_server_mode(mode)
