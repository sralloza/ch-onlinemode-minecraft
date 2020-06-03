import itertools
from pathlib import Path
import re
from unittest import mock

import pytest

from server_manager.src.exceptions import InvalidPlayerError
from server_manager.src.files import AdvancementsFile, File, PlayerDataFile, StatsFile
from server_manager.src.player import Player


@pytest.fixture
def player_mocks():
    gu = mock.patch("server_manager.src.player.get_username").start()
    gm = mock.patch("server_manager.src.player.get_mode").start()

    yield gm, gu

    mock.patch.stopall()


class TestInit:
    def test_ok(self, player_mocks):
        gm_m, gu_m = player_mocks
        gm_m.return_value = "<username>"
        gu_m.return_value = "<mode>"

        adv_file = AdvancementsFile("<path>")
        stats_file = StatsFile("<path>")
        data_file = PlayerDataFile("<path>")

        permutations = list(itertools.permutations((adv_file, stats_file, data_file)))
        players = []

        for files in permutations:
            players.append(Player("<uuid>", *files))

        assert gm_m.call_count == gu_m.call_count == 6

        for player in players[1:]:
            assert player == players[0]

    def test_error(self, player_mocks):
        gm_m, gu_m = player_mocks
        gm_m.return_value = "<username>"
        gu_m.return_value = "<mode>"

        adv_file = AdvancementsFile("<path>")
        stats_file = StatsFile("<path>")
        data_file = PlayerDataFile("<path>")

        permutations = list(
            itertools.permutations((adv_file, stats_file, data_file), 2)
        )

        for files in permutations:
            with pytest.raises(InvalidPlayerError, match="Can't create Player"):
                Player("<uuid>", *files)

        assert gm_m.call_count == gu_m.call_count == 6

        with pytest.raises(TypeError, match="files can't be"):
            Player("<uuid>", "invalid-file")


