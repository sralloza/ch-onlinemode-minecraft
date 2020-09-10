from unittest import mock

from click.testing import CliRunner
import pytest

from server_manager import __version__
from server_manager.main import main, setup_logging
from server_manager.src.exceptions import CheckError


@mock.patch("logging.FileHandler")
@mock.patch("server_manager.main.get_backups_folder")
@mock.patch("logging.basicConfig")
def test_setup_logging(log_config_m, gsp_m, file_h_m):
    fmt = "[%(asctime)s] %(levelname)s - %(name)s:%(lineno)s - %(message)s"
    filename = gsp_m.return_value.joinpath.return_value

    setup_logging()

    gsp_m.assert_called_once_with()
    gsp_m.return_value.joinpath.assert_called_once_with("lia-manager.log")

    file_h_m.assert_called_once_with(filename, "at", "utf8")

    log_config_m.assert_called_once_with(
        level=10, format=fmt, handlers=[file_h_m.return_value]
    )
    setup_logging_m.call = False


@pytest.fixture(autouse=True)
def setup_logging_m():
    setup_logging_m.call = True
    logging_m = mock.patch("server_manager.main.setup_logging").start()
    yield
    if setup_logging_m.call:
        logging_m.assert_called_once_with()
    else:
        logging_m.assert_not_called()


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
    assert "lia" in result.output
    assert "version" in result.output
    setup_logging_m.call = False


@mock.patch("server_manager.main.create_backup")
def test_backup(backup_m):
    runner = CliRunner()
    result = runner.invoke(main, ["backup"])
    assert result.exit_code == 0
    assert result.output == ""
    backup_m.assert_called_once_with()


@pytest.mark.parametrize("mode", [True, False])
@mock.patch("server_manager.main.PropertiesManager.get_property")
def test_get_online_mode(get_prop_m, mode):
    get_prop_m.return_value = mode
    runner = CliRunner()
    result = runner.invoke(main, ["online-mode", "get"])

    msg = f"server is currently running as {mode}\n"
    assert result.exit_code == 0
    assert result.output == msg
    get_prop_m.assert_called_once_with("online_mode")


@pytest.mark.parametrize("is_ok", [True, False])
@mock.patch("server_manager.main.set_mode")
def test_set_online_mode(set_mode_m, is_ok):
    if not is_ok:
        set_mode_m.side_effect = CheckError("a", "b", "c", 25)

    runner = CliRunner()
    result = runner.invoke(main, ["online-mode", "set", "true"])

    if is_ok:
        assert result.exit_code == 0
        assert result.output == "Set online-mode to True\n"
    else:
        assert result.exit_code == 1
        assert result.output == "Error: CheckError: a, b, c, 25\n"


@pytest.mark.parametrize("empty", [True, False])
@mock.patch("server_manager.main.get_players_data")
def test_get_players_data(gpd_m, empty):
    if empty:
        gpd_m.return_value = []
    else:
        gpd_m.return_value = ["p1", "p2", "p3"]

    runner = CliRunner()
    result = runner.invoke(main, ["players", "list-csv"])

    gpd_m.assert_called_once_with()

    assert result.exit_code == 0
    if empty:
        assert result.output == "<no players found in the csv>\n"
    else:
        assert result.output == " - p1\n - p2\n - p3\n"


@pytest.mark.parametrize("empty", [True, False])
@mock.patch("server_manager.main.get_mode")
@mock.patch("server_manager.main.Player.generate")
def test_list_players(player_gen_m, get_mode_m, empty):
    class Player:
        def __init__(self, username: str, uuid: str):
            self.username = username
            self.uuid = uuid

        def get_inventory(self):
            return self.username

        def get_ender_chest(self):
            return self.uuid

    if empty:
        player_gen_m.return_value = []
    else:
        player_gen_m.return_value = [
            Player("player one", "uuid-1"),
            Player("p2", "id-2"),
            Player("this is player 3", "333-333-333"),
        ]
        get_mode_m.side_effect = [True, False, True]

    runner = CliRunner()
    result = runner.invoke(main, ["players", "list-server"])

    player_gen_m.assert_called_once_with()

    if empty:
        get_mode_m.assert_not_called()
    else:
        get_mode_m.assert_called()

    if empty:
        expected = "<no players found in the server archives>\n"
    else:
        expected = (
            " | username         -  mode   -    uuid     - inventory - ender-chest |\n"
            " | player one       - online  -   uuid-1    -    10     -      6      |\n"
            " | p2               - offline -    id-2     -     2     -      4      |\n"
            " | this is player 3 - online  - 333-333-333 -    16     -     11      |\n"
        )

    assert result.exit_code == 0
    assert result.output == expected


@pytest.mark.parametrize("force", [True, False])
@mock.patch("server_manager.main.remove_players_safely")
@mock.patch("server_manager.main.Player.generate")
def test_reset_players(player_gen_m, rps_m, force):
    args = ["players", "reset"]
    if force:
        args.append("--force")

    runner = CliRunner()
    result = runner.invoke(main, args)

    player_gen_m.assert_called_once_with()
    rps_m.assert_called_once_with(player_gen_m.return_value, force=force)

    assert result.exit_code == 0
    assert result.output == ""


@pytest.mark.parametrize("fail", [False, True])
@mock.patch("server_manager.main.Player.generate")
def test_show_player(player_gen_m, fail):
    jeb = mock.MagicMock(username="Jeb")
    notch = mock.MagicMock(username="Notch")
    notch.get_detailed_inventory.return_value = "<inv>"
    notch.get_detailed_ender_chest.return_value = "<end-chest>"
    players = [jeb]

    if not fail:
        players.append(notch)
    player_gen_m.return_value = players

    runner = CliRunner()
    result = runner.invoke(main, ["players", "show", "notch"])

    player_gen_m.assert_called_once_with()

    if not fail:
        out = "Inventory:\n<inv>\n\nEnder chest:\n<end-chest>\n"
        assert result.exit_code == 0
        assert result.output == out

        notch.get_detailed_inventory.assert_called_once_with()
        notch.get_detailed_ender_chest.assert_called_once_with()

    else:
        out = "Error: No player named 'notch'\n"
        assert result.exit_code == 1
        assert result.output == out

        notch.get_detailed_inventory.assert_not_called()
        notch.get_detailed_ender_chest.assert_not_called()

    jeb.get_detailed_inventory.assert_not_called()
    jeb.get_detailed_ender_chest.assert_not_called()


@mock.patch("server_manager.main.File.gen_files")
@mock.patch("server_manager.main.get_server_path")
@mock.patch("server_manager.main.File.memory")
def test_print_files(memory_m, gsp_m, gen_files_m):
    memory = {"a": ["a1"], "b": ["b1", "b2"], "c": ["c1", "c2", "c3"]}
    memory_m.__getitem__.side_effect = lambda x: memory[x]
    memory_m.__iter__.side_effect = lambda: iter(memory)

    runner = CliRunner()
    result = runner.invoke(main, ["debug", "files"])

    gsp_m.assert_called_once_with()
    gen_files_m.assert_called_once_with(gsp_m.return_value)
    memory_m.__getitem__.assert_called()

    assert result.exit_code == 0
    assert result.output == "a1\nb1\nb2\nc1\nc2\nc3\n"


@mock.patch("server_manager.main.update_whitelist")
def test_update_whitelist(update_wl_m):
    runner = CliRunner()
    result = runner.invoke(main, ["update-whitelist"])

    update_wl_m.assert_called_once_with()

    assert result.exit_code == 0
    assert result.output == ""
