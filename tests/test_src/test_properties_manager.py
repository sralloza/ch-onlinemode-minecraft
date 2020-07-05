from pathlib import Path
from unittest import mock

import pytest
from colorama import Fore

from server_manager.src.exceptions import InvalidServerStateError
from server_manager.src.properties_manager import (
    get_server_mode,
    get_server_path,
    get_server_properties_filepath,
    properties_manager,
    set_server_mode,
    validate_server_path,
)


class TestGetServerPath:
    @pytest.fixture(autouse=True)
    def mocks(self):
        root = "server_manager.src.properties_manager."
        self.input_m = mock.patch(root + "input").start()
        self.data_path_m = mock.patch(root + "DATA_PATH").start()
        self.vsp_m = mock.patch(root + "validate_server_path").start()
        yield

        mock.patch.stopall()

    def test_file_exists(self):
        self.data_path_m.is_file.return_value = True
        self.data_path_m.read_text.return_value = " \n\n  <root-path>\n \n "

        result = get_server_path()
        assert result == Path("<root-path>")

        self.data_path_m.is_file.assert_called_once_with()
        self.data_path_m.read_text.assert_called_once_with()
        self.data_path_m.write_text.assert_not_called()
        self.vsp_m.assert_not_called()

    def test_file_not_exist(self):
        self.data_path_m.is_file.return_value = False
        self.input_m.return_value = " \n\n  <root-path>\n \n "

        result = get_server_path()
        assert result == Path("<root-path>")

        self.data_path_m.is_file.assert_called_once_with()
        self.data_path_m.read_text.assert_not_called()
        self.input_m.assert_called_once_with("Write the path of the server: ")
        self.vsp_m.assert_called_once_with("<root-path>")
        self.data_path_m.write_text.assert_called_with("<root-path>")


@mock.patch("server_manager.src.properties_manager.get_server_properties_filepath")
def test_validate_server_path_ok(gspf_m):
    gspf_m.return_value.is_file.return_value = True

    validate_server_path("<server-path>")

    gspf_m.assert_called_once_with("<server-path>")
    gspf_m.return_value.is_file.assert_called_once_with()


@mock.patch("server_manager.src.properties_manager.get_server_properties_filepath")
def test_validate_server_path_fail(gspf_m, capsys):
    gspf_m.return_value.is_file.return_value = False
    gspf_m.return_value.as_posix.return_value = "<properties-path>"

    with pytest.raises(SystemExit, match="-1"):
        validate_server_path("<server-path>")

    gspf_m.assert_called_once_with("<server-path>")
    gspf_m.return_value.is_file.assert_called_once_with()
    gspf_m.return_value.as_posix.assert_called_once_with()

    captured = capsys.readouterr()
    assert Fore.LIGHTRED_EX in captured.err
    assert Fore.RESET in captured.err
    assert "server.properties not found: '<properties-path>'" in captured.err
    assert captured.out == ""


def test_get_server_properties_filepath():
    expected = Path("/var/minecraft/server/server.properties")
    result = get_server_properties_filepath("/var/minecraft/server")
    assert result == expected


class TestPropertiesManager:
    @pytest.fixture(autouse=True)
    def mocks(self):
        root = "server_manager.src.properties_manager."
        self.gspf_m = mock.patch(root + "get_server_properties_filepath").start()
        self.str2bool_m = mock.patch(root + "str2bool").start()
        self.bool2str_m = mock.patch(root + "bool2str").start()
        self.prop_path = Path(__file__).parent.parent.joinpath(
            "test_data/server.properties"
        )
        self.text = self.prop_path.read_text()
        self.gspf_m.return_value.read_text.return_value = self.text
        self.onlines = {True: "true", False: "false"}

        yield

        self.gspf_m.return_value.read_text.assert_called_once_with(encoding="utf-8")
        mock.patch.stopall()

    def test_get_current_mode(self):
        result = properties_manager(online_mode=None)
        assert result == self.str2bool_m.return_value
        self.gspf_m.assert_called_once_with()
        self.str2bool_m.assert_called_once_with("onlinemode", parser=False)

    @pytest.mark.parametrize("online", [True, False])
    def test_current_mode_fail(self, online):
        self.str2bool_m.return_value = online
        with pytest.raises(InvalidServerStateError):
            properties_manager(online_mode=online)

        self.str2bool_m.assert_called_once_with("onlinemode", parser=False)

    @pytest.mark.parametrize("online", [True, False])
    def test_current_mode_ok(self, online):
        self.str2bool_m.return_value = not online
        self.bool2str_m.side_effect = self.onlines.get

        result = properties_manager(online_mode=online)
        assert result == online  # returns the new online mode

        self.str2bool_m.assert_any_call("onlinemode", parser=False)
        new_text = self.text.replace("onlinemode", self.onlines[online])
        self.gspf_m.return_value.write_text.assert_called_once_with(
            new_text, encoding="utf-8"
        )


@pytest.mark.parametrize("online", [True, False])
@mock.patch("server_manager.src.properties_manager.properties_manager")
def test_set_server_mode(pm_m, online):
    result = set_server_mode(online_mode=online)
    pm_m.assert_called_with(online_mode=online)
    assert result == pm_m.return_value


@mock.patch("server_manager.src.properties_manager.properties_manager")
def test_get_server_mode(pm_m):
    result = get_server_mode()
    pm_m.assert_called_with(online_mode=None)
    assert result == pm_m.return_value
