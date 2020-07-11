import shlex
from dataclasses import dataclass
from unittest import mock

import pytest
from server_manager.main import Commands, Parser, main, setup_logging


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


class TestParseArgs:
    @mock.patch("sys.argv")
    def set_args(self, string=None, sys_argv_m=None):
        real_args = ["test.py"] + shlex.split(string)
        sys_argv_m.__getitem__.side_effect = lambda s: real_args[s]

        try:
            args = Parser.parse_args()
            return args
        finally:
            sys_argv_m.__getitem__.assert_called_once_with(slice(1, None, None))
            assert Parser.parser.prog == "lia"

    def test_backup(self):
        result = self.set_args("backup")
        assert result["command"] == "backup"
        assert len(result) == 1

    def test_debug_files(self):
        result = self.set_args("debug-files")
        assert result["command"] == "debug-files"
        assert len(result) == 1

    def test_get_online_mode(self):
        result = self.set_args("get-online-mode")
        assert result["command"] == "get-online-mode"
        assert len(result) == 1

    def test_list_csv_players(self):
        result = self.set_args("list-csv-players")
        assert result["command"] == "list-csv-players"
        assert len(result) == 1

    def test_list_server_players(self):
        result = self.set_args("list-server-players")
        assert result["command"] == "list-server-players"
        assert len(result) == 1

    def test_reset_players_true(self):
        result = self.set_args("reset-players")
        assert result["command"] == "reset-players"
        assert result["force"] is False
        assert len(result) == 2

    def test_reset_playesr_with_force(self):
        result = self.set_args("reset-players --force")
        assert result["command"] == "reset-players"
        assert result["force"] is True
        assert len(result) == 2

    def test_set_online_mode_ok(self):
        result = self.set_args("set-online-mode true")
        assert result["command"] == "set-online-mode"
        assert result["online-mode"] is True
        assert len(result) == 2

        result = self.set_args("set-online-mode false")
        assert result["command"] == "set-online-mode"
        assert result["online-mode"] is False
        assert len(result) == 2

    def test_set_online_mode_fail_no_arg(self):
        with pytest.raises(SystemExit, match="2"):
            self.set_args("set-online-mode")

    def test_set_online_mode_fail_typerror(self):
        with pytest.raises(SystemExit, match="2"):
            self.set_args("set-online-mode invalid")

    def test_update_whitelist(self):
        result = self.set_args("update-whitelist")
        assert result["command"] == "update-whitelist"
        assert len(result) == 1

    def test_no_command(self):
        result = self.set_args("")
        assert result["command"] is None
        assert len(result) == 1


@mock.patch("server_manager.main.Parser.parser")
def test_print_help(parser_m, capsys):
    parser_m.print_help.return_value = "<parser-help>"
    Parser.print_help()

    result = capsys.readouterr()
    parser_m.print_help.assert_called_once_with()

    assert result.err == ""
    assert result.out == ""


@mock.patch("argparse.ArgumentParser.parse_args")
def test_parser_error(parse_args_m, capsys):
    Parser.parse_args()
    parse_args_m.assert_called_once_with()

    with pytest.raises(SystemExit, match="2"):
        Parser.error("Custom error given to parser")

    captured = capsys.readouterr()
    assert "Custom error given to parser" in captured.err
    assert "lia" in captured.err
    assert captured.out == ""


class TestMain:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.parse_args_m = mock.patch("server_manager.main.Parser.parse_args").start()
        self.logging_m = mock.patch("server_manager.main.setup_logging").start()
        self.commands_m = mock.patch("server_manager.main.Commands").start()
        self.parser_help_m = mock.patch("server_manager.main.Parser.print_help").start()

        self.commands = [
            "backup",
            "print_players_data",
            "print_files",
            "get_online_mode",
            "list_players",
            "reset_players",
            "set_online_mode",
            "update_whitelist",
        ]

        yield

        self.parse_args_m.assert_called_once_with()
        self.logging_m.assert_called_once_with()

        mock.patch.stopall()

    def set_args(self, args):
        self.parse_args_m.return_value = args

    def assert_only_call(self, only_called):
        for command in self.commands:
            if command == only_called:
                continue
            getattr(self.commands_m, command).assert_not_called()

    def test_backup(self):
        self.set_args({"command": "backup"})
        main()
        self.commands_m.backup.assert_called_once_with()
        self.assert_only_call("backup")

    def test_print_players_data(self):
        self.set_args({"command": "list-csv-players"})
        main()
        self.commands_m.print_players_data.assert_called_once_with()
        self.assert_only_call("print_players_data")

    def test_print_files(self):
        self.set_args({"command": "debug-files"})
        main()
        self.commands_m.print_files.assert_called_once_with()
        self.assert_only_call("print_files")

    def test_get_online_mode(self):
        self.set_args({"command": "get-online-mode"})
        main()
        self.commands_m.get_online_mode.assert_called_once_with()
        self.assert_only_call("get_online_mode")

    def test_list_players(self):
        self.set_args({"command": "list-server-players"})
        main()
        self.commands_m.list_players.assert_called_once_with()
        self.assert_only_call("list_players")

    def test_reset_players(self):
        self.set_args({"command": "reset-players", "force": "<force>"})
        main()
        self.commands_m.reset_players.assert_called_once_with("<force>")
        self.assert_only_call("reset_players")

    def test_set_online_mode(self):
        self.set_args({"command": "set-online-mode", "online-mode": "<om>"})
        main()
        self.commands_m.set_online_mode.assert_called_once_with("<om>")
        self.assert_only_call("set_online_mode")

    def test_update_whitelist(self):
        self.set_args({"command": "update-whitelist"})
        main()
        self.commands_m.update_whitelist.assert_called_once_with()
        self.assert_only_call("update_whitelist")

    def test_no_command(self):
        self.set_args({"command": None})

        main()
        self.assert_only_call("none")
        self.parser_help_m.assert_called_once_with()


