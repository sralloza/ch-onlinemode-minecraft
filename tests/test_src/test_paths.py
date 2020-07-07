from pathlib import Path
from unittest import mock

import pytest

from server_manager.src.paths import get_server_path


class TestGetServerPath:
    @pytest.fixture(autouse=True)
    def mocks(self):
        root = "server_manager.src.paths."
        root2 = root.replace("paths", "properties_manager")
        self.input_m = mock.patch(root + "input").start()
        self.data_path_m = mock.patch(root + "DATA_PATH").start()
        self.vsp_m = mock.patch(root2 + "validate_server_path").start()
        get_server_path.cache_clear()
        yield

        mock.patch.stopall()

    def test_file_exists(self):
        self.data_path_m.is_file.return_value = True
        self.data_path_m.read_text.return_value = " \n\n  <root-path>\n \n "

        result = get_server_path()
        assert result == Path("<root-path>")

        # Test LRU cache
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

        # Test LRU cache
        result = get_server_path()
        assert result == Path("<root-path>")

        self.data_path_m.is_file.assert_called_once_with()
        self.data_path_m.read_text.assert_not_called()
        self.input_m.assert_called_once_with("Write the path of the server: ")
        self.vsp_m.assert_called_once_with("<root-path>")
        self.data_path_m.write_text.assert_called_with("<root-path>")
