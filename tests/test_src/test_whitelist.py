from collections import namedtuple
from unittest import mock

from server_manager.src.whitelist import create_whitelist, update_whitelist


@mock.patch("json.dumps")
@mock.patch("server_manager.src.whitelist.get_players_data")
def test_create_whitelist(gpd_m, dumps_m):
    Player = namedtuple("Player", "username uuid online")
    players = [Player("a", "00a", True), Player("b", "00b", False)]
    whitelist = [{"uuid": "00a", "name": "a"}, {"uuid": "00b", "name": "b"}]
    gpd_m.return_value = players

    result = create_whitelist()

    assert result == dumps_m.return_value
    dumps_m.assert_called_once_with(whitelist, indent=4, ensure_ascii=False)


@mock.patch("server_manager.src.whitelist.create_whitelist")
@mock.patch("server_manager.src.whitelist.get_server_properties_filepath")
def test_update_whitelist(gspf_m, create_whitelist_m):
    update_whitelist()
    gspf_m.assert_called_once_with()
    gspf_m.return_value.with_name.assert_called_with("whitelist.json")
    path = gspf_m.return_value.with_name.return_value
    path.write_text.assert_called_once_with(create_whitelist_m.return_value)