class TestCommand:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.backup_m = mock.patch("server_manager.main.create_backup").start()
        self.gsv_m = mock.patch("server_manager.main.get_server_mode").start()
        self.set_mode_m = mock.patch("server_manager.main.set_mode").start()
        self.gpd_m = mock.patch("server_manager.main.get_players_data").start()
        self.player_gen_m = mock.patch("server_manager.main.Player.generate").start()
        self.get_mode_m = mock.patch("server_manager.main.get_mode").start()
        self.gsp_m = mock.patch("server_manager.main.get_server_path").start()
        self.gen_files_m = mock.patch("server_manager.main.File.gen_files").start()
        self._memory_m = mock.patch("server_manager.main.File.memory").start()
        self.memory_m = self._memory_m.__getitem__
        self.update_wl_m = mock.patch("server_manager.main.update_whitelist").start()
        self.rps_m = mock.patch("server_manager.main.remove_players_safely").start()

        yield

        mock.patch.stopall()

    def test_backup(self, capsys):
        Commands.backup()

        self.backup_m.assert_called_once_with()
        self.gsv_m.assert_not_called()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.gsp_m.assert_not_called()
        self.gen_files_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()
        self.rps_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == ""
        assert result.err == ""

    def test_get_online_mode(self, capsys):
        self.gsv_m.return_value = "<server-mode>"

        Commands.get_online_mode()

        self.backup_m.assert_not_called()
        self.gsv_m.assert_called_once_with()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.gsp_m.assert_not_called()
        self.gen_files_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()
        self.rps_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == "server is currently running as <server-mode>\n"
        assert result.err == ""

    def test_set_online_mode(self, capsys):
        Commands.set_online_mode("<om>")

        self.backup_m.assert_not_called()
        self.gsv_m.assert_not_called()
        self.set_mode_m.assert_called_once_with(new_mode="<om>")
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.gsp_m.assert_not_called()
        self.gen_files_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()
        self.rps_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == "Set online-mode to <om>\n"
        assert result.err == ""

    def test_print_players_data(self, capsys):
        self.gpd_m.return_value = ["p1", "p2", "p3"]

        Commands.print_players_data()

        self.backup_m.assert_not_called()
        self.gsv_m.assert_not_called()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_called_once_with()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.gsp_m.assert_not_called()
        self.gen_files_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()
        self.rps_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == " - p1\n - p2\n - p3\n"
        assert result.err == ""

    def test_list_players(self, capsys):
        @dataclass
        class Player:
            username: str
            uuid: str

            def get_inventory(self):
                return self.username

            def get_ender_chest(self):
                return self.uuid

        self.player_gen_m.return_value = [
            Player("player one", "uuid-1"),
            Player("p2", "id-2"),
            Player("this is player 3", "333-333-333"),
        ]
        self.get_mode_m.side_effect = [True, False, True]

        Commands.list_players()

        self.backup_m.assert_not_called()
        self.gsv_m.assert_not_called()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_called_once_with()
        self.get_mode_m.assert_called()
        self.gsp_m.assert_not_called()
        self.gen_files_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()
        self.rps_m.assert_not_called()

        result = capsys.readouterr()
        expected = (
            " | username         -  mode   -    uuid     - inventory - ender-chest |\n"
            " | player one       - online  -   uuid-1    -    10     -      6      |\n"
            " | p2               - offline -    id-2     -     2     -      4      |\n"
            " | this is player 3 - online  - 333-333-333 -    16     -     11      |\n"
        )
        assert result.out == expected
        assert result.err == ""

    def test_print_files(self, capsys):
        memory = {"a": ["a1"], "b": ["b1", "b2"], "c": ["c1", "c2", "c3"]}
        self.memory_m.side_effect = lambda x: memory[x]
        self._memory_m.__iter__.side_effect = lambda: iter(memory)

        Commands.print_files()

        self.backup_m.assert_not_called()
        self.gsv_m.assert_not_called()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.gsp_m.assert_called_once_with()
        self.gen_files_m.assert_called_once_with(self.gsp_m.return_value)
        self.memory_m.assert_called()
        self.update_wl_m.assert_not_called()
        self.rps_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == "a1\nb1\nb2\nc1\nc2\nc3\n"
        assert result.err == ""

    def test_update_whitelist(self, capsys):
        Commands.update_whitelist()

        self.backup_m.assert_not_called()
        self.gsv_m.assert_not_called()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.gsp_m.assert_not_called()
        self.gen_files_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_called_once_with()
        self.rps_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == ""
        assert result.err == ""

    def test_reset_players(self, capsys):
        Commands.reset_players("<force>")

        self.backup_m.assert_not_called()
        self.gsv_m.assert_not_called()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_called_once_with()
        self.get_mode_m.assert_not_called()
        self.gsp_m.assert_not_called()
        self.gen_files_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()
        self.rps_m.assert_called_once_with(
            self.player_gen_m.return_value, force="<force>"
        )

        result = capsys.readouterr()
        assert result.out == ""
        assert result.err == ""
