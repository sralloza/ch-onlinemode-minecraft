from collections import namedtuple
from unittest import mock

import pytest

from server_manager.src.checks import (
    PlayerChecks,
    check_players,
    group_players,
    remove_players_safely,
)
from server_manager.src.exceptions import CheckError


class TestCheckPlayers:
    @pytest.fixture(autouse=True)
    def mocks(self, caplog):
        caplog.set_level(10, "server_manager.src.checks")
        self.caplog = caplog
        self.plchecks_m = mock.patch("server_manager.src.checks.PlayerChecks").start()
        yield
        records = caplog.get_records(when="call")
        assert records[0].message == "Checking players"
        assert len(records) == 2

        mock.patch.stopall()

    def test_check_players_ok(self):
        self.plchecks_m.check_online_mode.return_value = True
        self.plchecks_m.check_duplicates.return_value = True
        players = mock.MagicMock()

        result = check_players(players)
        assert result is True

        self.plchecks_m.check_online_mode.assert_called_once_with(players)
        self.plchecks_m.check_duplicates.assert_called_once_with(players)
        assert self.caplog.records[1].message == "Player checks passed"

    def test_check_players_online_fail(self):
        self.plchecks_m.check_online_mode.return_value = False
        self.plchecks_m.check_duplicates.return_value = True
        players = mock.MagicMock()

        with pytest.raises(CheckError, match="Online mode check failed"):
            check_players(players)

        self.plchecks_m.check_online_mode.assert_called_once_with(players)
        self.plchecks_m.check_duplicates.assert_not_called()
        assert self.caplog.records[1].message == "Online mode check failed"

    def test_check_players_duplicates_fail(self):
        self.plchecks_m.check_online_mode.return_value = True
        self.plchecks_m.check_duplicates.return_value = False
        players = mock.MagicMock()

        with pytest.raises(CheckError, match="Duplicates check failed"):
            check_players(players)

        self.plchecks_m.check_online_mode.assert_called_once_with(players)
        self.plchecks_m.check_duplicates.assert_called_once_with(players)
        assert self.caplog.records[1].message == "Duplicates check failed"


class TestPlayerChecks:
    @pytest.fixture(autouse=True)
    def mocks(self, caplog):
        root = "server_manager.src.checks."
        self.gsm_m = mock.patch(root + "get_server_mode").start()
        self.rps_m = mock.patch(root + "remove_players_safely").start()
        self.gp_m = mock.patch(root + "group_players").start()
        self.ply = namedtuple("Player", "id online")
        caplog.set_level(10, "server_manager.src.checks")

        yield
        mock.patch.stopall()

    @pytest.mark.parametrize("fail", [False, True])
    def test_check_online_mode(self, fail, caplog):
        players = [self.ply(i + 1, x) for i, x in enumerate([True, True, True])]
        extra = [self.ply(4, False), self.ply(5, False)]
        if fail:
            players += extra

        self.gsm_m.return_value = True

        result = PlayerChecks.check_online_mode(players)

        if fail:
            assert result == self.rps_m.return_value
            assert len(caplog.records) == 1
            assert caplog.records[0].levelname == "ERROR"
            msg = "These players are using a different mode than the server"
            assert msg in caplog.records[0].msg
            assert caplog.records[0].args == (False, True, extra)
        else:
            assert result is True
            assert len(caplog.records) == 0

    @pytest.mark.parametrize("fail", [False, True])
    def test_check_duplicates(self, fail, caplog):
        groups = [
            ("u1", [self.ply(1, True)]),
            ("u2", [self.ply(2, True)]),
            ("u3", [self.ply(3, True), self.ply(3, False)]),
            ("u4", [self.ply(3, True), self.ply(3, False)]),
        ]

        if not fail:
            del groups[-2][-1][-1]
            del groups[-1][-1][-1]

        self.gp_m.return_value = groups
        players = mock.MagicMock()

        result = PlayerChecks.check_duplicates(players)

        if fail:
            assert result == self.rps_m.return_value
            assert len(caplog.records) == 1
            assert caplog.records[0].levelname == "ERROR"
            msg = "Check result negative: these players have more than one online mode:"
            assert msg in caplog.records[0].msg
            assert caplog.records[0].args == ({"u3": 2, "u4": 2})
        else:
            assert result is True
            assert len(caplog.records) == 0


