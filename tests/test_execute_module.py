import pytest

# pylint: disable=no-name-in-module,unused-import


def test_execute_module():
    with pytest.raises(ImportError):
        from server_manager import __main__