def test_repr(player_mocks):
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    adv_file = AdvancementsFile("<path>")
    stats_file = StatsFile("<path>")
    data_file = PlayerDataFile("<path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)
    assert repr(player) == "Player(<username>|<mode> - <uuid>)"

    assert gm_m.call_count == 1
    assert gu_m.call_count == 1


def test_eq(player_mocks):
    gm_m, gu_m = player_mocks

    adv_file = AdvancementsFile("<path>")
    stats_file = StatsFile("<path>")
    data_file = PlayerDataFile("<path>")

    player1 = Player("<uuid>", adv_file, stats_file, data_file)
    player2 = Player("<uuid>", adv_file, stats_file, data_file)

    assert player1 == player2

    assert gm_m.call_count == 2
    assert gu_m.call_count == 2


def test_neq(player_mocks):
    gm_m, gu_m = player_mocks

    adv_file1 = AdvancementsFile("<path-1>")
    stats_file1 = StatsFile("<path-1>")
    data_file1 = PlayerDataFile("<path-1>")

    adv_file2 = AdvancementsFile("<path-2>")
    stats_file2 = StatsFile("<path-2>")
    data_file2 = PlayerDataFile("<path-2>")

    player1 = Player("<uuid-1>", adv_file1, stats_file1, data_file1)
    player2 = Player("<uuid-2>", adv_file1, stats_file1, data_file1)
    player3 = Player("<uuid-1>", adv_file2, stats_file1, data_file1)
    player4 = Player("<uuid-1>", adv_file1, stats_file2, data_file1)
    player5 = Player("<uuid-1>", adv_file1, stats_file1, data_file2)

    assert player1 != player2
    assert player1 != player3
    assert player1 != player4
    assert player1 != player5

    assert gm_m.call_count == 5
    assert gu_m.call_count == 5


def test_to_extended_repr(player_mocks):
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    adv_file = AdvancementsFile("<adv-path>")
    stats_file = StatsFile("<stats-path>")
    data_file = PlayerDataFile("<data-path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)

    expected = (
        "Player(<username>|<mode> - <uuid>, "
        "player_data_file='<data-path>', stats_file='<stats-path>', "
        "advancements_file='<adv-path>')"
    )
    assert player.to_extended_repr() == expected


def test_change_uuid(player_mocks):
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    pdf_m = mock.MagicMock()
    sf_m = mock.MagicMock()
    af_m = mock.MagicMock()

    adv_file = AdvancementsFile("<adv-path>")
    stats_file = StatsFile("<stats-path>")
    data_file = PlayerDataFile("<data-path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)
    player.player_data_file = pdf_m
    player.stats_file = sf_m
    player.advancements_file = af_m

    player.change_uuid("<new-uuid>")

    pdf_m.change_uuid.assert_called_once_with("<new-uuid>")
    sf_m.change_uuid.assert_called_once_with("<new-uuid>")
    af_m.change_uuid.assert_called_once_with("<new-uuid>")


class TestGenerate:
    @classmethod
    def setup_class(cls):
        class TypeA(File):
            pass

        class TypeB(File):
            pass

        class TypeC(File):
            pass

        cls.subtypes = {"typea": TypeA, "typeb": TypeB, "typec": TypeC}
        cls.memory = {
            "typea": [TypeA("pa-<ply1>"), TypeA("pa-<ply2>"), TypeA("pa-<ply3>")],
            "typeb": [TypeB("pb-<ply1>"), TypeB("pb-<ply2>"), TypeB("pb-<ply3>")],
            "typec": [TypeC("pc-<ply1>"), TypeC("pc-<ply2>"), TypeC("pc-<ply3>")],
        }

        # File.subtypes = cls.subtypes


        # cls.Base = Base
        cls.TypeA = TypeA
        cls.TypeB = TypeB
        cls.TypeC = TypeC

    @pytest.fixture
    def mocks(self):
        class CustomPlayer:
            def __init__(self, uuid, *files):
                self.uuid = uuid

                # For sorting commpatibility
                self.username = uuid
                self.files = files

            def __eq__(self, other):
                return vars(self) == vars(other)

            def __str__(self):
                return f"CustomPlayer(uuid={self.uuid}, files={self.files})"

            def __repr__(self):
                return str(self)

        self.CustomPlayer = CustomPlayer

        File.uuid_pattern = re.compile(r"<[-\w]+>")
        gf_m = mock.patch("server_manager.src.files.File.gen_files").start()
        pl_m = mock.patch("server_manager.src.player.Player").start()
        pl_m.side_effect = lambda *x: CustomPlayer(*x)
        fm_m = mock.patch("server_manager.src.files.File.memory", self.memory).start()

        yield gf_m, pl_m

        mock.patch.stopall()

    def test_ok(self, mocks):
        gf_m, pl_m = mocks

        players = Player.generate(Path("root"))
        gf_m.assert_called_once_with(Path("root"))

        assert len(players) == 3
        expected = [
            self.CustomPlayer(
                "<ply1>",
                self.TypeA("pa-<ply1>"),
                self.TypeB("pb-<ply1>"),
                self.TypeC("pc-<ply1>"),
            ),
            self.CustomPlayer(
                "<ply2>",
                self.TypeA("pa-<ply2>"),
                self.TypeB("pb-<ply2>"),
                self.TypeC("pc-<ply2>"),
            ),
            self.CustomPlayer(
                "<ply3>",
                self.TypeA("pa-<ply3>"),
                self.TypeB("pb-<ply3>"),
                self.TypeC("pc-<ply3>"),
            ),
        ]

        assert players == expected
        pl_m.assert_called()
        assert pl_m.call_count == 3

    def test_error(self, mocks):
        gf_m, pl_m = mocks
        self.memory["typea"][0] = self.TypeA("invalid-path")

        with pytest.raises(ValueError, match="invalid-path"):
            Player.generate(Path("root"))

        gf_m.assert_called_once_with(Path("root"))
        pl_m.assert_not_called()
