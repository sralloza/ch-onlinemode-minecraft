from enum import Enum
from pathlib import Path
from unittest import mock

from colorama import Fore
import pytest

from server_manager.src.exceptions import PropertyError
from server_manager.src.properties_manager import (
    DifficultyProperty,
    MetaProperty,
    Properties,
    PropertiesManager,
    WhitelistProperty,
    get_server_properties_filepath,
    set_default_properties,
    validate_server_path,
)
from server_manager.src.utils import str2bool


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

    def test_get(self):
        for prop in Properties:
            assert Properties.get(prop) == prop
            assert Properties.get(prop.name) == prop
            assert Properties.get(prop.value) == prop


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

            @classmethod
            def get(cls, value):
                try:
                    return cls[value]
                except KeyError:
                    return cls(value)

        self.new_properties = NewProperties
        mock.patch(root + "Properties", NewProperties).start()

        self.validator_m = mock.MagicMock()
        self.validator_m.a.str_to_value = str
        self.validator_m.b.str_to_value = str2bool
        self.validator_m.c.str_to_value = int

        self.general_map = {
            NewProperties.mock_a: self.validator_m.a,
            NewProperties.mock_b: self.validator_m.b,
            NewProperties.mock_c: self.validator_m.c,
            NewProperties.dummy: None,
        }
        mock.patch(root + "PropertiesManager.general_map", self.general_map).start()

        self.getters = {
            NewProperties.mock_a: lambda: 10,
            NewProperties.mock_b: lambda: 11,
            NewProperties.mock_c: lambda: 12,
            NewProperties.dummy: None,
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

    def test_adapt_value(self):
        assert PropertiesManager.adapt_value("mock-a", 123) == "123"
        assert PropertiesManager.adapt_value("mock-b", "on") is True
        assert PropertiesManager.adapt_value("mock-c", "12") == 12

    def test_set_property_ok(self):
        self.mock_a.assert_not_called()
        self.mock_b.assert_not_called()
        self.mock_c.assert_not_called()

        PropertiesManager.set_property(mock_a="a")

        self.mock_a.assert_called_once_with("a")
        self.mock_b.assert_not_called()
        self.mock_c.assert_not_called()

        PropertiesManager.set_property(mock_b="on")
        self.mock_a.assert_called_once_with("a")
        self.mock_b.assert_called_once_with(True)
        self.mock_c.assert_not_called()

        PropertiesManager.set_property(mock_c=-9)
        self.mock_a.assert_called_once_with("a")
        self.mock_b.assert_called_once_with(True)
        self.mock_c.assert_called_once_with(-9)

    def test_set_property_fail(self):
        with pytest.raises(ValueError):
            PropertiesManager.set_property(invalid_property=True)

        with pytest.raises(ValueError):
            PropertiesManager.set_property()

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
            get = 0
            set = 1

        prop = self.new_properties.dummy

        assert PropertiesManager.getters_map[prop] is None
        assert PropertiesManager.setters_map[prop] is None

        PropertiesManager.register_property(DummyProperty, "dummy")

        assert PropertiesManager.getters_map[prop] == DummyProperty.get
        assert PropertiesManager.setters_map[prop] == DummyProperty.set


class TestMetaProperty:
    @pytest.fixture(autouse=True)
    def mocks(self):
        root = "server_manager.src.properties_manager."
        self.reg_prop_m = mock.patch(
            root + "PropertiesManager.register_property"
        ).start()

        yield

        mock.patch.stopall()

    def test_ok(self):
        class BaseSomething1(metaclass=MetaProperty):
            pass

        assert BaseSomething1.__name__ == "BaseSomething1"

        self.reg_prop_m.assert_not_called()

        class BaseSomething2(BaseSomething1):
            pass

        assert BaseSomething2.__name__ == "BaseSomething2"

        self.reg_prop_m.assert_not_called()

        class NormalClass(metaclass=MetaProperty):
            property_name = "normal-class"

        assert NormalClass.__name__ == "NormalClass"

        self.reg_prop_m.assert_called_once_with(NormalClass, "normal-class")

        class NormalClass2(NormalClass):
            property_name = "normal-class-2"

        assert NormalClass2.__name__ == "NormalClass2"

        self.reg_prop_m.assert_called()
        assert self.reg_prop_m.call_count == 2
        self.reg_prop_m.any_call(NormalClass2, "normal-class-2")

    def test_fail(self):
        with pytest.raises(ValueError, match="Must set property name"):

            # pylint: disable=unused-variable
            class FailedClass(metaclass=MetaProperty):
                pass

        class GoodBase1(metaclass=MetaProperty):
            property_name = None

        with pytest.raises(ValueError, match="Must set property name"):

            # pylint: disable=unused-variable
            class FailedClass1(GoodBase1):
                pass

        class GoodBase2(metaclass=MetaProperty):
            pass

        with pytest.raises(ValueError, match="Must set property name"):

            # pylint: disable=unused-variable
            class FailedClass2(GoodBase2):
                pass


class TestNormalProperties:
    defaults = {
        "allow-nether": True,
        "broadcast-rcon-to-ops": True,
        "difficulty": "hard",
        "enable-rcon": True,
        "enable-status": True,
        "enforce-whitelist": True,
        "max-players": 3,
        "online-mode": True,
        "rcon.password": "",
        "rcon.port": 25575,
        "whitelist": True,
    }
    new_values = {
        "allow-nether": False,
        "broadcast-rcon-to-ops": False,
        "difficulty": "peaceful",
        "enable-rcon": False,
        "enable-status": False,
        "enforce-whitelist": False,
        "max-players": 50,
        "online-mode": False,
        "rcon.password": "fdssfasdf",
        "rcon.port": 15957,
        "whitelist": False,
    }
    wrong_values = {
        "allow-nether": 1 + 2j,
        "broadcast-rcon-to-ops": "hello there",
        "difficulty": 23,
        "enable-rcon": "maybe",
        "enable-status": "what?",
        "enforce-whitelist": "?",
        "max-players": False,
        "online-mode": "I am the king",
        "rcon.password": dict(),
        "rcon.port": list(),
        "whitelist": set(),
    }

    properties = [
        "AllowNetherProperty",
        "BroadcastRconToOpsProperty",
        "EnableRconProperty",
        "EnableStatusProperty",
        "MaxPlayersProperty",
        "OnlineModeProperty",
        "RconPasswordProperty",
        "RconPortProperty",
    ]

    @pytest.fixture(autouse=True)
    def mocks(self):
        self.module = __import__("server_manager").src.properties_manager

        self.root = "server_manager.src.properties_manager."
        self.gpr_m = mock.patch(
            self.root + "PropertiesManager.get_properties_raw"
        ).start()
        self.wpr_m = mock.patch(
            self.root + "PropertiesManager.write_properties_raw"
        ).start()
        self.prop_path = Path(__file__).parent.parent.joinpath(
            "test_data/server.properties"
        )
        self.text = self.prop_path.read_text()
        self.gpr_m.return_value = self.text

        yield

        mock.patch.stopall()

    @pytest.mark.parametrize("propclassname", properties)
    def test_get(self, propclassname):
        prop = getattr(self.module, propclassname)
        expected = self.defaults[prop.property_name]
        assert prop.get() == expected
        self.gpr_m.assert_called()

    @pytest.mark.parametrize("propclassname", properties)
    def test_set_ok(self, propclassname):
        prop = getattr(self.module, propclassname)
        new_value = self.new_values[prop.property_name]
        prop.set(new_value)
        string = f"{prop.property_name}={prop.value_to_str(new_value)}"
        assert string in self.wpr_m.call_args[0][0]
        self.gpr_m.assert_called()

    @pytest.mark.parametrize("propclassname", properties)
    def test_set_fail_type(self, propclassname):
        prop = getattr(self.module, propclassname)
        wrong_value = self.wrong_values[prop.property_name]
        with pytest.raises(ValueError):
            prop.set(wrong_value)

    @pytest.mark.parametrize("propclassname", properties)
    def test_set_fail_same_value(self, propclassname):
        get_mocker = mock.patch(self.root + propclassname + ".get")
        get_m = get_mocker.start()

        prop = getattr(self.module, propclassname)
        new_value = self.new_values[prop.property_name]
        get_m.return_value = new_value
        with pytest.raises(PropertyError):
            prop.set(new_value)

        get_m.assert_called_once_with()
        get_mocker.stop()

    @pytest.mark.parametrize("propclassname", properties)
    def test_default(self, propclassname):
        set_mocker = mock.patch(self.root + propclassname + ".set")
        set_m = set_mocker.start()

        prop = getattr(self.module, propclassname)
        prop.set_default()

        set_m.assert_called_once_with(prop.default)
        set_mocker.stop()


class TestDifficultyProperty:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.module = __import__("server_manager").src.properties_manager

        self.root = "server_manager.src.properties_manager."
        self.gpr_m = mock.patch(
            self.root + "PropertiesManager.get_properties_raw"
        ).start()
        self.wpr_m = mock.patch(
            self.root + "PropertiesManager.write_properties_raw"
        ).start()
        self.prop_path = Path(__file__).parent.parent.joinpath(
            "test_data/server.properties"
        )
        self.text = self.prop_path.read_text()
        self.gpr_m.return_value = self.text

    def test_get(self):
        expected = TestNormalProperties.defaults["difficulty"]
        assert DifficultyProperty.get() == expected
        self.gpr_m.assert_called()

    def test_str_to_value(self):
        test_ok = DifficultyProperty.str_to_value

        assert test_ok("normal") == "normal"
        assert test_ok("peaceful") == "peaceful"
        assert test_ok("hard") == "hard"

        def test_fail(value):
            with pytest.raises(ValueError):
                DifficultyProperty.str_to_value(value)

        test_fail(23)
        test_fail("super-hard")
        test_fail(1 + 5j)
        test_fail(True)
        test_fail(False)
        test_fail(None)

    def test_set_ok(self):
        new_value = TestNormalProperties.new_values["difficulty"]
        DifficultyProperty.set(new_value)
        string = f"difficulty={DifficultyProperty.value_to_str(new_value)}"
        assert string in self.wpr_m.call_args[0][0]
        self.gpr_m.assert_called()

    def test_set_fail_type(self):
        wrong_value = TestNormalProperties.wrong_values["difficulty"]
        with pytest.raises(ValueError):
            DifficultyProperty.set(wrong_value)

    def test_set_fail_same_value(self):
        get_mocker = mock.patch(self.root + "DifficultyProperty.get")
        get_m = get_mocker.start()

        new_value = TestNormalProperties.new_values["difficulty"]
        get_m.return_value = new_value
        with pytest.raises(PropertyError):
            DifficultyProperty.set(new_value)

        get_m.assert_called_once_with()
        get_mocker.stop()

    def test_default(self):
        set_mocker = mock.patch(self.root + "DifficultyProperty.set")
        set_m = set_mocker.start()

        DifficultyProperty.set_default()

        set_m.assert_called_once_with(DifficultyProperty.default)
        set_mocker.stop()


class TestWhitelistProperty:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.module = __import__("server_manager").src.properties_manager

        self.root = "server_manager.src.properties_manager."
        self.gpr_m = mock.patch(
            self.root + "PropertiesManager.get_properties_raw"
        ).start()
        self.wpr_m = mock.patch(
            self.root + "PropertiesManager.write_properties_raw"
        ).start()
        self.prop_path = Path(__file__).parent.parent.joinpath(
            "test_data/server.properties"
        )
        self.text = self.prop_path.read_text()
        self.gpr_m.return_value = self.text

    def test_get_ok(self):
        expected = TestNormalProperties.defaults["whitelist"]
        assert WhitelistProperty.get() == expected
        self.gpr_m.assert_called()

    @pytest.mark.parametrize("whitelist", [True, False])
    def test_get_fail(self, whitelist):
        part_a = str(not whitelist).lower()
        part_b = str(whitelist).lower()
        msg = f"enforce-whitelist={part_a}\nwhite-list={part_b}"
        self.gpr_m.return_value = msg

        with pytest.raises(ValueError):
            WhitelistProperty.get()

    def test_set_ok(self):
        new_value = TestNormalProperties.new_values["whitelist"]
        WhitelistProperty.set(new_value)
        string1 = f"white-list={WhitelistProperty.value_to_str(new_value)}"
        string2 = f"enforce-whitelist={WhitelistProperty.value_to_str(new_value)}"
        assert string1 in self.wpr_m.call_args[0][0]
        assert string2 in self.wpr_m.call_args[0][0]
        self.gpr_m.assert_called()

    def test_set_fail_type(self):
        wrong_value = TestNormalProperties.wrong_values["whitelist"]
        with pytest.raises(ValueError):
            WhitelistProperty.set(wrong_value)

    def test_set_fail_same_value(self):
        get_mocker = mock.patch(self.root + "WhitelistProperty.get")
        get_m = get_mocker.start()

        new_value = TestNormalProperties.new_values["whitelist"]
        get_m.return_value = new_value
        with pytest.raises(PropertyError):
            WhitelistProperty.set(new_value)

        get_m.assert_called_once_with()
        get_mocker.stop()

    def test_default(self):
        set_mocker = mock.patch(self.root + "WhitelistProperty.set")
        set_m = set_mocker.start()

        WhitelistProperty.set_default()

        set_m.assert_called_once_with(WhitelistProperty.default)
        set_mocker.stop()


class TestSetDefaultProperties:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.root = "server_manager.src.properties_manager."
        self.mock = mock.MagicMock()
        self.gen_map = {
            "a": self.mock.a,
            "b": self.mock.b,
            "c": self.mock.c,
            "d": self.mock.d,
        }
        self.mock.b.set_default.side_effect = PropertyError
        self.mock.d.set_default.side_effect = PropertyError
        mock.patch(
            self.root + "PropertiesManager.general_map",
            self.gen_map,
        ).start()

        yield

        mock.patch.stopall()

    def test_ok(self, capsys):
        set_default_properties()

        self.mock.a.set_default.assert_called_once_with()
        self.mock.b.set_default.assert_called_once_with()
        self.mock.c.set_default.assert_called_once_with()
        self.mock.d.set_default.assert_called_once_with()

        expected = f"{Fore.CYAN}Fixed property a\n"
        expected += f"{Fore.LIGHTGREEN_EX}b OK\n"
        expected += f"{Fore.CYAN}Fixed property c\n"
        expected += f"{Fore.LIGHTGREEN_EX}d OK\n"

        result = capsys.readouterr()
        assert result.out == expected
        assert result.err == ""
