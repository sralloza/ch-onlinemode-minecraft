from subprocess import CalledProcessError
from unittest import mock

import pytest
from server_manager.src.backup import (
    create_backup,
    get_backup_zipfile_path,
    get_backups_folder,
    is_sfk_installed,
    run_sfk,
)
from server_manager.src.exceptions import SFKError, SFKNotFoundError


class TestIsSfkInstalled:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.run_m = mock.patch("server_manager.src.backup.run").start()
        self.devnull_m = mock.patch("server_manager.src.backup.DEVNULL").start()
        self.system_m = mock.patch("server_manager.src.backup.system").start()
        yield
        mock.patch.stopall()

    @pytest.mark.parametrize("fail", [False, True])
    @pytest.mark.parametrize("system", ["Linux", "Windows"])
    def test_is_sfk_installed(self, system, fail):
        self.system_m.return_value = system
        if fail:
            self.run_m.side_effect = CalledProcessError(-1, "command")

        result = is_sfk_installed()
        assert result == (not fail)

        self.run_m.assert_called_once()
        assert self.run_m.call_args[1] == {
            "stdin": self.devnull_m,
            "stdout": self.devnull_m,
            "stderr": self.devnull_m,
            "check": True,
        }
        assert self.run_m.call_args[0][0][1] == "sfk"

        if system == "Windows":
            assert self.run_m.call_args[0][0][0] == "where"
        else:
            assert self.run_m.call_args[0][0][0] == "which"


@mock.patch("server_manager.src.backup.makedirs")
@mock.patch("server_manager.src.backup.get_server_path")
def test_get_backups_folder(gsp_m, mkdirs_m):
    result = get_backups_folder()
    gsp_m.assert_called_once_with()

    assert result == gsp_m.return_value.with_name.return_value
    gsp_m.return_value.with_name.assert_called_once_with("backups")
    mkdirs_m.assert_called_once_with(result, exist_ok=True)


@mock.patch("server_manager.src.backup.datetime")
@mock.patch("server_manager.src.backup.get_backups_folder")
def test_get_backup_zipfile_path(gbf_m, dt_m):
    current_str_time = "<str-time>"
    dt_m.now.return_value.strftime.return_value = current_str_time

    backup_zipfile_path = get_backup_zipfile_path()
    assert backup_zipfile_path == gbf_m.return_value.joinpath.return_value

    dt_m.now.assert_called_once_with()
    dt_m.now.return_value.strftime.assert_called_once_with("%Y.%m.%d.%H.%M")
    gbf_m.assert_called_once_with()
    gbf_m.return_value.joinpath.assert_called_once_with("LIA-backup-<str-time>.zip")


class TestRunSfk:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.gsp_m = mock.patch("server_manager.src.backup.get_server_path").start()
        self.gbzp_m = mock.patch(
            "server_manager.src.backup.get_backup_zipfile_path"
        ).start()
        self.run_m = mock.patch("server_manager.src.backup.run").start()
        self.devnull_m = mock.patch("server_manager.src.backup.DEVNULL").start()
        self.pipe_m = mock.patch("server_manager.src.backup.PIPE").start()
        yield
        mock.patch.stopall()

    @pytest.mark.parametrize("fail", [False, True])
    def test_run_sfk(self, fail, caplog):
        caplog.set_level(10)
        self.gsp_m.return_value.as_posix.return_value = "/path/to/server"
        self.gbzp_m.return_value.as_posix.return_value = "/path/to/zip"

        if fail:
            self.run_m.side_effect = CalledProcessError(
                -1, "command", output="<stdout>", stderr="<stderr>"
            )

        if fail:
            with pytest.raises(SFKError, match="Error running SFK"):
                run_sfk()
        else:
            run_sfk()

        self.gsp_m.assert_called_once_with()
        self.gsp_m.return_value.as_posix.assert_called()
        assert self.gsp_m.return_value.as_posix.call_count == 2
        self.gbzp_m.assert_called_once_with()
        self.gbzp_m.return_value.as_posix.assert_called()
        assert self.gbzp_m.return_value.as_posix.call_count == 2

        args = ["sfk", "zip", "/path/to/zip", "/path/to/server", "-yes"]
        kwargs = {
            "stdin": self.devnull_m,
            "stdout": self.pipe_m,
            "stderr": self.pipe_m,
            "check": True,
        }

        self.run_m.assert_called_once_with(args, **kwargs)

        if fail:
            assert len(caplog.records) == 2

            assert (
                caplog.records[1].msg == "Error running SFK [%d] (stdout=%s, stderr=%s)"
            )
            assert caplog.records[1].args == (-1, "<stdout>", "<stderr>")
            assert caplog.records[1].levelname == "CRITICAL"
        else:
            assert len(caplog.records) == 1

        assert caplog.records[0].msg == "Creating backup of %r to %r"
        assert caplog.records[0].args == ("/path/to/server", "/path/to/zip")
        assert caplog.records[0].levelname == "DEBUG"


class TestCreateBackup:
    @pytest.fixture(autouse=True)
    def mocks(self):
        self.isi_m = mock.patch("server_manager.src.backup.is_sfk_installed").start()
        self.run_sfk_m = mock.patch("server_manager.src.backup.run_sfk").start()
        yield
        mock.patch.stopall()

    def test_ok(self):
        self.isi_m.return_value = True

        create_backup()

        self.isi_m.assert_called_once_with()
        self.run_sfk_m.assert_called_once_with()

    def test_fail(self):
        self.isi_m.return_value = False

        with pytest.raises(SFKNotFoundError, match="SFK is not installed"):
            create_backup()

        self.isi_m.assert_called_once_with()
        self.run_sfk_m.assert_not_called()
