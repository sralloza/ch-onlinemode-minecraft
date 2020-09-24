from itertools import groupby
from unittest import mock

import pytest

from server_manager.src.exceptions import SearchError
from server_manager.src.players_data import (
    CSV_PATH,
    get_mode,
    get_players_data,
    get_username,
    get_uuid,
    translate,
)


def test_get_players_data():
    assert CSV_PATH.exists()
    assert CSV_PATH.is_file()

    players_data = get_players_data()

    for player in players_data:
        assert hasattr(player, "uuid")
        assert hasattr(player, "username")
        assert hasattr(player, "online")

    for username, group in groupby(players_data, lambda x: x.username):
        group = list(group)
        assert len(group) == 2

        first, second = group

        assert first.username == second.username == username
        assert first.uuid != second.uuid
        assert first.online != second.online
        assert first.online == (not second.online)


def test_get_uuid_ok():
    assert get_uuid("SrAlloza", True) == "4a618768-4f26-4688-8ab5-6e64f250c62f"
    assert get_uuid("SrAlloza", False) == "be17640b-8471-321e-a355-d2a2859ebda1"


@mock.patch("server_manager.src.players_data.get_players_data")
def test_get_uuid_fatal(gpd_m):
    gpd_m.return_value = []

    with pytest.raises(SearchError):
        get_uuid("someone", True)


def test_get_username():
    assert get_username("4a618768-4f26-4688-8ab5-6e64f250c62f") == "SrAlloza"
    assert get_username("be17640b-8471-321e-a355-d2a2859ebda1") == "SrAlloza"


@mock.patch("server_manager.src.players_data.get_players_data")
def test_get_username_fatal(gpd_m):
    gpd_m.return_value = []

    with pytest.raises(SearchError):
        get_username("some-id")


def test_get_mode():
    assert get_mode("4a618768-4f26-4688-8ab5-6e64f250c62f") is True
    assert get_mode("be17640b-8471-321e-a355-d2a2859ebda1") is False


@mock.patch("server_manager.src.players_data.get_players_data")
def test_get_mode_fatal(gpd_m):
    gpd_m.return_value = []

    with pytest.raises(SearchError):
        get_mode("some-id")


@mock.patch("server_manager.src.players_data.get_mode")
@mock.patch("server_manager.src.players_data.get_username")
def test_translate(get_username_m, get_mode_m):
    get_username_m.return_value = "notch"
    get_mode_m.return_value = "notch-mode"

    assert translate("uuid") == "'notch'<notch-mode>"
    get_username_m.assert_called_once_with("uuid")
    get_mode_m.assert_called_once_with("uuid")