class TestGroupPlayers:
    @classmethod
    def setup_class(cls):
        cls.Player = namedtuple("Player", "uuid username")

        cls.players = [
            cls.Player(1, "u1"),
            cls.Player(1, "u2"),
            cls.Player(1, "u2"),
            cls.Player(1, "u3"),
            cls.Player(2, "u3"),
            cls.Player(2, "u3"),
            cls.Player(2, "u4"),
            cls.Player(3, "u4"),
            cls.Player(3, "u4"),
            cls.Player(4, "u4"),
        ]

    def test_normal_key(self):
        result = group_players(self.players)
        for username, players in result:
            players = list(players)
            assert players == [x for x in self.players if x.username == username]
            assert len(players) == int(username[-1])

    def test_custom_key(self):
        result = group_players(self.players, key=lambda x: x.uuid)
        for uuid, players in result:
            players = list(players)
            assert players == [x for x in self.players if x.uuid == uuid]
            assert len(players) == 5 - int(uuid)


class TestRemovePlayersSafely:
    @pytest.fixture(autouse=True)
    def mocks(self):
        # self.plyayer_m = mock.patch("server_manager.src.checks.Player")
        yield
        mock.patch.stopall()

    def test_ok(self, caplog):
        caplog.set_level(10, "server_manager.src.checks")
        player = mock.MagicMock(username="p", online=True)
        player.get_ender_chest.return_value = []
        player.get_inventory.return_value = []
        players = [player] * 5

        remove_players_safely(players)

        assert len(caplog.records) == 10
        records = iter(caplog.records)
        for record_1 in records:
            assert record_1.levelname == "DEBUG"
            assert record_1.message == "Analysing player p [True]"

            rec2 = next(records)
            assert rec2.levelname == "INFO"
            assert rec2.message == "Removed player p [True]"

    def test_fail_inventory(self, caplog):
        caplog.set_level(10, "server_manager.src.checks")
        player = mock.MagicMock(username="p", online=True)
        player.get_ender_chest.return_value = []
        player.get_inventory.return_value = ["a", "b"]
        player.to_extended_repr.return_value = "<ext-repr>"
        players = [player] * 5

        remove_players_safely(players)

        assert len(caplog.records) == 10
        records = iter(caplog.records)
        for rec1 in records:
            assert rec1.levelname == "DEBUG"
            assert rec1.message == "Analysing player p [True]"

            rec2 = next(records)
            assert rec2.levelname == "ERROR"
            assert (
                rec2.msg
                == "Can't remove player %s\nItems: ender_chest=%d, inventory=%d"
            )
            assert rec2.args == ("<ext-repr>", 0, 2)

    def test_fail_ender_chest(self, caplog):
        caplog.set_level(10, "server_manager.src.checks")
        player = mock.MagicMock(username="p", online=True)
        player.get_ender_chest.return_value = ["a", "b", "c"]
        player.get_inventory.return_value = []
        player.to_extended_repr.return_value = "<ext-repr>"
        players = [player] * 5

        remove_players_safely(players)

        assert len(caplog.records) == 10
        records = iter(caplog.records)
        for rec1 in records:
            assert rec1.levelname == "DEBUG"
            assert rec1.message == "Analysing player p [True]"

            rec2 = next(records)
            assert rec2.levelname == "ERROR"
            assert (
                rec2.msg
                == "Can't remove player %s\nItems: ender_chest=%d, inventory=%d"
            )
            assert rec2.args == ("<ext-repr>", 3, 0)

    def test_fail_both(self, caplog):
        caplog.set_level(10, "server_manager.src.checks")
        player = mock.MagicMock(username="p", online=True)
        player.get_ender_chest.return_value = ["a", "b", "c"]
        player.get_inventory.return_value = ["a", "b", "c", "d", "e"]
        player.to_extended_repr.return_value = "<ext-repr>"
        players = [player] * 5

        remove_players_safely(players)

        assert len(caplog.records) == 10
        records = iter(caplog.records)
        for rec1 in records:
            assert rec1.levelname == "DEBUG"
            assert rec1.message == "Analysing player p [True]"

            rec2 = next(records)
            assert rec2.levelname == "ERROR"
            assert (
                rec2.msg
                == "Can't remove player %s\nItems: ender_chest=%d, inventory=%d"
            )
            assert rec2.args == ("<ext-repr>", 3, 5)
        player.remove.assert_not_called()
