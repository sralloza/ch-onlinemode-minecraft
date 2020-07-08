from unittest import mock

import pytest

from server_manager.src.exceptions import InvalidPluginStateError
from server_manager.src.plugin import (
    PLUGIN_DISABLED_NAME,
    PLUGIN_NAME,
    get_plugin_mode,
    get_plugin_offline_path,
    get_plugin_online_path,
    get_plugins_folder,
    set_plugin_mode,
)


def test_plugin_name():
    assert isinstance(PLUGIN_NAME, str)
    assert PLUGIN_NAME.endswith("jar")


def test_plugin_disabled_name():
    assert isinstance(PLUGIN_DISABLED_NAME, str)
    assert PLUGIN_DISABLED_NAME.endswith("disabled")
    assert PLUGIN_NAME in PLUGIN_DISABLED_NAME


@mock.patch("server_manager.src.plugin.get_server_path")
def test_get_plugins_folder(gsp_m):
    result = get_plugins_folder()

    assert gsp_m.return_value.joinpath.return_value == result
    gsp_m.return_value.joinpath.assert_called_with("plugins")


@mock.patch("server_manager.src.plugin.PLUGIN_DISABLED_NAME")
@mock.patch("server_manager.src.plugin.get_plugins_folder")
def test_get_plugin_offline_path(gpf_m, plugin_disabled_name):
    result = get_plugin_offline_path()

    assert gpf_m.return_value.joinpath.return_value == result
    gpf_m.return_value.joinpath.assert_called_with(plugin_disabled_name)


@mock.patch("server_manager.src.plugin.PLUGIN_NAME")
@mock.patch("server_manager.src.plugin.get_plugins_folder")
def test_get_plugin_online_path(gpf_m, plugin_name_m):
    result = get_plugin_online_path()

    assert gpf_m.return_value.joinpath.return_value == result
    gpf_m.return_value.joinpath.assert_called_with(plugin_name_m)


class TestGetPluginMode:
    @pytest.fixture(autouse=True)
    def mocks(self):
        root = "server_manager.src.plugin."
        self.offline_m = mock.patch(root + "get_plugin_offline_path").start()
        self.online_m = mock.patch(root + "get_plugin_online_path").start()

        yield

        mock.patch.stopall()

    def test_plugin_offline(self):
        self.online_m.return_value.is_file.return_value = False
        self.offline_m.return_value.is_file.return_value = True

        result = get_plugin_mode()
        assert result is False

        self.online_m.return_value.is_file.assert_not_called()
        self.offline_m.return_value.is_file.assert_called_once_with()

    def test_plugin_online(self):
        self.online_m.return_value.is_file.return_value = True
        self.offline_m.return_value.is_file.return_value = False

        result = get_plugin_mode()
        assert result is True

        self.online_m.return_value.is_file.assert_called_once_with()
        self.offline_m.return_value.is_file.assert_called_once_with()

    def test_error(self):
        self.online_m.return_value.is_file.return_value = False
        self.offline_m.return_value.is_file.return_value = False

        msg = "Plugin is neither online nor offile"
        with pytest.raises(InvalidPluginStateError, match=msg):
            get_plugin_mode()

        self.online_m.return_value.is_file.assert_called_once_with()
        self.offline_m.return_value.is_file.assert_called_once_with()


class TestSetPluginMode:
    @pytest.fixture(autouse=True)
    def mocks(self):
        root = "server_manager.src.plugin."
        self._online_m = mock.patch(root + "get_plugin_online_path").start()
        self._offline_m = mock.patch(root + "get_plugin_offline_path").start()

        self.online_m = self._online_m.return_value
        self.offline_m = self._offline_m.return_value

        yield

        mock.patch.stopall()

    def test_set_plugin_online(self):
        set_plugin_mode(True)

        self.offline_m.rename.assert_called_once_with(self.online_m)
        self.online_m.rename.assert_not_called()

    def test_set_plugin_offline(self):
        set_plugin_mode(False)

        self.online_m.rename.assert_called_once_with(self.offline_m)
        self.offline_m.rename.assert_not_called()
