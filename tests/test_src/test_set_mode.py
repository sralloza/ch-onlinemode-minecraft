from unittest import mock

import pytest

from server_manager.src.exceptions import CheckError
from server_manager.src.set_mode import change_players_mode, set_mode


class TestSetMode:
    @pytest.fixture(autouse=True)
    def mocks(self):
        root = "server_manager.src.set_mode."
        self.gsp_m = mock.patch(root + "get_server_path").start()
        self.gsm_m = mock.patch(root + "get_server_mode").start()
        self.player_gen_m = mock.patch(root + "Player.generate").start()
        self.check_pl_m = mock.patch(root + "check_players").start()
        self.cpm_m = mock.patch(root + "change_players_mode").start()
        self.ssm_m = mock.patch(root + "set_server_mode").start()

    @pytest.mark.parametrize("new_mode", [False, True])
    def test_set_mode_fails_same_mode(self, new_mode, caplog):
        caplog.set_level(10)
        self.gsm_m.return_value = new_mode

        msg = "server is already running with online-mode=%s" % new_mode
        with pytest.raises(ValueError, match=msg):
            set_mode(new_mode)

        self.gsp_m.assert_called_once_with()
        self.gsm_m.assert_called_once_with()
        self.player_gen_m.assert_not_called()
        self.check_pl_m.assert_not_called()
        self.cpm_m.assert_not_called()
        self.ssm_m.assert_not_called()

        assert len(caplog.records) == 2
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[0].msg == "Setting online-mode=%s (current=%s, path=%s)"
        assert caplog.records[1].levelname == "CRITICAL"
        assert caplog.records[1].msg == "server is already running with online-mode=%s"

    @pytest.mark.parametrize("new_mode", [False, True])
    def test_set_mode_fails_check(self, new_mode, caplog):
        caplog.set_level(10)
        self.gsm_m.return_value = not new_mode
        self.check_pl_m.side_effect = CheckError("check failed")

        with pytest.raises(CheckError, match="check failed"):
            set_mode(new_mode)

        self.gsp_m.assert_called_once_with()
        self.gsm_m.assert_called_once_with()
        self.player_gen_m.assert_called_once_with(self.gsp_m.return_value)
        self.check_pl_m.assert_called_once_with(self.player_gen_m.return_value)
        self.cpm_m.assert_not_called()
        self.ssm_m.assert_not_called()

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[0].msg == "Setting online-mode=%s (current=%s, path=%s)"

    @pytest.mark.parametrize("new_mode", [False, True])
    def test_set_mode_ok(self, new_mode, caplog):
        caplog.set_level(10)
        self.gsm_m.return_value = not new_mode

        set_mode(new_mode)

        self.gsp_m.assert_called_once_with()
        self.gsm_m.assert_called_once_with()
        self.player_gen_m.assert_called_once_with(self.gsp_m.return_value)
        self.check_pl_m.assert_called_once_with(self.player_gen_m.return_value)
        self.cpm_m.assert_called_once_with(self.player_gen_m.return_value, new_mode)
        self.ssm_m.assert_called_once_with(new_mode)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[0].msg == "Setting online-mode=%s (current=%s, path=%s)"


@pytest.mark.parametrize("new_mode", [True, False])
@mock.patch("server_manager.src.set_mode.get_username")
@mock.patch("server_manager.src.set_mode.get_uuid")
def test_change_players_mode(guuid_m, gusername_m, new_mode):
    player = mock.MagicMock()
    players = [player] * 5

    change_players_mode(players, new_mode=new_mode)

    assert gusername_m.call_count == 5
    
    gusername_m.assert_called_with(player.uuid)
    assert guuid_m.call_count == 5
    guuid_m.assert_called_with(gusername_m.return_value, new_mode)
