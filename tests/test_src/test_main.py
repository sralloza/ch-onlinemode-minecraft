import shlex
from collections import namedtuple
from unittest import mock

import pytest

from server_manager.main import Parser, main


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
            assert Parser.parser.prog == "server-manager"

    def test_online_mode_ok_arg(self):
        result = self.set_args("online-mode true")
        assert result["command"] == "online-mode"
        assert result["online-mode"] is True

        result = self.set_args("online-mode false")
        assert result["command"] == "online-mode"
        assert result["online-mode"] is False

    def test_online_mode_ok_no_arg(self):
        result = self.set_args("online-mode")
        assert result["command"] == "online-mode"
        assert result["online-mode"] is None

    def test_online_mode_fail_typerror(self):
        with pytest.raises(SystemExit, match="2"):
            self.set_args("online-mode invalid")

    def test_list(self):
        result = self.set_args("list")
        assert result["command"] == "list"

    def test_debug_files(self):
        result = self.set_args("debug-files")
        assert result["command"] == "debug-files"

    def test_data(self):
        result = self.set_args("data")
        assert result["command"] == "data"

    def test_whitelist(self):
        result = self.set_args("whitelist")
        assert result["command"] == "whitelist"

    def test_no_command(self):
        result = self.set_args("")
        assert result["command"] is None


@mock.patch("argparse.ArgumentParser.parse_args")
def test_parser_error(parse_args_m, capsys):
    Parser.parse_args()
    parse_args_m.assert_called_once_with()

    with pytest.raises(SystemExit, match="2"):
        Parser.error("Custom error given to parser")

    captured = capsys.readouterr()
    assert "Custom error given to parser" in captured.err
    assert "server-manager" in captured.err
    assert captured.out == ""


class TestMain:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.parse_args_m = mock.patch("server_manager.main.Parser.parse_args").start()
        self.set_mode_m = mock.patch("server_manager.main.set_mode").start()
        self.gpd_m = mock.patch("server_manager.main.get_players_data").start()
        self.player_gen_m = mock.patch("server_manager.main.Player.generate").start()
        self.get_mode_m = mock.patch("server_manager.main.get_mode").start()
        self._memory_m = mock.patch("server_manager.main.File.memory").start()
        self.memory_m = self._memory_m.__getitem__
        self.update_wl_m = mock.patch("server_manager.main.update_whitelist").start()

        yield

        mock.patch.stopall()

    def set_args(self, args):
        self.parse_args_m.return_value = args

    def test_online_mode(self, capsys):
        self.set_args({"command": "online-mode", "online-mode": "<om>"})

        main()

        self.parse_args_m.assert_called_once_with()
        self.set_mode_m.assert_called_once_with(mode="<om>")
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == "Set online-mode to <om>\n"
        assert result.err == ""

    def test_data(self, capsys):
        self.set_args({"command": "data"})
        self.gpd_m.return_value = ["p1", "p2", "p3"]

        main()

        self.parse_args_m.assert_called_once_with()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_called_once_with()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == " - p1\n - p2\n - p3\n"
        assert result.err == ""

    def test_list(self, capsys):
        self.set_args({"command": "list"})
        Player = namedtuple("Player", "username uuid")
        self.player_gen_m.return_value = [
            Player("player one", "uuid-1"),
            Player("p2", "id-2"),
            Player("this is player 3", "333-333-333"),
        ]
        self.get_mode_m.side_effect = [True, False, True]

        main()

        self.parse_args_m.assert_called_once_with()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_called_once_with()
        self.get_mode_m.assert_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()

        result = capsys.readouterr()
        expected = (
            " - player one       - online  -      uuid-1\n"
            " - p2               - offline -        id-2\n"
            " - this is player 3 - online  - 333-333-333\n"
        )
        assert result.out == expected
        assert result.err == ""

    def test_debug_files(self, capsys):
        self.set_args({"command": "debug-files"})
        memory = {"a": ["a1"], "b": ["b1", "b2"], "c": ["c1", "c2", "c3"]}
        self.memory_m.side_effect = lambda x: memory[x]
        self._memory_m.__iter__.side_effect = lambda: iter(memory)

        main()

        self.parse_args_m.assert_called_once_with()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_called_once_with()
        self.get_mode_m.assert_not_called()
        self.memory_m.assert_called()
        self.update_wl_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == "a1\nb1\nb2\nc1\nc2\nc3\n"
        assert result.err == ""

    def test_whitelist(self, capsys):
        self.set_args({"command": "whitelist"})

        main()

        self.parse_args_m.assert_called_once_with()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_called_once_with()

        result = capsys.readouterr()
        assert result.out == ""
        assert result.err == ""

    def test_no_command(self, capsys):
        self.set_args({"command": None})

        with pytest.raises(SystemExit, match="2"):
            main()

        self.parse_args_m.assert_called_once_with()
        self.set_mode_m.assert_not_called()
        self.gpd_m.assert_not_called()
        self.player_gen_m.assert_not_called()
        self.get_mode_m.assert_not_called()
        self.memory_m.assert_not_called()
        self.update_wl_m.assert_not_called()

        result = capsys.readouterr()
        assert result.out == ""
        assert "Must select command" in result.err
