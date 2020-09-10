from unittest import mock

import pytest

from server_manager.src.exceptions import CheckError
from server_manager.src.set_mode import set_mode


class TestSetMode:
    @pytest.fixture(autouse=True)
    def mocks(self):
        root = "server_manager.src.set_mode."
        self.gsp_m = mock.patch(root + "get_server_path").start()
        self.gp_m = mock.patch(root + "PropertiesManager.get_property").start()
        self.player_gen_m = mock.patch(root + "Player.generate").start()
        self.check_players_m = mock.patch(root + "check_players").start()
        self.check_plugin_m = mock.patch(root + "check_plugin").start()
        self.cpm_m = mock.patch(root + "change_players_mode").start()
        self.spm_m = mock.patch(root + "set_plugin_mode").start()
        self.sp_m = mock.patch(root + "PropertiesManager.set_property").start()

        yield

        mock.patch.stopall()

    @pytest.mark.parametrize("new_mode", [False, True])
    def test_set_mode_fails_same_mode(self, new_mode, caplog):
        caplog.set_level(10)
        self.gp_m.return_value = new_mode

        msg = "server is already running with online-mode=%s" % new_mode
        with pytest.raises(ValueError, match=msg):
            set_mode(new_mode)

        self.gsp_m.assert_called_once_with()
        self.gp_m.assert_called_once_with("online_mode")
        self.player_gen_m.assert_not_called()
        self.check_players_m.assert_not_called()
        self.check_plugin_m.assert_not_called()
        self.cpm_m.assert_not_called()
        self.spm_m.assert_not_called()
        self.sp_m.assert_not_called()

        assert len(caplog.records) == 2
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[0].msg == "Setting online-mode=%s (current=%s, path=%s)"
        assert caplog.records[1].levelname == "CRITICAL"
        assert caplog.records[1].msg == "server is already running with online-mode=%s"

    @pytest.mark.parametrize("new_mode", [False, True])
    def test_set_mode_fails_players_check(self, new_mode, caplog):
        caplog.set_level(10)
        self.sp_m.return_value = not new_mode
        self.check_players_m.side_effect = CheckError("players check failed")

        with pytest.raises(CheckError, match="players check failed"):
            set_mode(new_mode)

        self.gsp_m.assert_called_once_with()
        self.gp_m.assert_called_once_with("online_mode")
        self.player_gen_m.assert_called_once_with(self.gsp_m.return_value)
        self.check_players_m.assert_called_once_with(self.player_gen_m.return_value)
        self.check_plugin_m.assert_not_called()
        self.cpm_m.assert_not_called()
        self.spm_m.assert_not_called()
        self.sp_m.assert_not_called()

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[0].msg == "Setting online-mode=%s (current=%s, path=%s)"

    @pytest.mark.parametrize("new_mode", [False, True])
    def test_set_mode_fails_plugin_check(self, new_mode, caplog):
        caplog.set_level(10)
        self.sp_m.return_value = not new_mode
        self.check_plugin_m.side_effect = CheckError("plugin check failed")

        with pytest.raises(CheckError, match="plugin check failed"):
            set_mode(new_mode)

        self.gsp_m.assert_called_once_with()
        self.gp_m.assert_called_once_with("online_mode")
        self.player_gen_m.assert_called_once_with(self.gsp_m.return_value)
        self.check_players_m.assert_called_once_with(self.player_gen_m.return_value)
        self.check_plugin_m.assert_called_once_with()
        self.cpm_m.assert_not_called()
        self.spm_m.assert_not_called()
        self.sp_m.assert_not_called()

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[0].msg == "Setting online-mode=%s (current=%s, path=%s)"

    @pytest.mark.parametrize("new_mode", [False, True])
    def test_set_mode_ok(self, new_mode, caplog):
        caplog.set_level(10)
        self.sp_m.return_value = not new_mode

        set_mode(new_mode)

        self.gsp_m.assert_called_once_with()
        self.gp_m.assert_called_once_with("online_mode")
        self.player_gen_m.assert_called_once_with(self.gsp_m.return_value)
        self.check_players_m.assert_called_once_with(self.player_gen_m.return_value)
        self.check_plugin_m.assert_called_once_with()
        self.cpm_m.assert_called_once_with(self.player_gen_m.return_value, new_mode)
        self.spm_m.assert_called_once_with(not new_mode)
        self.sp_m.assert_called_once_with(online_mode=new_mode)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[0].msg == "Setting online-mode=%s (current=%s, path=%s)"
