from enum import Enum
from pathlib import Path
from unittest import mock

import pytest
from colorama import Fore
from server_manager.src.properties_manager import (
    Properties,
    PropertiesManager,
    get_server_mode,
    get_server_properties_filepath,
    set_server_mode,
    validate_server_path,
)


class TestPropertiesEnum:
    def test_members_values(self):
        assert Properties.online_mode == Properties("online-mode")
        assert Properties.whitelist == Properties("whitelist")

    def test_members_names(self):
        assert Properties.online_mode == Properties["online_mode"]
        assert Properties.whitelist == Properties["whitelist"]

    def test_types(self):
        for prop in Properties:
            assert isinstance(prop.name, str)
            assert isinstance(prop.value, str)
            assert prop.name.replace("_", "-") == prop.value


class TestValidateServerPath:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.gspf_m = mock.patch(
            "server_manager.src.properties_manager.get_server_properties_filepath"
        ).start()
        yield
        mock.patch.stopall()

    def test_ok(self):
        self.gspf_m.return_value.is_file.return_value = True

        validate_server_path("<server-path>")

        self.gspf_m.assert_called_once_with("<server-path>")
        self.gspf_m.return_value.is_file.assert_called_once_with()

    def test_fail(self, capsys):
        self.gspf_m.return_value.is_file.return_value = False
        self.gspf_m.return_value.as_posix.return_value = "<properties-path>"

        with pytest.raises(SystemExit, match="-1"):
            validate_server_path("<server-path>")

        self.gspf_m.assert_called_once_with("<server-path>")
        self.gspf_m.return_value.is_file.assert_called_once_with()
        self.gspf_m.return_value.as_posix.assert_called_once_with()

        captured = capsys.readouterr()
        assert Fore.LIGHTRED_EX in captured.err
        assert Fore.RESET in captured.err
        assert "server.properties not found: '<properties-path>'" in captured.err
        assert captured.out == ""


@mock.patch("server_manager.src.properties_manager.get_server_path")
def test_get_server_properties_filepath(gsp_m):
    gsp_m.return_value = "<server-path>"

    expected = Path("/var/minecraft/server/server.properties")
    result = get_server_properties_filepath("/var/minecraft/server")
    assert result == expected

    result = get_server_properties_filepath()
    assert result == Path("<server-path>/server.properties")
    gsp_m.assert_called_once_with()

    # Test LRU cache
    result = get_server_properties_filepath()
    assert result == Path("<server-path>/server.properties")
    gsp_m.assert_called_once_with()

    get_server_properties_filepath.cache_clear()

    result = get_server_properties_filepath()
    assert result == Path("<server-path>/server.properties")
    gsp_m.assert_called()
    assert gsp_m.call_count == 2


class TestPropertiesManager:
    @pytest.fixture(autouse=True)
    def mocks(self):
        root = "server_manager.src.properties_manager."
        self.gspf_m = mock.patch(root + "get_server_properties_filepath").start()
        self.prop_path = Path(__file__).parent.parent.joinpath(
            "test_data/server.properties"
        )
        self.text = self.prop_path.read_text()
        self.gspf_m.return_value.read_text.return_value = self.text

        self.mock_a = mock.MagicMock()
        self.mock_b = mock.MagicMock()
        self.mock_c = mock.MagicMock()

        class NewProperties(Enum):
            mock_a = "mock-a"
            mock_b = "mock-b"
            mock_c = "mock-c"
            dummy = "dummy"

        self.NewProperties = NewProperties
        mock.patch(root + "Properties", NewProperties).start()

        self.getters = {
            NewProperties.mock_a: lambda: 10,
            NewProperties.mock_b: lambda: 11,
            NewProperties.mock_c: lambda: 12,
            NewProperties.dummy: None
        }
        mock.patch(root + "PropertiesManager.getters_map", self.getters).start()

        self.setters = {
            NewProperties.mock_a: self.mock_a,
            NewProperties.mock_b: self.mock_b,
            NewProperties.mock_c: self.mock_c,
            NewProperties.dummy: None,
        }
        mock.patch(root + "PropertiesManager.setters_map", self.setters).start()

        yield

        mock.patch.stopall()

    def test_get_property(self):
        assert PropertiesManager.get_property("mock-a") == 10
        assert PropertiesManager.get_property("mock-b") == 11
        assert PropertiesManager.get_property("mock-c") == 12

    def test_set_property(self):
        self.mock_a.assert_not_called()
        self.mock_b.assert_not_called()
        self.mock_c.assert_not_called()

        PropertiesManager.set_property(mock_a="a")

        self.mock_a.assert_called_once_with("a")
        self.mock_b.assert_not_called()
        self.mock_c.assert_not_called()

        PropertiesManager.set_property(mock_b=52)
        self.mock_a.assert_called_once_with("a")
        self.mock_b.assert_called_once_with(52)
        self.mock_c.assert_not_called()

        PropertiesManager.set_property(mock_c=-9)
        self.mock_a.assert_called_once_with("a")
        self.mock_b.assert_called_once_with(52)
        self.mock_c.assert_called_once_with(-9)

    def test_get_properties_raw(self):
        properties_raw = PropertiesManager.get_properties_raw()
        assert properties_raw == self.text
        self.gspf_m.return_value.read_text.assert_called_once_with(encoding="utf-8")

        # LRU cache
        properties_raw = PropertiesManager.get_properties_raw()
        assert properties_raw == self.text
        self.gspf_m.return_value.read_text.assert_called_once_with(encoding="utf-8")

    def test_write_properties_raw(self):
        PropertiesManager.write_properties_raw("<server.properties>")
        self.gspf_m.return_value.write_text.assert_called_once_with(
            "<server.properties>", encoding="utf-8"
        )

    def test_register_property(self):
        class DummyProperty:
            @classmethod
            def set(cls, *args):
                return

            @classmethod
            def get(cls,):
                return

        prop = self.NewProperties.dummy

        assert PropertiesManager.getters_map[prop] is None
        assert PropertiesManager.setters_map[prop] is None

        PropertiesManager.register_property(DummyProperty, "dummy")

        assert PropertiesManager.getters_map[prop] == DummyProperty.get
        assert PropertiesManager.setters_map[prop] == DummyProperty.set
