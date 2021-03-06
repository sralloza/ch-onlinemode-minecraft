import itertools
from pathlib import Path
import re
from unittest import mock

import pytest

from server_manager.src.exceptions import InvalidPlayerError
from server_manager.src.files import AdvancementsFile, File, PlayerDataFile, StatsFile
from server_manager.src.player import Coords, Item, Player, change_players_mode

# pylint: disable=redefined-outer-name


class TestItem:
    @pytest.fixture
    def item(self):
        yield Item("netherite sword", 4)

    def test_attributes(self, item):
        assert isinstance(item, Item)
        assert hasattr(item, "name")
        assert hasattr(item, "count")
        assert isinstance(item.name, str)
        assert isinstance(item.count, int)

    def test_str(self, item):
        assert str(item) == "Item(name='netherite sword', count=4)"

    def test_repr(self, item):
        assert str(item) == repr(item)

    def test_eq(self, item):
        assert item == Item("netherite sword", 4)
        assert item != Item("netherite ingot", 4)
        assert item != Item("netherite sword", 5)


@pytest.fixture
def player_mocks():
    gu_m = mock.patch("server_manager.src.player.get_username").start()
    gm_m = mock.patch("server_manager.src.player.get_mode").start()

    yield gm_m, gu_m

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


def test_get_nbt_data(player_mocks):
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    pdf_m = mock.MagicMock()
    nbt_path = Path(__file__).parent.parent.joinpath("test_data/nbt-example.dat")
    pdf_m.read_bytes.return_value = nbt_path.read_bytes()
    sf_m = mock.MagicMock()
    af_m = mock.MagicMock()

    adv_file = AdvancementsFile("<adv-path>")
    stats_file = StatsFile("<stats-path>")
    data_file = PlayerDataFile("<data-path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)
    player.player_data_file = pdf_m
    player.stats_file = sf_m
    player.advancements_file = af_m

    nbt_data = player.get_nbt_data()
    assert len(nbt_data) == 52
    assert nbt_data["AbsorptionAmount"] == 0
    assert nbt_data["DataVersion"] == 2567
    assert nbt_data["DeathTime"] == 0
    assert nbt_data["Dimension"] == "minecraft:overworld"
    assert len(nbt_data["EnderItems"]) == 15
    assert nbt_data["Fire"] == 0
    assert nbt_data["HurtByTimestamp"] == 2183960
    assert len(nbt_data["Inventory"]) == 10
    assert nbt_data["Motion"][0] == 0
    assert nbt_data["Motion"][1] == 0
    assert nbt_data["Motion"][2] == 0
    assert nbt_data["OnGround"] == 0
    assert nbt_data["PortalCooldown"] == 0
    assert nbt_data["foodLevel"] == 17
    assert nbt_data["seenCredits"] == 1

    pdf_m.read_bytes.assert_called_once_with()


def test_analyse_items(player_mocks):
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    pdf_m = mock.MagicMock()
    nbt_path = Path(__file__).parent.parent.joinpath("test_data/nbt-example.dat")
    pdf_m.read_bytes.return_value = nbt_path.read_bytes()
    sf_m = mock.MagicMock()
    af_m = mock.MagicMock()

    adv_file = AdvancementsFile("<adv-path>")
    stats_file = StatsFile("<stats-path>")
    data_file = PlayerDataFile("<data-path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)
    player.player_data_file = pdf_m
    player.stats_file = sf_m
    player.advancements_file = af_m

    nbt_data = player.get_nbt_data()
    items = player.analyse_items(nbt_data["Inventory"])
    expected_items = {
        "andesite": 6,
        "cobblestone": 16,
        "diorite": 36,
        "flint and steel": 1,
        "gravel": 3,
        "orange terracotta": 8,
        "red terracotta": 9,
        "stone": 1,
        "tnt": 1,
        "torch": 1,
    }
    expected_items = [Item(k, v) for k, v in expected_items.items()]
    expected_items.sort(key=lambda x: x.name)
    assert items == expected_items


dims = [
    ("minecraft:the_nether", "the_nether"),
    ("minecraft:overworld", "overworld"),
    ("minecraft:the_end", "the_end"),
]


@pytest.mark.parametrize("unparsed_dim,parsed_dim", dims)
@mock.patch("server_manager.src.player.Player.get_nbt_data")
def test_position(gnbtd_m, player_mocks, unparsed_dim, parsed_dim):
    gnbtd_m.return_value = {"Pos": [321, 255, 123], "Dimension": unparsed_dim}
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    adv_file = AdvancementsFile("<adv-path>")
    stats_file = StatsFile("<stats-path>")
    data_file = PlayerDataFile("<data-path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)
    expected = Coords(parsed_dim, 321, 255, 123)
    assert player.get_position() == expected


@mock.patch("server_manager.src.player.Player.get_nbt_data")
def test_get_inventory(gnbtd_m, player_mocks):
    gnbtd_m.return_value = {"Inventory": "<inventory>"}
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    adv_file = AdvancementsFile("<adv-path>")
    stats_file = StatsFile("<stats-path>")
    data_file = PlayerDataFile("<data-path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)

    assert player.get_inventory() == "<inventory>"


@mock.patch("server_manager.src.player.Player.analyse_items")
@mock.patch("server_manager.src.player.Player.get_inventory")
def test_get_detailed_inventory(get_inv_m, analyse_m, player_mocks):
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    adv_file = AdvancementsFile("<adv-path>")
    stats_file = StatsFile("<stats-path>")
    data_file = PlayerDataFile("<data-path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)
    assert player.get_detailed_inventory() == analyse_m.return_value
    analyse_m.assert_called_once_with(get_inv_m.return_value)
    get_inv_m.assert_called_once_with()


@mock.patch("server_manager.src.player.Player.get_nbt_data")
def test_get_ender_chest(gnbtd_m, player_mocks):
    gnbtd_m.return_value = {"EnderItems": "<ender-items>"}
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    adv_file = AdvancementsFile("<adv-path>")
    stats_file = StatsFile("<stats-path>")
    data_file = PlayerDataFile("<data-path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)

    assert player.get_ender_chest() == "<ender-items>"


@mock.patch("server_manager.src.player.Player.analyse_items")
@mock.patch("server_manager.src.player.Player.get_ender_chest")
def test_get_detailed_ender_chest(get_inv_m, analyse_m, player_mocks):
    gm_m, gu_m = player_mocks
    gm_m.return_value = "<mode>"
    gu_m.return_value = "<username>"

    adv_file = AdvancementsFile("<adv-path>")
    stats_file = StatsFile("<stats-path>")
    data_file = PlayerDataFile("<data-path>")

    player = Player("<uuid>", adv_file, stats_file, data_file)
    assert player.get_detailed_ender_chest() == analyse_m.return_value
    analyse_m.assert_called_once_with(get_inv_m.return_value)
    get_inv_m.assert_called_once_with()


def test_remove(player_mocks):
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

    player.remove()

    pdf_m.remove.assert_called_once_with()
    sf_m.remove.assert_called_once_with()
    af_m.remove.assert_called_once_with()


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

    @pytest.fixture(autouse=True)
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

        self.CustomPlayer = CustomPlayer  # pylint: disable=invalid-name
        assert str(CustomPlayer(1, 2, 3)) == "CustomPlayer(uuid=1, files=(2, 3))"
        assert repr(CustomPlayer(1, 2, 3)) == "CustomPlayer(uuid=1, files=(2, 3))"

        File.uuid_pattern = re.compile(r"<[-\w]+>")
        self.guff = mock.patch(
            "server_manager.src.files.File.get_uuid_from_filepath"
        ).start()
        self.guff.side_effect = lambda file: re.search(r"<(\w+)>", str(file)).group()
        self.gf_m = mock.patch("server_manager.src.files.File.gen_files").start()
        self.pl_m = mock.patch("server_manager.src.player.Player").start()
        self.pl_m.side_effect = CustomPlayer
        self.gsp_m = mock.patch("server_manager.src.player.get_server_path").start()
        self.gsp_m.return_value = Path("root")
        mock.patch("server_manager.src.files.File.memory", self.memory).start()

        yield

        mock.patch.stopall()

    @pytest.mark.parametrize("root_path", [None, Path("root")])
    def test_ok(self, root_path, caplog):
        caplog.set_level(10)
        players = Player.generate(root_path)
        assert len(caplog.records) == 2
        self.gf_m.assert_called_once_with(Path("root"))

        if root_path:
            self.gsp_m.assert_not_called()
        else:
            self.gsp_m.assert_called_once_with()

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
        self.pl_m.assert_called()
        assert self.pl_m.call_count == 3


@pytest.mark.parametrize("new_mode", [True, False])
@mock.patch("server_manager.src.player.get_username")
@mock.patch("server_manager.src.player.get_uuid")
def test_change_players_mode(guuid_m, gusername_m, new_mode):
    player = mock.MagicMock()
    players = [player] * 5

    change_players_mode(players, new_mode=new_mode)

    assert gusername_m.call_count == 5

    gusername_m.assert_called_with(player.uuid)
    assert guuid_m.call_count == 5
    guuid_m.assert_called_with(gusername_m.return_value, new_mode)
